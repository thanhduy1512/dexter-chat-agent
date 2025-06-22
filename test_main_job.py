#!/usr/bin/env python3
"""
Test script for the main OptiSigns sync job
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from src.scrapers.optisigns_scraper import OptiSignsScraper
        print("✅ OptiSignsScraper imported successfully")
    except Exception as e:
        print(f"❌ Failed to import OptiSignsScraper: {e}")
        return False
    
    try:
        from src.openai.file_manager import OpenAIFileManager
        print("✅ OpenAIFileManager imported successfully")
    except Exception as e:
        print(f"❌ Failed to import OpenAIFileManager: {e}")
        return False
    
    try:
        from src.openai.vector_store_manager import VectorStoreManager
        print("✅ VectorStoreManager imported successfully")
    except Exception as e:
        print(f"❌ Failed to import VectorStoreManager: {e}")
        return False
    
    try:
        from src.utils.file_tracker import FileTracker
        print("✅ FileTracker imported successfully")
    except Exception as e:
        print(f"❌ Failed to import FileTracker: {e}")
        return False
    
    try:
        from src.utils.file_converter import FileConverter
        print("✅ FileConverter imported successfully")
    except Exception as e:
        print(f"❌ Failed to import FileConverter: {e}")
        return False
    
    try:
        from src.utils.job_logger import JobLogger
        print("✅ JobLogger imported successfully")
    except Exception as e:
        print(f"❌ Failed to import JobLogger: {e}")
        return False
    
    return True

def test_environment():
    """Test environment variables"""
    print("\n🔧 Testing environment variables...")
    
    required_vars = [
        'OPENAI_API_KEY',
        'OPENAI_API_BASE_URL',
        'VECTOR_STORE_ID',
        'OPTISIGNS_API_BASE_URL',
        'OUTPUT_DIRECTORY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"✅ {var} is set")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    return True

def test_main_job_import():
    """Test that the main job can be imported"""
    print("\n🚀 Testing main job import...")
    
    try:
        from main import OptiSignsSyncJob
        print("✅ OptiSignsSyncJob imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import OptiSignsSyncJob: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing OptiSigns Sync Job Setup")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed")
        return False
    
    # Test environment
    if not test_environment():
        print("\n❌ Environment tests failed")
        return False
    
    # Test main job import
    if not test_main_job_import():
        print("\n❌ Main job import failed")
        return False
    
    print("\n✅ All tests passed! The main job should be ready to run.")
    print("\nTo run the job:")
    print("   python main.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 