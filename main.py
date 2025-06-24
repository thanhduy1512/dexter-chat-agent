#!/usr/bin/env python3
"""
Help Center Sync Job
Scrapes help center articles and syncs them to OpenAI vector stores with intelligent delta detection.
"""

import os
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from src.scrapers.optisigns_scraper import OptiSignsScraper
from src.openai.file_manager import OpenAIFileManager
from src.openai.vector_store_manager import VectorStoreManager
from src.utils.file_tracker import FileTracker
from src.utils.job_logger import JobLogger

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/sync_job_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

class OptiSignsSyncJob:
    """Optimized sync job with fast file indexing, proper file replacement, and parallel processing"""
    
    def __init__(self, max_workers=5):
        self.scraper = OptiSignsScraper()
        self.file_manager = OpenAIFileManager()
        self.vector_manager = VectorStoreManager()
        self.file_tracker = FileTracker()
        self.job_logger = JobLogger()
        self.max_workers = max_workers
        self.lock = Lock()  # Thread-safe tracking updates
        
        self.vector_store_id = os.getenv('VECTOR_STORE_ID')
        if not self.vector_store_id:
            raise ValueError("VECTOR_STORE_ID not found in environment variables")
    
    def run(self):
        """Run the optimized sync job with parallel processing"""
        start_time = time.time()
        logging.info("🚀 Starting Help Center Sync Job (Parallel Processing)")
        
        try:
            # Step 1: Scrape articles
            logging.info("📡 Step 1: Scraping help center...")
            articles = self.scraper.scrape_all_articles()
            logging.info(f"✅ Scraped {len(articles)} articles from API")
            
            # Step 1.5: Download articles to disk
            logging.info(" Step 1.5: Downloading articles to disk...")
            self.scraper.create_output_directory()
            downloaded_count = 0
            for article_id, article in articles.items():
                filename = f"{article_id}.md"
                filepath = os.path.join(self.scraper.output_dir, filename)
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(article['content'])
                    downloaded_count += 1
                except Exception as e:
                    logging.error(f"❌ Failed to save article {article_id}: {e}")
            logging.info(f"✅ Downloaded {downloaded_count} articles to disk")
            
            # Step 2: Filter to only articles that exist locally
            logging.info("🔍 Step 2: Filtering to locally existing files...")
            local_articles = {}
            missing_local_count = 0
            
            for article_id, article in articles.items():
                filename = f"{article_id}.md"
                local_file_path = os.path.join(self.scraper.output_dir, filename)
                
                if os.path.exists(local_file_path):
                    local_articles[article_id] = article
                else:
                    missing_local_count += 1
                    logging.warning(f"⚠️ Article {article_id} exists in API but not locally: {filename}")
            
            logging.info(f"✅ Found {len(local_articles)} articles with local files, {missing_local_count} missing locally")
            
            if not local_articles:
                logging.warning("⚠️ No local files found to process!")
                return
            
            # Step 3: Create fast file index (ONCE)
            logging.info("🔍 Step 3: Creating fast file index...")
            file_index = self.vector_manager.create_file_index(self.vector_store_id)
            
            # Step 4: Process articles in parallel
            logging.info(f"⚡ Step 4: Processing articles with {self.max_workers} parallel workers...")
            uploaded_count = 0
            updated_count = 0
            skipped_count = 0
            failed_count = 0
            
            # Prepare articles for parallel processing
            articles_to_process = []
            for article_id, article in local_articles.items():
                articles_to_process.append((article_id, article, file_index))
            
            # Process articles in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_article = {
                    executor.submit(self.process_article_fast, article, file_index): article_id 
                    for article_id, article, file_index in articles_to_process
                }
                
                # Process completed tasks
                for future in as_completed(future_to_article):
                    article_id = future_to_article[future]
                    try:
                        result = future.result()
                        if result == 'uploaded':
                            uploaded_count += 1
                        elif result == 'updated':
                            updated_count += 1
                        elif result == 'skipped':
                            skipped_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        logging.error(f"❌ Error processing article {article_id}: {e}")
                        failed_count += 1
            
            # Step 5: Log results
            duration = time.time() - start_time
            summary = {
                'job_start': datetime.fromtimestamp(start_time).isoformat(),
                'job_end': datetime.now().isoformat(),
                'duration_seconds': round(duration, 2),
                'results': {
                    'uploaded': uploaded_count,
                    'updated': updated_count,
                    'skipped': skipped_count,
                    'failed': failed_count,
                    'missing_local': missing_local_count
                }
            }
            
            self.job_logger.save_job_summary(summary)
            
            logging.info("✅ Help Center Sync Job completed successfully!")
            logging.info(f"📊 Results: {uploaded_count} uploaded, {updated_count} updated, {skipped_count} skipped, {failed_count} failed, {missing_local_count} missing locally")
            logging.info(f"⏱️ Duration: {duration:.2f} seconds")
            logging.info(f"🚀 Parallel processing with {self.max_workers} workers")
            
        except Exception as e:
            logging.error(f"❌ Job failed: {e}")
            raise
    
    def process_article_fast(self, article, file_index):
        """Process a single article using fast file lookup and proper replacement (thread-safe)"""
        article_id = article['id']
        filename = f"{article_id}.md"
        file_key = filename
        local_file_path = os.path.join(self.scraper.output_dir, filename)
        current_hash = self.file_tracker.get_file_hash(local_file_path)
        tracking_info = self.file_tracker.get_tracking_info(file_key)

        # Helper: get OpenAI file ID from tracking
        openai_file_id = tracking_info['file_id'] if tracking_info else None
        vector_store_file_id = tracking_info['vector_store_file_id'] if tracking_info else None

        # 1. New file (no tracking)
        if not tracking_info:
            try:
                logging.info(f"📤 Uploading new article {article_id}...")
                openai_file_id = self.file_manager.upload_markdown_file(local_file_path)
                vector_store_file_id = self.vector_manager.add_file(self.vector_store_id, openai_file_id)
                with self.lock:
                    self.file_tracker.update_tracking(
                        file_key, openai_file_id, vector_store_file_id, current_hash, local_file_path
                    )
                logging.info(f"✅ Article {article_id} uploaded and added to vector store")
                return 'uploaded'
            except Exception as e:
                logging.error(f"❌ Failed to upload new article {article_id}: {e}")
                return 'failed'

        # 2. Unchanged file (hash matches)
        if tracking_info['hash'] == current_hash:
            logging.info(f"✅ Article {article_id} unchanged, skipping")
            return 'skipped'

        # 3. Changed file (hash mismatch)
        try:
            logging.info(f"🔄 Updating article {article_id} (content changed)...")
            # Upload new file to OpenAI
            new_openai_file_id = self.file_manager.upload_markdown_file(local_file_path)
            # Remove old from vector store (if present)
            if vector_store_file_id:
                self.vector_manager.remove_file(self.vector_store_id, vector_store_file_id)
                logging.info(f"🗑️ Removed old vector store file {vector_store_file_id}")
            # Add new to vector store
            new_vector_store_file_id = self.vector_manager.add_file(self.vector_store_id, new_openai_file_id)
            # Update tracking
            with self.lock:
                self.file_tracker.update_tracking(
                    file_key, new_openai_file_id, new_vector_store_file_id, current_hash, local_file_path
                )
            logging.info(f"✅ Article {article_id} updated in OpenAI and vector store")
            return 'updated'
        except Exception as e:
            logging.error(f"❌ Failed to update article {article_id}: {e}")
            return 'failed'

def main():
    """Main entry point"""
    # You can adjust max_workers based on your needs
    # Higher numbers = faster but more API rate limiting risk
    job = OptiSignsSyncJob(max_workers=5)
    job.run()

if __name__ == "__main__":
    main() 