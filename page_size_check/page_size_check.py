from concurrent.futures import ThreadPoolExecutor

from browsermobproxy import Server
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from xvfbwrapper import Xvfb

import click
import requests
import threading

from page_size_check.parser import HarFileParser


def start_server_display(browsermob_server_path):
    display = Xvfb()
    display.start()

    server = Server(path=browsermob_server_path, options={'port': 8090})
    server.start()
    return display, server


def start_proxy_driver(server, firefox_driver_path):
    proxy = server.create_proxy()

    profile = webdriver.FirefoxProfile()
    selenium_proxy = proxy.selenium_proxy()
    profile.set_proxy(selenium_proxy)
    driver = webdriver.Firefox(firefox_profile=profile, executable_path=firefox_driver_path)

    return proxy, driver


def get_sitemap_urls(sitemap_url, server, firefox_driver_path, verbose, csv_output):
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
            'verbose': verbose,
            'csv_output': csv_output,
        })
    return urls


def execute_parser(url_info):
    page_url, server, firefox_driver_path = url_info['page_url'], url_info['server'], url_info['firefox_driver_path']
    sitemap_url, verbose, csv_output = url_info['sitemap_url'], url_info['verbose'], url_info['csv_output']

    proxy, driver = start_proxy_driver(server, firefox_driver_path)
    proxy.new_har()
    try:
        driver.get(page_url)
    except TimeoutException:
        driver.quit()
        file_error_name = "./{}-errors.txt".format(sitemap_url.replace("/", "-"))
        with threading.Lock():
            with open(file_error_name, 'a+') as file:
                file.write("{}\n".format(page_url))

    har_file_parser = HarFileParser(page_url, proxy, verbose)
    entries_resume, total_page_size = har_file_parser.parse_log_entries()

    dom_content_loaded = har_file_parser.get_dom_content_loaded_time(driver)
    driver.quit()
    if not csv_output:
        har_file_parser.show_results(entries_resume, total_page_size, dom_content_loaded)
    else:
        with threading.Lock():
            if verbose:
                har_file_parser.write_verbose_to_csv(entries_resume, total_page_size, dom_content_loaded,
                                                     sitemap_url)
            else:
                har_file_parser.write_noverbose_to_csv(entries_resume, total_page_size, dom_content_loaded,
                                                       sitemap_url)


@click.command()
@click.option('--verbose/--no-verbose', default=False, help='Verbose mode.')
@click.option('--csv_output/--no-csv_output', default=False, help='Output in csv or terminal.')
@click.option('--browsermob_server_path', default='./browsermob-proxy-2.1.4/bin/browsermob-proxy',
              help='Browsermob Server Path.')
@click.option('--firefox_driver_path', default='./geckodriver', help='Firefox Driver Path.')
@click.option('--sitemap_url', help='Sitemap to get urls.')
@click.option('--threads', default=4, help='Number of threads.')
def run(sitemap_url, verbose, csv_output, browsermob_server_path, firefox_driver_path, threads):

    display, server = start_server_display(browsermob_server_path)
    sitemap_urls = get_sitemap_urls(sitemap_url, server, firefox_driver_path, verbose, csv_output)

    try:
        with ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(execute_parser, sitemap_urls)
    except Exception as ex:
        raise ex
    finally:
        server.stop()
        display.stop()


if __name__ == '__main__':
    run()