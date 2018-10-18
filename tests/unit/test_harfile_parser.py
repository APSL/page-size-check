
from page_size_check.parser import HarFileParser


class TestHarFileParser:

    def test_harfileparser(self, page_url, fix_har_file, sitemap_url, fix_entries_resume, fix_total_page_size):
        har_file_parser = HarFileParser(page_url, fix_har_file, sitemap_url)
        entries_resume, total_page_size = har_file_parser.parse_log_entries()
        assert entries_resume == fix_entries_resume
        assert total_page_size == fix_total_page_size
