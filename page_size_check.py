from browsermobproxy import Server
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from xvfbwrapper import Xvfb

import click
import requests

from parser import HarFileParser


def start_server_proxy_driver(browsermob_server_path, firefox_driver_path):
    # Start
    display = Xvfb()
    display.start()

    server = Server(path=browsermob_server_path, options={'port': 8090})
    server.start()
    proxy = server.create_proxy()

    profile = webdriver.FirefoxProfile()
    selenium_proxy = proxy.selenium_proxy()
    profile.set_proxy(selenium_proxy)
    driver = webdriver.Firefox(firefox_profile=profile, executable_path=firefox_driver_path)

    return display, server, proxy, driver


def get_sitemap_urls(sitemap_url):
    if not sitemap_url:

        return []
    # Get the sitemap and parse it to get the urls
    urls = []
    sitemap_xml = requests.get(sitemap_url).text
    soup = BeautifulSoup(sitemap_xml)
    for loc in soup.findAll("loc"):
        urls.append(loc.text)
    return urls


@click.command()
@click.option('--verbose/--no-verbose', default=False, help='Verbose mode.')
@click.option('--browsermob_server_path', default='./browsermob-proxy-2.1.4/bin/browsermob-proxy',
              help='Browsermob Server Path.')
@click.option('--firefox_driver_path', default='./geckodriver', help='Firefox Driver Path.')
@click.option('--sitemap_url', help='Sitemap to get urls.')
def run(sitemap_url, verbose, browsermob_server_path, firefox_driver_path):
    sitemap_urls = get_sitemap_urls(sitemap_url)

    display, server, proxy, driver = start_server_proxy_driver(browsermob_server_path, firefox_driver_path)

    try:
        for url in sitemap_urls:
            proxy.new_har()
            try:
                driver.get(url)
            except TimeoutException:
                file_error_name = "./{}-errors.txt".format(sitemap_url.replace("/", "-"))
                with open(file_error_name, 'a+') as file:
                    file.write("{}\n".format(url))
                continue

            har_file_parser = HarFileParser(url, proxy, verbose)
            entries_resume, total_page_size = har_file_parser.parse_log_entries()

            dom_content_loaded = har_file_parser.get_dom_content_loaded_time(driver)
            har_file_parser.show_results(entries_resume, total_page_size, dom_content_loaded)
    except Exception as ex:
        raise ex
    finally:
        driver.quit()
        server.stop()
        display.stop()


if __name__ == '__main__':
    run()
