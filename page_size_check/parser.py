import csv
from datetime import datetime, timedelta
from haralyzer import HarPage
from urllib.parse import urlparse
from prettytable import from_csv, PrettyTable


class HarFileData:
    """
    Data Structure of the information extracted from the HarFile
    """
    page_url = ""
    log_entries = []
    har_page = None
    lower_datetime = None
    higher_datetime = None
    sitemap_domain = ""
    entries_resume = {}
    total_page_size = 0
    dom_content_loaded = 0

    @property
    def num_entries(self):
        """
        Provides the number of entries on the HarFile
        """
        return len(self.log_entries)

    @property
    def finish_time(self):
        """
        Time between the first and the last entry of the page
        """
        return (self.higher_datetime-self.lower_datetime).total_seconds() * 1000

    @property
    def load_time(self):
        """
        T​ime that takes to download and display the entire content of a web page in the browser window
        """
        return self.har_page.get_load_time()


class HarFileParser:
    """
    Parser of the HarFile
    """

    def _pre_parse(self, har_file_data, har_file, page_url, sitemap_url):
        """
        Prepare the data to be parsed

        :param HarFileData har_file_data:
        :param dict har_file:
        :param str page_url:
        :param str sitemap_url:
        :return:
        """
        har_file_data.page_url = page_url
        if har_file['log']['entries']:
            har_file_data.log_entries = har_file['log']['entries']
        page_id = har_file['log']['pages'][0].get('id')
        if page_id:
            har_file_data.har_page = HarPage(page_id, har_data=har_file)
        har_file_data.lower_datetime = datetime.now() + timedelta(hours=1)
        har_file_data.higher_datetime = datetime.now() - timedelta(hours=1)
        har_file_data.sitemap_domain = urlparse(sitemap_url).netloc

    def parse(self, har_file, page_url, sitemap_url, driver=None):
        """
        Parse HarFile to a HarFileData structure

        :param dict har_file:
        :param str page_url:
        :param str sitemap_url:
        :param webdriver.Firefox driver:
        :return HarFileData:
        """
        har_file_data = HarFileData()
        self._pre_parse(har_file_data, har_file, page_url, sitemap_url)
        entries_resume = {}
        total_page_size = 0

        for entry in har_file_data.log_entries:
            mime_type = entry['response']['content']['mimeType'].split(";")[0]

            if mime_type not in entries_resume:
                entries_resume[mime_type] = {}
                entries_resume[mime_type]['entries'] = []
                entries_resume[mime_type]['total_size'] = 0
                entries_resume[mime_type]['total_time'] = 0
            started_date_time = datetime.strptime(entry['startedDateTime'].rsplit("+", 1)[0], "%Y-%m-%dT%H:%M:%S.%f")

            if started_date_time < har_file_data.lower_datetime:
                har_file_data.lower_datetime = started_date_time
            if started_date_time > har_file_data.higher_datetime:
                har_file_data.higher_datetime = started_date_time

            entry_info = {
                'url': entry['request']['url'],
                'time': entry['time'],  # time in ms
                'status': entry['response']['status'],
                'body_size': entry['response']['bodySize'] / 1024,  # size in KB
                'headers_size': entry['response']['headersSize'] / 1024,  # size in KB
            }
            entry_info['total_size'] = entry_info['body_size'] + entry_info['headers_size']

            # entries aggregation
            entries_resume[mime_type]['entries'].append(entry_info)
            entries_resume[mime_type]['total_size'] += entry_info['total_size']  # size in MB
            entries_resume[mime_type]['total_time'] += entry_info['time']  # time in ms
            # More detailed times can be included:
            # blocked', 'ssl', 'connect', 'receive', 'send', 'comment', 'wait', 'dns'
            total_page_size += entry_info['total_size']
        har_file_data.entries_resume = entries_resume
        har_file_data.total_page_size = total_page_size / 1024  # size in MB
        if driver:
            har_file_data.dom_content_loaded = self._get_dom_content_loaded_time(driver)
        return har_file_data

    def _get_dom_content_loaded_time(self, driver):
        """
        Method to get the dom content loaded time using JS at the browser
        :param driver: Browser which the webpage that is beig analized
        :return:
        """
        script = 'return window.performance.timing.domContentLoadedEventStart' \
                 ' - window.performance.timing.navigationStart;'
        return driver.execute_script(script)

    @staticmethod
    def mimetype_resources_to_csv(results):
        """
        Generate a CSV with a resume of the resources by mimetype used by the webpage

        :param list results: list of HarFileData
        """
        file_path = '{}-mimetype-resources.csv'.format(results[0].sitemap_domain)
        with open(file_path, 'a+', newline='') as csv_file:
            field_names = ['page_url', 'mime_type', 'n_entries', 'total_size', 'average_size', 'percentage_size',
                           'total_time', 'average_time']
            writer = csv.DictWriter(csv_file, fieldnames=field_names)
            writer.writeheader()

            for result in results:
                for mime_type, entries in result.entries_resume.items():
                    total_page_size = round(result.entries_resume['text/html']['total_size'], 3)

                    average_size = round(entries['total_size']/len(entries['entries']), 3)
                    average_time = round(entries['total_time']/len(entries['entries']), 3)
                    percentage_size = round((entries['total_size']/total_page_size) * 100, 3)
                    writer.writerow({
                        'page_url': result.page_url,
                        'mime_type': mime_type,
                        'n_entries': len(entries['entries']),
                        'total_size': round(entries['total_size'], 3),
                        'average_size': average_size,
                        'percentage_size': percentage_size,
                        'total_time': entries['total_time'],
                        'average_time': average_time
                    })

    @staticmethod
    def resources_to_csv(results):
        """
        Generate a CSV with a list of the resources used by the webpage

        :param list results: list of HarFileData
        """
        file_path = '{}-resources-list.csv'.format(results[0].sitemap_domain)
        with open(file_path, 'a+', newline='') as csv_file:
            field_names = ['page_url', 'resource_url', 'mime_type', 'size', 'time']
            writer = csv.DictWriter(csv_file, fieldnames=field_names)
            writer.writeheader()

            for result in results:
                for mime_type, entries in result.entries_resume.items():
                    for entry in entries['entries']:
                        writer.writerow({
                            'page_url': result.page_url,
                            'mime_type': mime_type,
                            'resource_url': entry['url'],
                            'size': round(entry['total_size'], 3),
                            'time': round(entry['time'], 3)}
                        )

    def get_summary(self, results, display_summary):
        """
        Get the summarized results: generate a CSV with this data and print the results to the
        stdout if display_summary param is set to True.

        :param list results: list of HarFileData
        :param bool display_summary: If true displays the results summary to the stdout
        """
        file_path = '{}-resume-urls.csv'.format(results[0].sitemap_domain)
        with open(file_path, 'w') as csv_file:
            # Prepare CSV file
            field_names = ['page_url', 'num_entries', 'page_size (KB)', 'page_load_time (ms)',
                           'total_size (MB)', 'total_load_time (ms)', 'finish_time (ms)', 'dom_load_time (ms)']
            writer = csv.DictWriter(csv_file, fieldnames=field_names)
            writer.writeheader()

            # Totals
            page_size_sum = 0
            page_load_time_avg = 0
            total_size_sum = 0
            total_load_time_avg = 0
            for result in results:
                page_size = round(result.entries_resume['text/html']['total_size'], 3)
                writer.writerow({
                    'page_url': result.page_url,
                    'num_entries': result.num_entries,
                    'page_size (KB)': page_size,
                    'page_load_time (ms)': result.entries_resume['text/html']['total_time'],
                    'total_size (MB)': round(result.total_page_size, 3),
                    'total_load_time (ms)': result.load_time,
                    'finish_time (ms)': result.finish_time,
                    'dom_load_time (ms)': result.dom_content_loaded,
                })
                page_size_sum += page_size
                page_load_time_avg += result.entries_resume['text/html']['total_time']
                total_size_sum += round(result.total_page_size, 3)
                total_load_time_avg += result.load_time
            page_size_sum = round(page_size_sum, 3)
            page_load_time_avg = round(page_load_time_avg / len(results), 3)
            total_load_time_avg = round(total_load_time_avg / len(results), 3)
        if display_summary:
            # Print the CSV in table format (prettytables don't allow the use of sys.stdout.write)
            with open(file_path, 'r') as csv_file:
                summary_table = from_csv(csv_file)
                print(summary_table)

            # Print the totals in table format
            totals_table = PrettyTable()
            totals_table.field_names = ["page_size_sum (KB)", "page_load_time_avg (ms)", "total_size_sum (MB)",
                                        "total_load_time_avg (ms)"]
            totals_table.add_row([page_size_sum, page_load_time_avg, total_size_sum, total_load_time_avg])
            print(totals_table)
