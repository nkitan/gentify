"""
Unit tests for web scraper module.
"""

import pytest
import requests
from unittest.mock import patch, MagicMock
from src.web_scraper.scraper import WebScraper, WebScraperError


class TestWebScraper:
    """Test cases for WebScraper class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = WebScraper(delay=0.1)  # Use small delay for testing
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.scraper.close()
    
    @patch('src.web_scraper.scraper.requests.Session.get')
    def test_scrape_text_success(self, mock_get):
        """Test successful text scraping."""
        # Mock HTML response
        mock_response = MagicMock()
        mock_response.content = b"""
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Welcome</h1>
                <p>This is a test paragraph.</p>
                <script>console.log('test');</script>
                <style>body { color: black; }</style>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test text extraction
        url = "https://example.com"
        text = self.scraper.scrape_text(url)
        
        # Verify script and style tags were removed
        assert "console.log" not in text
        assert "color: black" not in text
        assert "Welcome" in text
        assert "This is a test paragraph." in text
        
        # Verify request was made
        mock_get.assert_called_once_with(url, timeout=30)
    
    @patch('src.web_scraper.scraper.requests.Session.get')
    def test_scrape_with_selector_success(self, mock_get):
        """Test successful scraping with CSS selector."""
        # Mock HTML response
        mock_response = MagicMock()
        mock_response.content = b"""
        <html>
            <body>
                <div class="content">
                    <p>First paragraph</p>
                    <p>Second paragraph</p>
                </div>
                <div class="sidebar">
                    <p>Sidebar content</p>
                </div>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test selector-based extraction
        url = "https://example.com"
        content = self.scraper.scrape_with_selector(url, ".content p")
        
        assert "First paragraph" in content
        assert "Second paragraph" in content
        assert "Sidebar content" not in content
    
    @patch('src.web_scraper.scraper.requests.Session.get')
    def test_scrape_links_success(self, mock_get):
        """Test successful link extraction."""
        # Mock HTML response
        mock_response = MagicMock()
        mock_response.content = b"""
        <html>
            <body>
                <a href="/page1" title="Page 1">Internal Link</a>
                <a href="https://external.com" title="External">External Link</a>
                <a href="mailto:test@example.com">Email Link</a>
                <a href="#section1">Anchor Link</a>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test link extraction
        url = "https://example.com"
        links = self.scraper.scrape_links(url, filter_internal=False)
        
        assert len(links) == 4
        
        # Check link details
        internal_link = next(link for link in links if link["text"] == "Internal Link")
        assert internal_link["href"] == "/page1"
        assert internal_link["title"] == "Page 1"
        assert internal_link["is_internal"] is True
        
        external_link = next(link for link in links if link["text"] == "External Link")
        assert external_link["href"] == "https://external.com"
        assert external_link["is_internal"] is False
    
    @patch('src.web_scraper.scraper.requests.Session.get')
    def test_scrape_images_success(self, mock_get):
        """Test successful image extraction."""
        # Mock HTML response
        mock_response = MagicMock()
        mock_response.content = b"""
        <html>
            <body>
                <img src="/image1.jpg" alt="Image 1" width="100" height="200">
                <img src="https://example.com/image2.png" alt="Image 2" title="Second Image">
                <img src="data:image/gif;base64,..." alt="Data URL Image">
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test image extraction
        url = "https://example.com"
        images = self.scraper.scrape_images(url)
        
        assert len(images) == 3
        
        # Check image details
        first_image = images[0]
        assert first_image["src"] == "/image1.jpg"
        assert first_image["alt"] == "Image 1"
        assert first_image["width"] == "100"
        assert first_image["height"] == "200"
        
        second_image = images[1]
        assert second_image["src"] == "https://example.com/image2.png"
        assert second_image["title"] == "Second Image"
    
    @patch('src.web_scraper.scraper.requests.Session.get')
    def test_scrape_table_success(self, mock_get):
        """Test successful table extraction."""
        # Mock HTML response
        mock_response = MagicMock()
        mock_response.content = b"""
        <html>
            <body>
                <table>
                    <tr>
                        <th>Name</th>
                        <th>Age</th>
                        <th>City</th>
                    </tr>
                    <tr>
                        <td>Alice</td>
                        <td>25</td>
                        <td>New York</td>
                    </tr>
                    <tr>
                        <td>Bob</td>
                        <td>30</td>
                        <td>San Francisco</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test table extraction
        url = "https://example.com"
        table_data = self.scraper.scrape_table(url)
        
        assert len(table_data) == 3  # Header + 2 data rows
        
        # Check header row
        assert table_data[0] == ["Name", "Age", "City"]
        
        # Check data rows
        assert table_data[1] == ["Alice", "25", "New York"]
        assert table_data[2] == ["Bob", "30", "San Francisco"]
    
    @patch('src.web_scraper.scraper.requests.Session.get')
    def test_scrape_metadata_success(self, mock_get):
        """Test successful metadata extraction."""
        # Mock HTML response
        mock_response = MagicMock()
        mock_response.content = b"""
        <html lang="en">
            <head>
                <title>Test Page Title</title>
                <meta name="description" content="This is a test page description">
                <meta name="keywords" content="test, page, example">
                <meta name="author" content="Test Author">
                <meta property="og:description" content="OpenGraph description">
            </head>
            <body>
                <h1>Content</h1>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test metadata extraction
        url = "https://example.com"
        metadata = self.scraper.scrape_metadata(url)
        
        assert metadata["url"] == url
        assert metadata["title"] == "Test Page Title"
        assert metadata["description"] == "This is a test page description"
        assert metadata["keywords"] == "test, page, example"
        assert metadata["author"] == "Test Author"
        assert metadata["language"] == "en"
    
    @patch('src.web_scraper.scraper.requests.Session.get')
    def test_request_timeout(self, mock_get):
        """Test request timeout handling."""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        url = "https://example.com"
        
        with pytest.raises(WebScraperError, match="Request timeout"):
            self.scraper.scrape_text(url)
    
    @patch('src.web_scraper.scraper.requests.Session.get')
    def test_connection_error(self, mock_get):
        """Test connection error handling."""
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        url = "https://example.com"
        
        with pytest.raises(WebScraperError, match="Connection error"):
            self.scraper.scrape_text(url)
    
    @patch('src.web_scraper.scraper.requests.Session.get')
    def test_http_error(self, mock_get):
        """Test HTTP error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        http_error = requests.exceptions.HTTPError(response=mock_response)
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response
        
        url = "https://example.com"
        
        with pytest.raises(WebScraperError, match="HTTP error 404"):
            self.scraper.scrape_text(url)
    
    @patch('src.web_scraper.scraper.requests.Session.get')
    def test_rate_limiting(self, mock_get):
        """Test rate limiting functionality."""
        import time
        
        mock_response = MagicMock()
        mock_response.content = b"<html><body>Test</body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Set a longer delay for testing
        self.scraper.delay = 0.2
        
        url = "https://example.com"
        
        # Make first request and record time
        start_time = time.time()
        self.scraper.scrape_text(url)
        first_request_time = time.time()
        
        # Make second request
        self.scraper.scrape_text(url)
        second_request_time = time.time()
        
        # Check that delay was enforced
        total_time = second_request_time - start_time
        assert total_time >= self.scraper.delay
    
    @patch('src.web_scraper.scraper.requests.Session.get')
    def test_no_table_found(self, mock_get):
        """Test table extraction when no table exists."""
        mock_response = MagicMock()
        mock_response.content = b"<html><body><p>No table here</p></body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        url = "https://example.com"
        
        with pytest.raises(WebScraperError, match="No table found"):
            self.scraper.scrape_table(url)
    
    @patch('src.web_scraper.scraper.requests.Session.get')
    def test_empty_selector_results(self, mock_get):
        """Test scraping with selector that matches no elements."""
        mock_response = MagicMock()
        mock_response.content = b"<html><body><p>Content</p></body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        url = "https://example.com"
        content = self.scraper.scrape_with_selector(url, ".nonexistent")
        
        assert content == ""
    
    def test_context_manager(self):
        """Test using scraper as context manager."""
        with patch('src.web_scraper.scraper.requests.Session.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"<html><body>Test</body></html>"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            with WebScraper() as scraper:
                result = scraper.scrape_text("https://example.com")
                assert "Test" in result
        
        # Session should be closed after context exit
        # We can't easily test this without accessing private attributes
        # but the close method should have been called
    
    def test_scraper_configuration(self):
        """Test scraper configuration options."""
        custom_scraper = WebScraper(
            delay=2.0,
            timeout=60,
            user_agent="CustomBot/1.0"
        )
        
        assert custom_scraper.delay == 2.0
        assert custom_scraper.timeout == 60
        assert "CustomBot/1.0" in custom_scraper.session.headers["User-Agent"]
        
        custom_scraper.close()


class TestWebScraperIntegration:
    """Integration tests for web scraper functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = WebScraper(delay=0.1)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.scraper.close()
    
    @patch('src.web_scraper.scraper.requests.Session.get')
    def test_complete_page_scraping_workflow(self, mock_get):
        """Test complete workflow of scraping different elements from a page."""
        # Mock comprehensive HTML response
        mock_response = MagicMock()
        mock_response.content = b"""
        <html lang="en">
            <head>
                <title>Complete Test Page</title>
                <meta name="description" content="A comprehensive test page">
                <meta name="author" content="Test Suite">
            </head>
            <body>
                <header>
                    <h1>Main Title</h1>
                    <nav>
                        <a href="/home">Home</a>
                        <a href="/about">About</a>
                        <a href="https://external.com">External</a>
                    </nav>
                </header>
                <main>
                    <article class="content">
                        <h2>Article Title</h2>
                        <p>This is the main content of the article.</p>
                        <img src="/image1.jpg" alt="Article Image">
                    </article>
                    <table class="data-table">
                        <tr><th>Product</th><th>Price</th></tr>
                        <tr><td>Widget</td><td>$10</td></tr>
                        <tr><td>Gadget</td><td>$20</td></tr>
                    </table>
                </main>
                <footer>
                    <p>Footer content</p>
                </footer>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        url = "https://example.com"
        
        # Test 1: Extract metadata
        metadata = self.scraper.scrape_metadata(url)
        assert metadata["title"] == "Complete Test Page"
        assert metadata["description"] == "A comprehensive test page"
        
        # Test 2: Extract all text
        text = self.scraper.scrape_text(url)
        assert "Main Title" in text
        assert "Article Title" in text
        assert "Footer content" in text
        
        # Test 3: Extract specific content
        content = self.scraper.scrape_with_selector(url, ".content")
        assert "Article Title" in content
        assert "main content of the article" in content
        assert "Footer content" not in content
        
        # Test 4: Extract links
        links = self.scraper.scrape_links(url)
        link_texts = [link["text"] for link in links]
        assert "Home" in link_texts
        assert "About" in link_texts
        assert "External" in link_texts
        
        # Test 5: Extract images
        images = self.scraper.scrape_images(url)
        assert len(images) == 1
        assert images[0]["src"] == "/image1.jpg"
        assert images[0]["alt"] == "Article Image"
        
        # Test 6: Extract table
        table_data = self.scraper.scrape_table(url, ".data-table")
        assert len(table_data) == 3  # Header + 2 rows
        assert table_data[0] == ["Product", "Price"]
        assert table_data[1] == ["Widget", "$10"]
        assert table_data[2] == ["Gadget", "$20"]
