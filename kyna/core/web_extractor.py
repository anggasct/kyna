"""
Web Content Extraction Module - Extracts and processes web content.

This module provides functionality to extract content from web URLs and convert
it to clean markdown format for document processing.

Key components:
- `WebContentExtractor`: Main class for extracting web content
- URL validation and content extraction
- HTML to markdown conversion
- Metadata extraction (title, description)

Integration:
- Used by `DocumentProcessor` to handle URL-based documents
- Converts web content to a format suitable for RAG processing
"""
import logging
import re
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import html2text
from langchain.schema import Document

logger = logging.getLogger(__name__)


class WebContentExtractor:
    
    def __init__(self, timeout: int = 30, max_content_length: int = 10_000_000):
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.ignore_tables = False
        self.html_converter.body_width = 0
        self.html_converter.single_line_break = False
    
    def is_valid_url(self, url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def extract_content(self, url: str) -> Optional[Document]:
        if not self.is_valid_url(url):
            logger.error(f"Invalid URL: {url}")
            return None
        
        try:
            response = self._fetch_url(url)
            if not response:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            metadata = self._extract_metadata(soup, url)
            
            if 'wikipedia.org' in url:
                content = self._extract_wikipedia_content(soup)
            else:
                content = self._extract_main_content(soup)
            
            markdown_content = self._convert_to_markdown(content)
            
            if not markdown_content.strip():
                logger.warning(f"No meaningful content extracted from {url}")
                return None
            
            return Document(
                page_content=markdown_content,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            return None
    
    def _fetch_url(self, url: str) -> Optional[requests.Response]:
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_content_length:
                logger.warning(f"Content too large: {content_length} bytes from {url}")
                return None
            
            content_type = response.headers.get('content-type', '').lower()
            if not any(ct in content_type for ct in ['text/html', 'application/xhtml']):
                logger.warning(f"Unsupported content type: {content_type} from {url}")
                return None
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {str(e)}")
            return None
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        metadata = {
            'source': url,
            'type': 'web_content'
        }
        
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            metadata['description'] = meta_desc.get('content', '').strip()
        
        og_title = soup.find('meta', property='og:title')
        if og_title:
            metadata['og_title'] = og_title.get('content', '').strip()
        
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            metadata['og_description'] = og_desc.get('content', '').strip()
        
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            metadata['language'] = html_tag.get('lang')
        
        return metadata
    
    def _extract_main_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        unwanted_tags = [
            'script', 'style', 'nav', 'footer', 'header', 'aside',
            'form', 'button', 'input', 'select', 'textarea'
        ]
        
        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()
        unwanted_selectors = [
            'advertisement', 'ad(?!min)', 'ads', 'promo', 'social', 'share',
            'comment', 'comments', 'popup', 'modal'
        ]
        
        for selector in unwanted_selectors:
            for element in soup.find_all(class_=re.compile(selector, re.I)):
                element.decompose()
            for element in soup.find_all(id=re.compile(selector, re.I)):
                element.decompose()
        main_content = (
            soup.find('main') or 
            soup.find('article') or
            soup.find('div', {'id': 'mw-content-text'}) or
            soup.find('div', {'class': 'mw-parser-output'}) or
            soup.find('div', class_=re.compile('content|main|body', re.I)) or
            soup.find('div', id=re.compile('content|main|body', re.I)) or
            soup.find('body')
        )
        
        return main_content or soup
    
    def _extract_wikipedia_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        unwanted_wikipedia = [
            'script', 'style', 'nav', 'footer', 'header', 'aside',
            'form', 'button', 'input', 'select', 'textarea',
            'table.navbox', 'div.navbox', 'div.hatnote', 'div.dablink',
            'div.sistersitebox', 'div.ambox', 'div.mbox-small',
            'div.infobox', 'table.infobox', 'div.thumb',
            'div.printfooter', 'div.catlinks', 'div#toc'
        ]
        
        for selector in unwanted_wikipedia:
            if '.' in selector or '#' in selector:
                if '.' in selector:
                    tag, class_name = selector.split('.', 1)
                    elements = soup.find_all(tag, class_=class_name) if tag else soup.find_all(class_=class_name)
                elif '#' in selector:
                    tag, id_name = selector.split('#', 1)
                    elements = soup.find_all(tag, id=id_name) if tag else soup.find_all(id=id_name)
                else:
                    elements = soup.find_all(selector)
            else:
                elements = soup.find_all(selector)
            
            for element in elements:
                element.decompose()
        wiki_content = (
            soup.find('div', {'id': 'mw-content-text'}) or
            soup.find('main') or
            soup.find('div', {'class': 'mw-parser-output'}) or
            soup.find('body')
        )
        
        return wiki_content or soup
    
    def _convert_to_markdown(self, content: BeautifulSoup) -> str:
        try:
            html_content = str(content)
            markdown = self.html_converter.handle(html_content)
            markdown = self._clean_markdown(markdown)
            
            return markdown
            
        except Exception as e:
            logger.error(f"Error converting to markdown: {str(e)}")
            return ""
    
    def _clean_markdown(self, markdown: str) -> str:
        markdown = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown)
        markdown = re.sub(r'\[\s*\]\([^)]*\)', '', markdown)
        markdown = re.sub(r'^#+\s*$', '', markdown, flags=re.MULTILINE)
        markdown = re.sub(r'-{3,}', '---', markdown)
        markdown = markdown.strip()
        
        return markdown


def get_web_content_extractor() -> WebContentExtractor:
    return WebContentExtractor()