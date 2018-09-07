from datetime import datetime, timedelta
from haralyzer import HarPage

import sys


class HarFileParser:
    url = ""
    log_entries = []
    har_page = None
    lower_datetime = None
    higher_datetime = None
    verbose = False

    def __init__(self, url, proxy, verbose):
        self.url = url
        if proxy.har['log']['entries']:
            self.log_entries = proxy.har['log']['entries']
        page_id = proxy.har['log']['pages'][0].get('id')
        if page_id:
            self.har_page = HarPage(page_id, har_data=proxy.har)
        if verbose:
            self.verbose = True
        self.lower_datetime = datetime.now() + timedelta(hours=1)
        self.higher_datetime = datetime.now() - timedelta(hours=1)

    @property
    def num_entries(self):
        return len(self.log_entries)

    @property
    def finish_time(self):
        return (self.higher_datetime-self.lower_datetime).total_seconds() * 1000

    @property
    def load_time(self):
        return self.har_page.get_load_time()

    def parse_log_entries(self):
        entries_resume = {}
        total_page_size = 0

        for entry in self.log_entries:

            mime_type = entry['response']['content']['mimeType']

            if mime_type not in entries_resume:
                entries_resume[mime_type] = {}
                entries_resume[mime_type]['entries'] = []
                entries_resume[mime_type]['total_size'] = 0
                entries_resume[mime_type]['total_time'] = 0

            started_date_time = datetime.strptime(entry['startedDateTime'].rsplit("+", 1)[0], "%Y-%m-%dT%H:%M:%S.%f")

            if started_date_time < self.lower_datetime:
                self.lower_datetime = started_date_time
            if started_date_time > self.higher_datetime:
                self.higher_datetime = started_date_time

            entry_info = {
                'url': entry['request']['url'],
                'time': entry['time'],  # time in ms
                'status': entry['response']['status'],
                'body_size': entry['response']['bodySize'] / (1024 * 1024),  # size in MB
                'headers_size': entry['response']['headersSize'] / (1024 * 1024),  # size in MB
            }
            entry_info['total_size'] = entry_info['body_size'] + entry_info['headers_size']

            # entries aggregation
            entries_resume[mime_type]['entries'].append(entry_info)
            entries_resume[mime_type]['total_size'] += entry_info['total_size']  # size in MB
            entries_resume[mime_type]['total_time'] += entry_info['time']  # time in ms
            # se puede incluir desglose de tiempos:
            # blocked', 'ssl', 'connect', 'receive', 'send', 'comment', 'wait', 'dns'
            total_page_size += entry_info['total_size']  # size in MB

        return entries_resume, total_page_size

    @staticmethod
    def get_dom_content_loaded_time(driver):
        script = 'return window.performance.timing.domContentLoadedEventStart' \
                 ' - window.performance.timing.navigationStart;'
        return driver.execute_script(script)

    def show_results(self, entries_resume, total_page_size, dom_content_loaded):
        offset = "\n\n\n"
        sys.stdout.write("\033[1;31m {}Url: {}\n".format(offset, self.url))
        sys.stdout.write("Total size of page: {}MB - Number of entries: {}  - FinishTime: {}ms - "
                         "DOMContentLoaded: {}ms - Load Time: {}ms\n".format(
                          round(total_page_size, 3), self.num_entries, self.finish_time, dom_content_loaded,
                          self.load_time))
        sys.stdout.write("\033[0;0m")

        for mime_type, entries in entries_resume.items():
            average_size = round(entries['total_size']/len(entries['entries']), 3)
            average_time = round(entries['total_time']/len(entries['entries']), 3)

            if not self.verbose:
                percentage_size = round((entries['total_size']/total_page_size) * 100, 3)
                sys.stdout.write("Mimetype: {} - Nº of entries: {} - Total size: {}MB - Average size: {}MB - "
                                 "Percentage on page size: {}% - Total time: {}ms - Average time: {}ms\n".format(
                                  mime_type, len(entries['entries']), round(entries['total_size'], 3), average_size,
                                  percentage_size, entries['total_time'], average_time))
            else:
                for entry in entries['entries']:
                    sys.stdout.write("Mimetype: {} - Url: {} - Size: {}MB - Time: {}ms\n".format(
                        mime_type, entry['url'], entry['total_size'], entry['time']))
