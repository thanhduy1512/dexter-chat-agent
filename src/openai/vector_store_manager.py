#!/usr/bin/env python3
"""
OpenAI Vector Store Manager
Handles file operations within OpenAI vector stores.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VectorStoreManager:
    """Manages file operations within OpenAI vector stores"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.base_url = os.getenv('OPENAI_API_BASE_URL')
        if not self.base_url:
            raise ValueError("OPENAI_API_BASE_URL not found in environment variables")
            
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "assistants=v2"
        }
    
    def get_file_by_id(self, vector_store_id, file_id):
        """Get vector store file by ID"""
        url = f"{self.base_url}/vector_stores/{vector_store_id}/files/{file_id}"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                return None
        except requests.RequestException:
            return None
    
    def list_all_files(self, vector_store_id):
        """List all files in a vector store with pagination support"""
        url = f"{self.base_url}/vector_stores/{vector_store_id}/files"
        all_files = []
        
        try:
            params = {}
            while True:
                response = requests.get(url, headers=self.headers, params=params)
                if response.status_code != 200:
                    break
                    
                data = response.json()
                files = data.get('data', [])
                all_files.extend(files)
                
                # Check for next page - use the last object ID as 'after' parameter
                if data.get('has_more') and files:
                    params['after'] = files[-1]['id']
                else:
                    break
                    
            return all_files
        except requests.RequestException:
            return []
    
    def add_file(self, vector_store_id, openai_file_id):
        """Add a file to a vector store"""
        url = f"{self.base_url}/vector_stores/{vector_store_id}/files"
        
        data = {"file_id": openai_file_id}
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result['id']
    
    def remove_file(self, vector_store_id, file_id):
        """Remove a file from vector store"""
        url = f"{self.base_url}/vector_stores/{vector_store_id}/files/{file_id}"
        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False
    
    def find_file_by_filename(self, vector_store_id, filename):
        """Find a file in vector store by filename"""
        from src.openai.file_manager import OpenAIFileManager
        
        files = self.list_all_files(vector_store_id)
        txt_filename = filename.replace('.md', '.txt')
        
        for file in files:
            openai_file_id = file.get('file_id')
            if openai_file_id:
                file_manager = OpenAIFileManager()
                file_info = file_manager.get_by_id(openai_file_id)
                
                if file_info and file_info.get('filename') == txt_filename:
                    file_id = file.get('id')
                    if self.get_file_by_id(vector_store_id, file_id):
                        return True, file_id, openai_file_id
        
        return False, None, None
    
    def delete_all_files(self, vector_store_id):
        """Delete all files from a vector store"""
        files = self.list_all_files(vector_store_id)
        
        if not files:
            return True
        
        deleted_count = 0
        failed_count = 0
        
        for file in files:
            file_id = file.get('id')
            if self.remove_file(vector_store_id, file_id):
                deleted_count += 1
            else:
                failed_count += 1
        
        return failed_count == 0
    
    def create_file_index(self, vector_store_id):
        """Create a fast lookup index of all files in the vector store"""
        print("🔍 Creating file index for fast lookups...")
        
        files = self.list_all_files(vector_store_id)
        file_index = {}
        
        # Create lookup by filename
        for file in files:
            openai_file_id = file.get('file_id')
            if openai_file_id:
                # Get file info once and cache it
                from src.openai.file_manager import OpenAIFileManager
                file_manager = OpenAIFileManager()
                file_info = file_manager.get_by_id(openai_file_id)
                
                if file_info:
                    filename = file_info.get('filename', '')
                    file_index[filename] = {
                        'vector_store_file_id': file.get('id'),
                        'openai_file_id': openai_file_id,
                        'file_info': file_info
                    }
                    print(f"📝 Indexed: {filename} -> {file.get('id')}")
        
        print(f"✅ File index created with {len(file_index)} files")
        print(f"🔍 Index keys: {list(file_index.keys())[:5]}...")  # Show first 5 keys
        return file_index
    
    def check_file_exists_fast(self, vector_store_id, filename, file_index=None):
        """Fast file existence check using pre-built index"""
        if file_index is None:
            file_index = self.create_file_index(vector_store_id)
        
        txt_filename = filename.replace('.md', '.txt')
        print(f"🔍 Looking for: {txt_filename} in index with {len(file_index)} files")
        print(f"🔍 Available keys: {list(file_index.keys())[:5]}...")  # Show first 5 available keys
        
        exists = txt_filename in file_index
        print(f"🔍 Found: {exists}")
        return exists, file_index.get(txt_filename, {})
    
    def replace_file(self, vector_store_id, old_file_id, new_openai_file_id):
        """Replace an existing file in the vector store with a new one"""
        try:
            # Remove the old file from vector store
            if old_file_id:
                self.remove_file(vector_store_id, old_file_id)
                print(f"🗑️ Removed old file {old_file_id} from vector store")
            
            # Add the new file to vector store
            new_vector_store_file_id = self.add_file(vector_store_id, new_openai_file_id)
            print(f"✅ Added new file {new_openai_file_id} to vector store")
            
            return new_vector_store_file_id
        except Exception as e:
            print(f"❌ Error replacing file: {e}")
            return None 