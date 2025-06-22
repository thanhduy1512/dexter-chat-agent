#!/usr/bin/env python3
"""
OptiSigns Help Center Sync Job
Main job that handles the complete flow:
1. Scrape data from OptiSigns help center
2. Check existence in local /articles directory
3. Compare content (hash, last-modified)
4. Check existence in OpenAI files and vector store
5. Upload only delta (new/updated articles)
6. Log final results with counts and links
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.optisigns_scraper import OptiSignsScraper
from openai.file_manager import OpenAIFileManager
from openai.vector_store_manager import VectorStoreManager
from utils.file_tracker import FileTracker
from utils.file_converter import FileConverter
from utils.job_logger import JobLogger

# Load environment variables
load_dotenv()

class OptiSignsSyncJob:
    """Main job orchestrator for OptiSigns help center synchronization"""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.scraper = OptiSignsScraper()
        self.file_manager = OpenAIFileManager()
        self.vector_store_manager = VectorStoreManager()
        self.file_tracker = FileTracker()
        self.file_converter = FileConverter()
        self.job_logger = JobLogger()
        
        # Job configuration
        self.articles_dir = os.getenv('OUTPUT_DIRECTORY', 'articles')
        self.vector_store_id = os.getenv('VECTOR_STORE_ID')
        
        if not self.vector_store_id:
            raise ValueError("VECTOR_STORE_ID not found in environment variables")
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"{log_dir}/sync_job_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.log_file = log_file
    
    def run(self):
        """Main job execution"""
        job_start = datetime.now()
        self.logger.info("🚀 Starting OptiSigns Help Center Sync Job")
        
        try:
            # Step 1: Scrape data from OptiSigns help center
            self.logger.info("📡 Step 1: Scraping OptiSigns help center...")
            scraped_articles = self.scrape_articles()
            
            # Step 2: Check existence in local /articles directory
            self.logger.info("📁 Step 2: Checking local articles directory...")
            local_articles = self.get_local_articles()
            
            # Step 3: Compare and identify changes
            self.logger.info("🔍 Step 3: Comparing scraped vs local articles...")
            changes = self.identify_changes(scraped_articles, local_articles)
            
            # Step 4: Check existence in OpenAI and vector store
            self.logger.info("☁️  Step 4: Checking OpenAI and vector store...")
            existing_files = self.check_existing_files(changes)
            
            # Step 5: Upload delta (new/updated articles)
            self.logger.info("📤 Step 5: Uploading delta to OpenAI and vector store...")
            upload_results = self.upload_delta(changes, existing_files)
            
            # Step 6: Log final results
            self.logger.info("📊 Step 6: Logging final results...")
            self.log_final_results(upload_results, job_start)
            
            self.logger.info("✅ OptiSigns Help Center Sync Job completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Job failed with error: {e}")
            self.log_job_failure(e, job_start)
            return False
    
    def scrape_articles(self):
        """Scrape articles from OptiSigns help center"""
        try:
            articles = self.scraper.scrape_all_articles()
            self.logger.info(f"📡 Scraped {len(articles)} articles from OptiSigns help center")
            return articles
        except Exception as e:
            self.logger.error(f"❌ Failed to scrape articles: {e}")
            raise
    
    def get_local_articles(self):
        """Get existing articles from local directory"""
        articles_dir = Path(self.articles_dir)
        if not articles_dir.exists():
            self.logger.info(f"📁 Local articles directory {self.articles_dir} does not exist")
            return {}
        
        local_articles = {}
        for md_file in articles_dir.glob("*.md"):
            article_id = md_file.stem
            local_articles[article_id] = {
                'path': str(md_file),
                'hash': self.file_tracker.get_file_hash(str(md_file)),
                'modified': md_file.stat().st_mtime
            }
        
        self.logger.info(f"📁 Found {len(local_articles)} local articles")
        return local_articles
    
    def identify_changes(self, scraped_articles, local_articles):
        """Identify new, updated, and unchanged articles"""
        changes = {
            'new': [],
            'updated': [],
            'unchanged': [],
            'deleted': []
        }
        
        # Check for new and updated articles
        for article_id, scraped_data in scraped_articles.items():
            if article_id not in local_articles:
                changes['new'].append({
                    'id': article_id,
                    'data': scraped_data
                })
            else:
                local_data = local_articles[article_id]
                # Compare content hash or last modified
                if self.has_content_changed(scraped_data, local_data):
                    changes['updated'].append({
                        'id': article_id,
                        'data': scraped_data,
                        'local_path': local_data['path']
                    })
                else:
                    changes['unchanged'].append({
                        'id': article_id,
                        'local_path': local_data['path']
                    })
        
        # Check for deleted articles (in local but not in scraped)
        for article_id in local_articles:
            if article_id not in scraped_articles:
                changes['deleted'].append({
                    'id': article_id,
                    'local_path': local_articles[article_id]['path']
                })
        
        self.logger.info(f"🔍 Changes identified: {len(changes['new'])} new, {len(changes['updated'])} updated, {len(changes['unchanged'])} unchanged, {len(changes['deleted'])} deleted")
        return changes
    
    def has_content_changed(self, scraped_data, local_data):
        """Check if content has changed by comparing hash or last modified"""
        # For now, we'll use a simple approach - if the scraped content hash differs from local
        # In a real implementation, you might want to compare the actual content
        scraped_hash = self.file_tracker.get_file_hash_from_content(scraped_data.get('content', ''))
        return scraped_hash != local_data['hash']
    
    def check_existing_files(self, changes):
        """Check which files already exist in OpenAI and vector store"""
        existing_files = {
            'openai': set(),
            'vector_store': set()
        }
        
        # Check OpenAI files
        try:
            openai_files = self.file_manager.list_all_files()
            for file_info in openai_files:
                filename = file_info.get('filename', '')
                article_id = filename.replace('.txt', '')
                existing_files['openai'].add(article_id)
        except Exception as e:
            self.logger.warning(f"⚠️  Could not check OpenAI files: {e}")
        
        # Check vector store files
        try:
            vector_files = self.vector_store_manager.list_all_files(self.vector_store_id)
            for file_info in vector_files:
                openai_file_id = file_info.get('file_id')
                if openai_file_id:
                    file_info = self.file_manager.get_by_id(openai_file_id)
                    if file_info:
                        filename = file_info.get('filename', '')
                        article_id = filename.replace('.txt', '')
                        existing_files['vector_store'].add(article_id)
        except Exception as e:
            self.logger.warning(f"⚠️  Could not check vector store files: {e}")
        
        self.logger.info(f"☁️  Found {len(existing_files['openai'])} files in OpenAI, {len(existing_files['vector_store'])} in vector store")
        return existing_files
    
    def upload_delta(self, changes, existing_files):
        """Upload only new and updated articles"""
        results = {
            'uploaded': [],
            'skipped': [],
            'failed': []
        }
        
        # Process new articles
        for article in changes['new']:
            try:
                result = self.upload_article(article['data'], existing_files)
                if result['success']:
                    results['uploaded'].append(article['id'])
                else:
                    results['failed'].append(article['id'])
            except Exception as e:
                self.logger.error(f"❌ Failed to upload new article {article['id']}: {e}")
                results['failed'].append(article['id'])
        
        # Process updated articles
        for article in changes['updated']:
            try:
                result = self.upload_article(article['data'], existing_files, article['local_path'])
                if result['success']:
                    results['uploaded'].append(article['id'])
                else:
                    results['failed'].append(article['id'])
            except Exception as e:
                self.logger.error(f"❌ Failed to upload updated article {article['id']}: {e}")
                results['failed'].append(article['id'])
        
        # Process unchanged articles
        for article in changes['unchanged']:
            results['skipped'].append(article['id'])
        
        self.logger.info(f"📤 Upload results: {len(results['uploaded'])} uploaded, {len(results['skipped'])} skipped, {len(results['failed'])} failed")
        return results
    
    def upload_article(self, article_data, existing_files, local_path=None):
        """Upload a single article to OpenAI and vector store"""
        article_id = article_data['id']
        
        # Check if already exists
        if article_id in existing_files['vector_store']:
            return {'success': True, 'action': 'skipped', 'reason': 'already_exists'}
        
        # Save article to local directory if needed
        if not local_path:
            local_path = self.save_article_locally(article_data)
        
        # Upload to OpenAI
        try:
            openai_file_id = self.file_manager.upload_markdown_file(local_path)
            
            # Add to vector store
            vector_file_id = self.vector_store_manager.add_file(self.vector_store_id, openai_file_id)
            
            # Update tracking
            self.file_tracker.update_tracking(local_path, openai_file_id, vector_file_id)
            
            return {'success': True, 'action': 'uploaded', 'openai_file_id': openai_file_id, 'vector_file_id': vector_file_id}
            
        except Exception as e:
            self.logger.error(f"❌ Failed to upload article {article_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def save_article_locally(self, article_data):
        """Save article to local directory"""
        os.makedirs(self.articles_dir, exist_ok=True)
        file_path = os.path.join(self.articles_dir, f"{article_data['id']}.md")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(article_data['content'])
        
        return file_path
    
    def log_final_results(self, upload_results, job_start):
        """Log final job results"""
        job_end = datetime.now()
        duration = job_end - job_start
        
        summary = {
            'job_start': job_start.isoformat(),
            'job_end': job_end.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'log_file': self.log_file,
            'results': {
                'uploaded': len(upload_results['uploaded']),
                'skipped': len(upload_results['skipped']),
                'failed': len(upload_results['failed'])
            },
            'uploaded_articles': upload_results['uploaded'],
            'failed_articles': upload_results['failed']
        }
        
        # Save job summary
        self.job_logger.save_job_summary(summary)
        
        # Log summary
        self.logger.info("📊 Job Summary:")
        self.logger.info(f"   ⏱️  Duration: {duration.total_seconds():.2f} seconds")
        self.logger.info(f"   📤 Uploaded: {summary['results']['uploaded']}")
        self.logger.info(f"   ✅ Skipped: {summary['results']['skipped']}")
        self.logger.info(f"   ❌ Failed: {summary['results']['failed']}")
        self.logger.info(f"   📄 Log file: {self.log_file}")
        
        if upload_results['failed']:
            self.logger.warning(f"   ⚠️  Failed articles: {upload_results['failed']}")
    
    def log_job_failure(self, error, job_start):
        """Log job failure"""
        job_end = datetime.now()
        duration = job_end - job_start
        
        summary = {
            'job_start': job_start.isoformat(),
            'job_end': job_end.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'log_file': self.log_file,
            'status': 'failed',
            'error': str(error)
        }
        
        self.job_logger.save_job_summary(summary)
        self.logger.error(f"❌ Job failed after {duration.total_seconds():.2f} seconds")

def main():
    """Main entry point"""
    job = OptiSignsSyncJob()
    success = job.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 