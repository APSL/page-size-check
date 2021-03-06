import logging
import click
import requests
from itertools import repeat
from concurrent.futures import ThreadPoolExecutor
from browsermobproxy import Server
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from xvfbwrapper import Xvfb

from page_size_check.parser import HarFileParser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)


def start_server_display(browsermob_server_path, browsermob_server_port):
    """
    Method to start the virtual screen where the browsers are going to be displayed and to start the Browsermob Server
    :param browsermob_server_path: Path of the browsermob server
    :param browsermob_server_port: Port where the browsermob server will be launched
    :return:
    """
    logger.info("Running BrowserMob server...")
    display = Xvfb()
    display.start()

    server = Server(path=browsermob_server_path, options={'port': browsermob_server_port})
    server.start()
    return display, server


def start_proxy_driver(server, firefox_driver_path):
    """
    Method to start the proxy where we are going to read the HarFile and the driver to open the urls
    :param server: Browsermob server
    :param firefox_driver_path: Path of the geckodriver of firefox
    :return:
    """
    proxy = server.create_proxy()

    profile = webdriver.FirefoxProfile()
    selenium_proxy = proxy.selenium_proxy()
    profile.set_proxy(selenium_proxy)
    driver = webdriver.Firefox(firefox_profile=profile, executable_path=firefox_driver_path)

    return proxy, driver


def get_sitemap_urls(sitemap_url, server, firefox_driver_path):
    """
    Method that gets the urls to be parsed
    :param sitemap_url: The url of the sitemap of the web that is going to be analized
    :param server: Browsermob server
    :param firefox_driver_path: Path of the geckodriver of firefox
    :return:
    """
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
    logger.info("Urls parsed: {}".format(len(urls)))
    return urls


def execute_parser(results, url_info):
    """
    Method to load the page on the browser, get the HarFile and parse its data
    :param results: Array where the parsed data is stored
    :param url_info: Information of the url to be analyzed
    :return:
    """
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
    except TimeoutException:  # TODO: change with retry policy
        driver.quit()
        logger.error("Error processing \"{}\" url".format(page_url))

    try:
        har_file_parser = HarFileParser()
        har_file_data = har_file_parser.parse(proxy.har, page_url, sitemap_url, driver)
        results.append(har_file_data)
        logger.info("\"{}\" parsed!".format(page_url))
    except Exception as ex:
        logger.exception(ex)
    driver.quit()


@click.command()
@click.option('--browsermob_server_path', default='./browsermob-proxy-2.1.4/bin/browsermob-proxy',
              help='BrowserMob server path.', envvar='BROWSERMOB_SERVER_PATH')
@click.option('--browsermob_server_port', default=8090, help='BrowserMob server port.')
@click.option('--firefox_driver_path', default='./geckodriver', help='Firefox driver path.',
              envvar='FIREFOX_DRIVER_PATH')
@click.option('--sitemap_url', help='Sitemap to get urls.')
@click.option('--threads', default=8, help='Number of threads.')
@click.option('--display_summary', default=True, help='If true displays the results summary to the stdout.')
@click.option('--generate_extra_csv', default=True, help='If true generates extra information in CSVs')
def run(sitemap_url, browsermob_server_path, browsermob_server_port, firefox_driver_path, threads,
        display_summary, generate_extra_csv):
    display, server = start_server_display(browsermob_server_path, browsermob_server_port)
    sitemap_urls = get_sitemap_urls(sitemap_url, server, firefox_driver_path)
    results = []
    try:
        with ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(execute_parser, repeat(results), sitemap_urls)
        logger.info("URLs processed: {}".format(len(results)))
        if results:
            har_file_parser = HarFileParser()
            har_file_parser.get_summary(results, display_summary)
            if generate_extra_csv:
                har_file_parser.resources_to_csv(results)
                har_file_parser.mimetype_resources_to_csv(results)
    except KeyboardInterrupt:
        logger.info("Stopping BrowserMob server...")
        server.stop()
        display.stop()


if __name__ == '__main__':
    run()
