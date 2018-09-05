from browsermobproxy import Server
from selenium import webdriver
from xvfbwrapper import Xvfb

import click
import sys

from parser import HarFileParser


@click.command()
@click.option('--verbose', default=False, help='Verbose mode.')
def run(verbose):
    display, server, proxy, driver = start_server_proxy_driver()

    try:
        proxy.new_har()
        driver.get("https://www.houmhotels.com/es/hoteles/houm-nets/galeria/")

        har_file_parser = HarFileParser(proxy)
        entries_resume, total_page_size = har_file_parser.parse_log_entries()

        finish_time, dom_content_loaded, load_time = get_pages_load_times(driver, har_file_parser)
        show_results(entries_resume, verbose, har_file_parser.num_entries, total_page_size, finish_time,
                     dom_content_loaded, load_time)
    except Exception as ex:
        raise ex
    finally:
        driver.quit()
        server.stop()
        display.stop()


def start_server_proxy_driver():
    display = Xvfb()
    display.start()

    server = Server(path="./browsermob-proxy-2.1.4/bin/browsermob-proxy",
                    options={'port': 8090})
    server.start()
    proxy = server.create_proxy()

    profile = webdriver.FirefoxProfile()
    selenium_proxy = proxy.selenium_proxy()
    profile.set_proxy(selenium_proxy)
    driver = webdriver.Firefox(firefox_profile=profile, executable_path="./geckodriver")

    return display, server, proxy, driver


def get_pages_load_times(driver, har_file_parser):
    finish_time = har_file_parser.finish_time
    dom_content_loaded = driver.execute_script(
            'return window.performance.timing.domContentLoadedEventStart - window.performance.timing.navigationStart;')

    load_time = har_file_parser.har_page.get_load_time()
    return finish_time, dom_content_loaded, load_time


def show_results(entries_resume, verbose, num_entries, total_page_size, finish_time, dom_content_loaded, load_time):
    for mime_type, entries in entries_resume.items():
        average_size = round(entries['total_size']/len(entries['entries']), 3)
        average_time = round(entries['total_time']/len(entries['entries']), 3)

        if not verbose:
            sys.stdout.write("Mimetype: {} - Nº of entries: {} - Total size: {}MB - Average size: {}MB - "
                             "Total time: {}ms - Average time: {}ms\n".format(mime_type, len(entries['entries']),
                                                                              round(entries['total_size'], 3),
                                                                              average_size, entries['total_time'],
                                                                              average_time))
        else:
            for entry in entries['entries']:
                sys.stdout.write("Mimetype: {} - Url: {} - Size: {}MB - Time: {}ms\n".format(
                    mime_type, entry['url'], entry['total_size'], entry['time']))

    sys.stdout.write("Total size of page: {}MB - Number of entries: {}  - FinishTime: {}ms - DOMContentLoaded: {}ms"
                     " - Load Time: {}ms\n".format(round(total_page_size, 3), num_entries, finish_time,
                                                   dom_content_loaded, load_time))


if __name__ == '__main__':
    run()
