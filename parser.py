from datetime import datetime, timedelta

from haralyzer import HarPage


class HarFileParser:
    log_entries = []
    har_page = None
    lower_datetime = None
    higher_datetime = None

    def __init__(self, proxy):
        if proxy.har['log']['entries']:
            self.log_entries = proxy.har['log']['entries']
        page_id = proxy.har['log']['pages'][0].get('id')
        if page_id:
            self.har_page = HarPage(page_id, har_data=proxy.har)
        self.lower_datetime = datetime.now() + timedelta(hours=1)
        self.higher_datetime = datetime.now() - timedelta(hours=1)

    @property
    def num_entries(self):
        return len(self.log_entries)

    @property
    def finish_time(self):
        return (self.higher_datetime-self.lower_datetime).total_seconds() * 1000

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
