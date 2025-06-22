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
            # Step 1: Scrape data
            self.logger.info("📡 Step 1: Scraping OptiSigns help center...")
            scraped_articles = self.scrape_articles()
            
            # Step 2: Get local articles to compare against
            self.logger.info("📁 Step 2: Checking local articles directory...")
            local_articles = self.get_local_articles()
            
            # Step 3: Identify changes
            self.logger.info("🔍 Step 3: Comparing scraped vs local articles...")
            changes = self.identify_changes(scraped_articles, local_articles)
            
            # Step 4: Process changes and sync with OpenAI
            self.logger.info("☁️  Step 4: Processing changes and syncing with OpenAI...")
            upload_results = self.process_and_upload_changes(changes)
            
            # Step 5: Log final results
            self.logger.info("📊 Step 5: Logging final results...")
            self.log_final_results(upload_results, job_start)
            
            self.logger.info("✅ OptiSigns Help Center Sync Job completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Job failed with error: {e}", exc_info=True)
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
    
    def process_and_upload_changes(self, changes):
        """Process new, updated, and unchanged articles and sync with OpenAI."""
        results = {'uploaded': [], 'updated': [], 'skipped': [], 'deleted': [], 'failed': []}

        # --- Process NEW and UPDATED articles ---
        articles_to_sync = changes['new'] + changes['updated']
        
        for article_data in articles_to_sync:
            is_update = 'local_path' in article_data
            article_id = article_data['id']
            try:
                self.logger.info(f"🔄 Syncing {'updated' if is_update else 'new'} article: {article_id}")

                if is_update:
                    local_path = article_data['local_path']
                    tracking_info = self.file_tracker.get_tracking_info(os.path.abspath(local_path))
                    if tracking_info:
                        if tracking_info.get('vector_store_file_id'):
                            self.logger.info(f"🗑️  Removing old vector store file: {tracking_info.get('vector_store_file_id')}")
                            self.vector_store_manager.remove_file(self.vector_store_id, tracking_info.get('vector_store_file_id'))
                        if tracking_info.get('file_id'):
                            self.logger.info(f"🗑️  Removing old OpenAI file: {tracking_info.get('file_id')}")
                            self.file_manager.delete(tracking_info.get('file_id'))
                
                local_path = self.save_article_locally(article_data['data'])
                
                openai_file_id = self.file_manager.upload_markdown_file(local_path)
                vector_file_id = self.vector_store_manager.add_file(self.vector_store_id, openai_file_id)
                
                current_hash = self.file_tracker.get_file_hash(local_path)
                self.file_tracker.update_tracking(os.path.abspath(local_path), openai_file_id, vector_file_id, current_hash, local_path)
                
                if is_update:
                    results['updated'].append(article_id)
                else:
                    results['uploaded'].append(article_id)

            except Exception as e:
                self.logger.error(f"❌ Failed to sync article {article_id}: {e}", exc_info=True)
                results['failed'].append(article_id)

        # --- Process UNCHANGED articles ---
        for article_data in changes['unchanged']:
            article_id = article_data['id']
            local_path = article_data['local_path']
            tracking_info = self.file_tracker.get_tracking_info(os.path.abspath(local_path))
            
            if tracking_info and tracking_info.get('vector_store_file_id') and \
               self.vector_store_manager.get_file_by_id(self.vector_store_id, tracking_info.get('vector_store_file_id')):
                
                self.logger.info(f"✅ Article {article_id} is unchanged and verified. Skipping.")
                results['skipped'].append(article_id)
            else:
                self.logger.warning(f"⚠️  Article {article_id} was unchanged locally, but missing remotely. Re-uploading.")
                try:
                    openai_file_id = self.file_manager.upload_markdown_file(local_path)
                    vector_file_id = self.vector_store_manager.add_file(self.vector_store_id, openai_file_id)
                    current_hash = self.file_tracker.get_file_hash(local_path)
                    self.file_tracker.update_tracking(os.path.abspath(local_path), openai_file_id, vector_file_id, current_hash, local_path)
                    results['uploaded'].append(article_id)
                except Exception as e:
                    self.logger.error(f"❌ Failed to re-upload missing article {article_id}: {e}", exc_info=True)
                    results['failed'].append(article_id)

        self.logger.info(f"📊 Sync results: {len(results['uploaded'])} uploaded, {len(results['updated'])} updated, {len(results['skipped'])} skipped, {len(results['failed'])} failed")
        return results
    
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
                'updated': len(upload_results['updated']),
                'skipped': len(upload_results['skipped']),
                'deleted': len(upload_results['deleted']),
                'failed': len(upload_results['failed'])
            },
            'uploaded_articles': upload_results['uploaded'],
            'updated_articles': upload_results['updated'],
            'failed_articles': upload_results['failed']
        }
        
        # Save job summary
        self.job_logger.save_job_summary(summary)
        
        # Log summary
        self.logger.info("📊 Job Summary:")
        self.logger.info(f"   ⏱️  Duration: {duration.total_seconds():.2f} seconds")
        self.logger.info(f"   📤 Uploaded: {summary['results']['uploaded']}")
        self.logger.info(f"   🔄 Updated: {summary['results']['updated']}")
        self.logger.info(f"   ✅ Skipped: {summary['results']['skipped']}")
        self.logger.info(f"   🗑️  Deleted: {summary['results']['deleted']}")
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