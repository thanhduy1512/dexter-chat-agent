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
        """List all files in a vector store"""
        url = f"{self.base_url}/vector_stores/{vector_store_id}/files"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json().get('data', [])
            return []
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