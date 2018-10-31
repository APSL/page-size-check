import csv
import logging
import click
import requests
import threading
from concurrent.futures import ThreadPoolExecutor
from browsermobproxy import Server
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from urllib.parse import urlparse
from xvfbwrapper import Xvfb

from page_size_check.parser import HarFileParser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)


def start_server_display(browsermob_server_path, browsermob_server_port):
    logger.info("Running BrowserMob server...")
    display = Xvfb()
    display.start()

    server = Server(path=browsermob_server_path, options={'port': browsermob_server_port})
    server.start()
    return display, server


def start_proxy_driver(server, firefox_driver_path):
    proxy = server.create_proxy()

    profile = webdriver.FirefoxProfile()
    selenium_proxy = proxy.selenium_proxy()
    profile.set_proxy(selenium_proxy)
    driver = webdriver.Firefox(firefox_profile=profile, executable_path=firefox_driver_path)

    return proxy, driver


def get_sitemap_urls(sitemap_url, server, firefox_driver_path):
    logger.info("Getting sitemap entries for \"{}\"".format(sitemap_url))
    if not sitemap_url:
        return []
    # Get the sitemap and parse it to get the urls
    urls = []
    sitemap_xml = requests.get(sitemap_url).text
    soup = BeautifulSoup(sitemap_xml)
    for loc in soup.findAll("loc"):
        urls.append({
            'page_url': loc.text,
            'server': server,
            'firefox_driver_path': firefox_driver_path,
            'sitemap_url': sitemap_url,
        })
    logger.debug("Urls parsed: {}".format(len(urls)))
    return urls


def execute_parser(url_info):
    page_url, server = url_info['page_url'], url_info['server']
    firefox_driver_path, sitemap_url = url_info['firefox_driver_path'], url_info['sitemap_url']

    try:
        proxy, driver = start_proxy_driver(server, firefox_driver_path)
        proxy.new_har()
    except Exception as ex:
        logger.exception(ex)
    try:
        logger.info("Processing \"{}\"".format(page_url))
        driver.get(page_url)
    except TimeoutException:
        driver.quit()
        logger.error("Error processing \"{}\" url".format(page_url))

    try:
        har_file_parser = HarFileParser(page_url, proxy.har, sitemap_url)
        entries_resume, total_page_size = har_file_parser.parse_log_entries()
        dom_content_loaded = har_file_parser.get_dom_content_loaded_time(driver)
    except Exception as ex:
        logger.exception(ex)
    driver.quit()
    # with threading.Lock():
    #     har_file_parser.resources_to_csv(entries_resume)
    # with threading.Lock():
    #     har_file_parser.mimetype_resources_to_csv(entries_resume, total_page_size)
    logger.info("Printing results...")
    with threading.Lock():
        har_file_parser.resume_to_csv(total_page_size, dom_content_loaded)


def resume_to_csv(self, total_page_size, dom_content_loaded):
    file_path = '{}-resume-urls.csv'.format(self.sitemap_domain)
    # file_exists = self.check_file_existence(file_path)
    with open(file_path, 'a+', newline='') as csv_file:
        field_names = ['page_url', 'num_entries', 'total_size', 'finish_time', 'domcontent_loaded', 'load_time']
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()
        writer.writerow({
            'page_url': self.url,
            'num_entries': self.num_entries,
            'total_size': round(total_page_size, 3),
            'finish_time': self.finish_time,
            'domcontent_loaded': dom_content_loaded,
            'load_time': self.load_time,
        })


@click.command()
@click.option('--browsermob_server_path', default='./browsermob-proxy-2.1.4/bin/browsermob-proxy',
              help='BrowserMob server path.', envvar='BROWSERMOB_SERVER_PATH')
@click.option('--browsermob_server_port', default=8090, help='BrowserMob server port.')
@click.option('--firefox_driver_path', default='./geckodriver', help='Firefox driver path.',
              envvar='FIREFOX_DRIVER_PATH')
@click.option('--sitemap_url', help='Sitemap to get urls.')
@click.option('--threads', default=4, help='Number of threads.')
def run(sitemap_url, browsermob_server_path, browsermob_server_port, firefox_driver_path, threads):
    display, server = start_server_display(browsermob_server_path, browsermob_server_port)
    sitemap_urls = get_sitemap_urls(sitemap_url, server, firefox_driver_path)
    try:
        with ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(execute_parser, sitemap_urls)
    except KeyboardInterrupt:
        logger.info("Stopping BrowserMob server...")
        server.stop()
        display.stop()


if __name__ == '__main__':
    run()
