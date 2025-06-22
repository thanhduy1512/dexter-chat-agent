#!/usr/bin/env python3
"""
OptiSigns Help Center Article Scraper
Scrapes articles from the OptiSigns help center API and saves them as markdown files.
"""

import requests
import json
import re
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import html2text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OptiSignsScraper:
    def __init__(self):
        self.base_url = os.getenv('OPTISIGNS_API_BASE_URL')
        if not self.base_url:
            raise ValueError("OPTISIGNS_API_BASE_URL not found in environment variables")
            
        self.output_dir = os.getenv('OUTPUT_DIRECTORY')
        if not self.output_dir:
            raise ValueError("OUTPUT_DIRECTORY not found in environment variables")
            
        self.h2t = html2text.HTML2Text()
        self.setup_html2text()
        
    def setup_html2text(self):
        """Configure html2text for optimal markdown conversion"""
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.ignore_emphasis = False
        self.h2t.body_width = 0  # Don't wrap text
        self.h2t.unicode_snob = True
        self.h2t.escape_snob = True
        self.h2t.skip_internal_links = False
        self.h2t.inline_links = True
        self.h2t.protect_links = True
        
    def fetch_articles(self, page=1, per_page=None):
        """Fetch articles from the OptiSigns API"""
        if per_page is None:
            per_page = int(os.getenv('ARTICLES_PER_PAGE'))
            if not per_page:
                raise ValueError("ARTICLES_PER_PAGE not found in environment variables")
            
        url = f"{self.base_url}?page={page}&per_page={per_page}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching articles: {e}")
            return None
            
    def clean_html_content(self, html_content):
        """Clean HTML content by removing unwanted elements"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove navigation elements, ads, and unwanted content
        unwanted_selectors = [
            'nav', '.nav', '.navigation',
            '.ad', '.advertisement', '.ads',
            '.sidebar', '.menu',
            '.footer', '.header',
            'script', 'style'
        ]
        
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()
                
        # Preserve relative links to OptiSigns articles
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/hc/en-us/articles/'):
                # Keep relative links as they are
                pass
            elif href.startswith('https://support.optisigns.com/hc/en-us/articles/'):
                # Convert absolute URLs to relative
                link['href'] = href.replace('https://support.optisigns.com', '')
                
        return str(soup)
        
    def html_to_markdown(self, html_content):
        """Convert HTML content to markdown"""
        # Clean the HTML first
        clean_html = self.clean_html_content(html_content)
        
        # Convert to markdown
        markdown = self.h2t.handle(clean_html)
        
        # Clean up the markdown
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)  # Remove excessive newlines
        markdown = markdown.strip()
        
        return markdown
        
    def sanitize_filename(self, filename):
        """Sanitize filename for safe file creation"""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', '_', filename)
        return filename
        
    def save_article(self, article):
        """Save a single article as markdown file"""
        article_id = article['id']
        title = article['title']
        
        # Create filename
        filename = f"{article_id}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        # Convert HTML body to markdown
        markdown_content = self.html_to_markdown(article['body'])
        
        # Create the full markdown document
        full_markdown = f"""# {title}

**Article ID:** {article_id}  
**Original URL:** {article['html_url']}  
**Created:** {article['created_at']}  
**Updated:** {article['updated_at']}

---

{markdown_content}

---
*Scraped from OptiSigns Help Center*
"""
        
        # Save to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_markdown)
            print(f"✓ Saved: {filename}")
            return True
        except Exception as e:
            print(f"✗ Error saving {filename}: {e}")
            return False
            
    def create_output_directory(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created output directory: {self.output_dir}")
            
    def scrape_articles(self, count=30):
        """Main function to scrape articles"""
        print(f"Starting to scrape {count} articles from OptiSigns Help Center...")
        
        # Create output directory
        self.create_output_directory()
        
        # Calculate pages needed
        per_page = int(os.getenv('ARTICLES_PER_PAGE'))
        if not per_page:
            raise ValueError("ARTICLES_PER_PAGE not found in environment variables")
        pages_needed = (count + per_page - 1) // per_page
        
        total_saved = 0
        
        for page in range(1, pages_needed + 1):
            print(f"\nFetching page {page}...")
            
            # Fetch articles for this page
            data = self.fetch_articles(page=page, per_page=per_page)
            
            if not data or 'articles' not in data:
                print(f"Error: No articles found on page {page}")
                continue
                
            articles = data['articles']
            
            # Process articles
            for article in articles:
                if total_saved >= count:
                    break
                    
                success = self.save_article(article)
                if success:
                    total_saved += 1
                    
            if total_saved >= count:
                break
                
        print(f"\n✅ Scraping complete! Saved {total_saved} articles to '{self.output_dir}/' directory.")
        return total_saved
    
    def scrape_all_articles(self):
        """Scrape all articles and return as dictionary with content"""
        print("Starting to scrape all articles from OptiSigns Help Center...")
        
        articles = {}
        page = 1
        per_page = int(os.getenv('ARTICLES_PER_PAGE', '30'))
        
        while True:
            print(f"Fetching page {page}...")
            
            # Fetch articles for this page
            data = self.fetch_articles(page=page, per_page=per_page)
            
            if not data or 'articles' not in data or not data['articles']:
                print(f"No more articles found on page {page}")
                break
                
            page_articles = data['articles']
            
            # Process articles
            for article in page_articles:
                article_id = str(article['id'])
                
                # Convert HTML body to markdown
                markdown_content = self.html_to_markdown(article['body'])
                
                # Create the full markdown document
                full_markdown = f"""# {article['title']}

**Article ID:** {article_id}  
**Original URL:** {article['html_url']}  
**Created:** {article['created_at']}  
**Updated:** {article['updated_at']}

---

{markdown_content}

---
*Scraped from OptiSigns Help Center*
"""
                
                articles[article_id] = {
                    'id': article_id,
                    'title': article['title'],
                    'url': article['html_url'],
                    'created_at': article['created_at'],
                    'updated_at': article['updated_at'],
                    'content': full_markdown
                }
            
            # Check if we've reached the end
            if len(page_articles) < per_page:
                break
            
            # break
            page += 1
                
        print(f"\n✅ Scraping complete! Found {len(articles)} articles.")
        return articles 