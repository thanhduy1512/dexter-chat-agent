#!/usr/bin/env python3
"""
Optimized Cleanup Script
Deletes all files from OpenAI files and vector store with parallel processing for speed.
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from src.openai.file_manager import OpenAIFileManager
from src.openai.vector_store_manager import VectorStoreManager
from src.utils.file_tracker import FileTracker

# Load environment variables
load_dotenv()

def cleanup_all(max_workers=10):
    """Clean up all files from OpenAI and vector store with parallel processing"""
    start_time = time.time()
    print("🧹 Starting optimized cleanup...")
    
    # Get environment variables
    vector_store_id = os.getenv('VECTOR_STORE_ID')
    if not vector_store_id:
        print("❌ VECTOR_STORE_ID not found in environment variables")
        return
    
    # Initialize managers
    file_manager = OpenAIFileManager()
    vector_manager = VectorStoreManager()
    file_tracker = FileTracker()
    
    print("📁 Step 1: Cleaning up vector store files...")
    try:
        # Delete all files from vector store (this is already fast)
        success = vector_manager.delete_all_files(vector_store_id)
        if success:
            print("✅ Vector store files deleted successfully")
        else:
            print("⚠️  Some vector store files may not have been deleted")
    except Exception as e:
        print(f"❌ Error deleting vector store files: {e}")
    
    print("📄 Step 2: Cleaning up OpenAI files with parallel processing...")
    try:
        # Get all files from OpenAI
        files = file_manager.list_all_files()
        print(f"Found {len(files)} files to delete")
        
        deleted_count = 0
        failed_count = 0
        
        # Process files in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all delete tasks
            future_to_file = {
                executor.submit(file_manager.delete, file.get('id')): file 
                for file in files if file.get('id')
            }
            
            # Process completed tasks
            for future in as_completed(future_to_file):
                file = future_to_file[future]
                file_id = file.get('id')
                filename = file.get('filename', file_id)
                
                try:
                    success = future.result()
                    if success:
                        deleted_count += 1
                        print(f"✅ Deleted: {filename}")
                    else:
                        failed_count += 1
                        print(f"❌ Failed to delete: {filename}")
                except Exception as e:
                    failed_count += 1
                    print(f"❌ Error deleting {filename}: {e}")
        
        print(f"✅ Deleted {deleted_count} OpenAI files, {failed_count} failed")
    except Exception as e:
        print(f"❌ Error listing/deleting OpenAI files: {e}")
    
    print("📋 Step 3: Clearing local tracking file...")
    try:
        file_tracker.clear_tracking()
        print("✅ Local tracking file cleared")
    except Exception as e:
        print(f"❌ Error clearing tracking file: {e}")
    
    duration = time.time() - start_time
    print(f"🎉 Cleanup completed in {duration:.2f} seconds!")
    print(f"⚡ Parallel processing with {max_workers} workers")

if __name__ == "__main__":
    cleanup_all() 