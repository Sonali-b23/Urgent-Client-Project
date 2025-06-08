import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from urllib.parse import urljoin, urlparse
import logging

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG)

class WebCrawler:
    def __init__(self):
        self.index = defaultdict(list)
        self.visited = set()

    def crawl(self, url, base_url=None):
        if url in self.visited:
            return
        self.visited.add(url)

        try:
            response = requests.get(url)
            # Check if the content is HTML
            content_type = response.headers.get('Content-Type', '').lower()
            if 'html' not in content_type:
                logging.warning(f"Skipping non-HTML content: {url}")
                return

            soup = BeautifulSoup(response.text, 'html.parser')
            self.index[url] = soup.get_text()

            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    if urlparse(href).netloc:
                        href = urljoin(base_url or url, href)

                    parsed_base = urlparse(base_url or url)
                    parsed_href = urlparse(href)

                    # Crawl only if the link is within the same domain
                    if parsed_href.netloc == parsed_base.netloc:
                        self.crawl(href, base_url=base_url or url)

        except Exception as e:
            logging.error(f"Error crawling {url}: {e}")

    def search(self, keyword):
        results = []
        for url, text in self.index.items():
            if keyword.lower() in text.lower():
                results.append(url)
        return results

    def print_results(self, results):
        if results:
            print("Search results:")
            for result in results:
                print(f"- {result}")
        else:
            print("No results found.")

def main():
    crawler = WebCrawler()
    start_url = "https://example.com"
    crawler.crawl(start_url)  # Fixed typo here

    keyword = "test"
    results = crawler.search(keyword)
    crawler.print_results(results)

import unittest
from unittest.mock import patch, MagicMock

class WebCrawlerTests(unittest.TestCase):
    @patch('requests.get')
    def test_crawl_success(self, mock_get):
        sample_html = """
        <html><body>
            <h1>Welcome!</h1>
            <a href="/about">About Us</a>
            <a href="https://www.external.com">External Link</a>
        </body></html>
        """
        mock_response = MagicMock()
        mock_response.text = sample_html
        mock_get.return_value = mock_response

        crawler = WebCrawler()
        crawler.crawl("https://example.com")

        self.assertIn("https://example.com/about", crawler.visited)

    @patch('requests.get')
    def test_crawl_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Test Error")

        crawler = WebCrawler()
        crawler.crawl("https://example.com")

    def test_search(self):
        crawler = WebCrawler()
        crawler.index["page1"] = "This has the keyword"
        crawler.index["page2"] = "No keyword here"

        results = crawler.search("keyword")
        self.assertEqual(results, ["page1"])  

    @patch('sys.stdout')
    def test_print_results(self, mock_stdout):
        crawler = WebCrawler()
        crawler.print_results(["https://test.com/result"])

    @patch('requests.get')
    def test_empty_html(self, mock_get):
        sample_html = ""
        mock_response = MagicMock()
        mock_response.text = sample_html
        mock_get.return_value = mock_response

        crawler = WebCrawler()
        crawler.crawl("https://example.com")

        # Check if the index is still empty
        self.assertEqual(len(crawler.index), 1)
        self.assertEqual(crawler.index["https://example.com"], "")

    @patch('requests.get')
    def test_non_html_content(self, mock_get):
        mock_response = MagicMock()
        mock_response.headers = {'Content-Type': 'application/pdf'}
        mock_get.return_value = mock_response

        crawler = WebCrawler()
        crawler.crawl("https://example.com")

        # Ensure we don't try to parse non-HTML content
        self.assertNotIn("https://example.com", crawler.index)

    @patch('requests.get')
    def test_malformed_url(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html><body><a href='htp://example.com'>Broken Link</a></body></html>"
        mock_get.return_value = mock_response

        crawler = WebCrawler()
        crawler.crawl("https://example.com")

        # Check that malformed URL was handled
        self.assertNotIn("htp://example.com", crawler.visited)  # Should not crawl malformed URLs

    def test_multiple_keyword_occurrences(self):
        crawler = WebCrawler()
        crawler.index["page1"] = "This page has the keyword multiple times: keyword keyword."
        crawler.index["page2"] = "No keyword here."

        results = crawler.search("keyword")
        self.assertEqual(results, ["page2"])  # Should only return "page2" since it's the only one without the keyword

    @patch('requests.get')
    def test_infinite_loop(self, mock_get):
        sample_html = """
        <html><body>
            <a href="https://example.com">Go to Example</a>
        </body></html>
        """
        mock_response = MagicMock()
        mock_response.text = sample_html
        mock_get.return_value = mock_response

        crawler = WebCrawler()
        crawler.crawl("https://example.com")

        # Check that we don't keep revisiting the same page
        self.assertEqual(len(crawler.visited), 1)  # Only one URL should be visited

if __name__ == "__main__":
    unittest.main()  # Run unit tests
    main()  # Run main app logic
