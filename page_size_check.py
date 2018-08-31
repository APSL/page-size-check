from browsermobproxy import Server
from selenium import webdriver
import sys

server = Server(path="/home/carlos/projects/page_size_check/browsermob-proxy-2.1.4/bin/browsermob-proxy",
                options={'port': 8090})
server.start()
proxy = server.create_proxy()

profile = webdriver.FirefoxProfile()
selenium_proxy = proxy.selenium_proxy()
profile.set_proxy(selenium_proxy)
driver = webdriver.Firefox(firefox_profile=profile, executable_path="/home/carlos/projects/page_size_check/geckodriver")

verbose = True

try:
    proxy.new_har()
    driver.get("https://www.houmhotels.com/es/")
    # sys.stdout.write(proxy.har)  # returns a HAR JSON blob
    log_entries = proxy.har['log']['entries']

    entries_resume = {}
    total_page_size = 0

    for entry in log_entries:

        mime_type = entry['response']['content']['mimeType']

        if mime_type not in entries_resume:
            entries_resume[mime_type] = {}
            entries_resume[mime_type]['entries'] = []
            entries_resume[mime_type]['total_size'] = 0
            entries_resume[mime_type]['total_time'] = 0

        entry_info = {
            'url': entry['request']['url'],
            'time': entry['time'],  # time in ms
            'status': entry['response']['status'],
            'body_size': entry['response']['bodySize'] / (1024 * 1024),  # size in MB
            'headers_size': entry['response']['headersSize'] / (1024 * 1024),  # size in MB
        }
        entry_info['total_size'] = entry_info['body_size'] + entry_info['headers_size']

        entries_resume[mime_type]['entries'].append(entry_info)
        entries_resume[mime_type]['total_size'] += entry_info['total_size']  # size in MB
        total_page_size += entry_info['total_size']  # size in MB
        entries_resume[mime_type]['total_time'] += entry_info['time']  # time in ms

        # se puede incluir desglose de tiempos: blocked', 'ssl', 'connect', 'receive', 'send', 'comment', 'wait', 'dns'

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
                sys.stdout.write("Mimetype: {} - Url: {} - Size: {}MB - Time: {}ms".format(
                    mime_type, entry['url'], entry['total_size'], entry['time']))
        #     pprint(entry)
    sys.stdout.write("Total size of page: {}MB - Number of entries: {} \n".format(round(total_page_size, 3),
                                                                                  len(log_entries)))
except Exception as ex:
    raise ex
finally:
    driver.quit()
    server.stop()
