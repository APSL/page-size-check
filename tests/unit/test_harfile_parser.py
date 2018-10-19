
from page_size_check.parser import HarFileParser


class TestHarFileParser:

    def test_harfileparser_entries(self, page_url, fix_har_file, sitemap_url, fix_entries_resume):
        har_file_parser = HarFileParser(page_url, fix_har_file, sitemap_url)
        entries_resume, total_page_size = har_file_parser.parse_log_entries()
        assert entries_resume == fix_entries_resume

    def test_harfileparser_numentries(self, page_url, fix_har_file, sitemap_url, fix_numentries):
        har_file_parser = HarFileParser(page_url, fix_har_file, sitemap_url)
        _, _ = har_file_parser.parse_log_entries()
        assert har_file_parser.num_entries == fix_numentries

    def test_harfileparser_loadtime(self, page_url, fix_har_file, sitemap_url, fix_load_time):
        har_file_parser = HarFileParser(page_url, fix_har_file, sitemap_url)
        assert har_file_parser.load_time == fix_load_time

    def test_harfileparser_total_page_size(self, page_url, fix_har_file, sitemap_url, fix_total_page_size):
        har_file_parser = HarFileParser(page_url, fix_har_file, sitemap_url)
        entries_resume, total_page_size = har_file_parser.parse_log_entries()
        assert total_page_size == fix_total_page_size
