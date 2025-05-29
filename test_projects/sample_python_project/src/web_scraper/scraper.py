"""
Web Scraper Module

This module provides web scraping capabilities using requests and BeautifulSoup
for extracting content from web pages with proper error handling and rate limiting.
"""

import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse
import logging


class WebScraperError(Exception):
    """Custom exception for web scraping operations."""
    pass


class WebScraper:
    """
    A web scraping utility class for extracting content from web pages.
    
    Provides methods for scraping text content, specific elements,
    and structured data with built-in rate limiting and error handling.
    """
    
    def __init__(self, delay: float = 1.0, timeout: int = 30, 
                 user_agent: str = "SampleBot/1.0"):
        """
        Initialize the web scraper.
        
        Args:
            delay (float): Delay between requests in seconds
            timeout (int): Request timeout in seconds
            user_agent (str): User agent string for requests
        """
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.logger = logging.getLogger(__name__)
        self._last_request_time = 0
    
    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.delay:
            sleep_time = self.delay - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _make_request(self, url: str) -> requests.Response:
        """
        Make a HTTP request with rate limiting and error handling.
        
        Args:
            url (str): URL to request
            
        Returns:
            requests.Response: HTTP response
            
        Raises:
            WebScraperError: If request fails
        """
        self._rate_limit()
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            self.logger.info(f"Successfully fetched: {url}")
            return response
            
        except requests.exceptions.Timeout:
            raise WebScraperError(f"Request timeout for URL: {url}")
        except requests.exceptions.ConnectionError:
            raise WebScraperError(f"Connection error for URL: {url}")
        except requests.exceptions.HTTPError as e:
            raise WebScraperError(f"HTTP error {e.response.status_code} for URL: {url}")
        except Exception as e:
            raise WebScraperError(f"Request failed for URL {url}: {e}")
    
    def scrape_text(self, url: str) -> str:
        """
        Scrape and extract all text content from a web page.
        
        Args:
            url (str): URL to scrape
            
        Returns:
            str: Extracted text content
            
        Raises:
            WebScraperError: If scraping fails
        """
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean it up
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            raise WebScraperError(f"Text extraction failed for {url}: {e}")
    
    def scrape_with_selector(self, url: str, css_selector: str) -> str:
        """
        Scrape content using a CSS selector.
        
        Args:
            url (str): URL to scrape
            css_selector (str): CSS selector for target elements
            
        Returns:
            str: Content from selected elements
            
        Raises:
            WebScraperError: If scraping fails
        """
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            elements = soup.select(css_selector)
            
            if not elements:
                self.logger.warning(f"No elements found for selector '{css_selector}' on {url}")
                return ""
            
            content_parts = []
            for element in elements:
                text = element.get_text(strip=True)
                if text:
                    content_parts.append(text)
            
            return '\n'.join(content_parts)
            
        except Exception as e:
            raise WebScraperError(f"Selector-based extraction failed for {url}: {e}")
    
    def scrape_links(self, url: str, filter_internal: bool = True) -> List[Dict[str, str]]:
        """
        Extract all links from a web page.
        
        Args:
            url (str): URL to scrape
            filter_internal (bool): Whether to include only internal links
            
        Returns:
            List[Dict[str, str]]: List of link information
            
        Raises:
            WebScraperError: If scraping fails
        """
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            base_domain = urlparse(url).netloc
            links = []
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(url, href)
                link_domain = urlparse(absolute_url).netloc
                
                # Filter internal links if requested
                if filter_internal and link_domain != base_domain:
                    continue
                
                link_info = {
                    'text': link.get_text(strip=True),
                    'href': href,
                    'absolute_url': absolute_url,
                    'title': link.get('title', ''),
                    'is_internal': link_domain == base_domain
                }
                
                links.append(link_info)
            
            self.logger.info(f"Extracted {len(links)} links from {url}")
            return links
            
        except Exception as e:
            raise WebScraperError(f"Link extraction failed for {url}: {e}")
    
    def scrape_images(self, url: str) -> List[Dict[str, str]]:
        """
        Extract image information from a web page.
        
        Args:
            url (str): URL to scrape
            
        Returns:
            List[Dict[str, str]]: List of image information
            
        Raises:
            WebScraperError: If scraping fails
        """
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            images = []
            
            for img in soup.find_all('img'):
                src = img.get('src')
                if not src:
                    continue
                
                absolute_url = urljoin(url, src)
                
                image_info = {
                    'src': src,
                    'absolute_url': absolute_url,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', ''),
                    'width': img.get('width', ''),
                    'height': img.get('height', '')
                }
                
                images.append(image_info)
            
            self.logger.info(f"Extracted {len(images)} images from {url}")
            return images
            
        except Exception as e:
            raise WebScraperError(f"Image extraction failed for {url}: {e}")
    
    def scrape_table(self, url: str, table_selector: str = "table") -> List[List[str]]:
        """
        Extract table data from a web page.
        
        Args:
            url (str): URL to scrape
            table_selector (str): CSS selector for the table
            
        Returns:
            List[List[str]]: Table data as rows and columns
            
        Raises:
            WebScraperError: If scraping fails
        """
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            table = soup.select_one(table_selector)
            if not table:
                raise WebScraperError(f"No table found with selector '{table_selector}'")
            
            rows = []
            for tr in table.find_all('tr'):
                cells = []
                for cell in tr.find_all(['td', 'th']):
                    cells.append(cell.get_text(strip=True))
                if cells:  # Only add non-empty rows
                    rows.append(cells)
            
            self.logger.info(f"Extracted table with {len(rows)} rows from {url}")
            return rows
            
        except Exception as e:
            raise WebScraperError(f"Table extraction failed for {url}: {e}")
    
    def scrape_metadata(self, url: str) -> Dict[str, str]:
        """
        Extract metadata from a web page (title, description, etc.).
        
        Args:
            url (str): URL to scrape
            
        Returns:
            Dict[str, str]: Page metadata
            
        Raises:
            WebScraperError: If scraping fails
        """
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            metadata = {
                'url': url,
                'title': '',
                'description': '',
                'keywords': '',
                'author': '',
                'language': ''
            }
            
            # Extract title
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text(strip=True)
            
            # Extract meta tags
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                name = meta.get('name', '').lower()
                property_attr = meta.get('property', '').lower()
                content = meta.get('content', '')
                
                if name == 'description' or property_attr == 'og:description':
                    metadata['description'] = content
                elif name == 'keywords':
                    metadata['keywords'] = content
                elif name == 'author':
                    metadata['author'] = content
                elif name == 'language' or property_attr == 'og:locale':
                    metadata['language'] = content
            
            # Extract language from html tag
            html_tag = soup.find('html')
            if html_tag and not metadata['language']:
                metadata['language'] = html_tag.get('lang', '')
            
            return metadata
            
        except Exception as e:
            raise WebScraperError(f"Metadata extraction failed for {url}: {e}")
    
    def close(self) -> None:
        """Close the session and clean up resources."""
        self.session.close()
        self.logger.info("Web scraper session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
