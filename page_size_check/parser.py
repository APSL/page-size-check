from datetime import datetime, timedelta
from haralyzer import HarPage
from urllib.parse import urlparse

import csv
import os.path


class HarFileParser:
    url = ""
    log_entries = []
    har_page = None
    lower_datetime = None
    higher_datetime = None
    sitemap_domain = ""

    def __init__(self, url, har_file, sitemap_url):
        self.url = url
        if har_file['log']['entries']:
            self.log_entries = har_file['log']['entries']
        page_id = har_file['log']['pages'][0].get('id')
        if page_id:
            self.har_page = HarPage(page_id, har_data=har_file)
        self.lower_datetime = datetime.now() + timedelta(hours=1)
        self.higher_datetime = datetime.now() - timedelta(hours=1)
        self.sitemap_domain = urlparse(sitemap_url).netloc

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

            mime_type = entry['response']['content']['mimeType'].split(";")[0]

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

    @staticmethod
    def check_file_existence(file_path):
        return os.path.isfile(file_path)

    def mimetype_resources_to_csv(self, entries_resume, total_page_size):
        file_path = '{}-mimetype-resources.csv'.format(self.sitemap_domain)
        file_exists = self.check_file_existence(file_path)
        with open(file_path, 'a+', newline='') as csv_file:
            field_names = ['page_url', 'mime_type', 'n_entries', 'total_size', 'average_size', 'percentage_size',
                           'total_time', 'average_time']
            writer = csv.DictWriter(csv_file, fieldnames=field_names)
            if not file_exists:
                writer.writeheader()

            for mime_type, entries in entries_resume.items():
                average_size = round(entries['total_size']/len(entries['entries']), 3)
                average_time = round(entries['total_time']/len(entries['entries']), 3)
                percentage_size = round((entries['total_size']/total_page_size) * 100, 3)
                writer.writerow({
                    'page_url': self.url,
                    'mime_type': mime_type,
                    'n_entries': len(entries['entries']),
                    'total_size': round(entries['total_size'], 3),
                    'average_size': average_size,
                    'percentage_size': percentage_size,
                    'total_time': entries['total_time'],
                    'average_time': average_time
                })

    def resources_to_csv(self, entries_resume):
        file_path = '{}-resources-list.csv'.format(self.sitemap_domain)
        file_exists = self.check_file_existence(file_path)
        with open(file_path, 'a+', newline='') as csv_file:
            field_names = ['page_url', 'resource_url', 'mime_type', 'size', 'time']
            writer = csv.DictWriter(csv_file, fieldnames=field_names)
            if not file_exists:
                writer.writeheader()

            for mime_type, entries in entries_resume.items():
                for entry in entries['entries']:
                    writer.writerow({
                        'page_url': self.url,
                        'mime_type': mime_type,
                        'resource_url': entry['url'],
                        'size': round(entry['total_size'], 3),
                        'time': round(entry['time'], 3)}
                    )

    def resume_to_csv(self, total_page_size, dom_content_loaded):
        file_path = '{}-resume-urls.csv'.format(self.sitemap_domain)
        file_exists = self.check_file_existence(file_path)
        with open(file_path, 'a+', newline='') as csv_file:
            field_names = ['page_url', 'num_entries', 'total_size', 'finish_time', 'domcontent_loaded', 'load_time']
            writer = csv.DictWriter(csv_file, fieldnames=field_names)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                'page_url': self.url,
                'num_entries': self.num_entries,
                'total_size': round(total_page_size, 3),
                'finish_time': self.finish_time,
                'domcontent_loaded': dom_content_loaded,
                'load_time': self.load_time,
            })
