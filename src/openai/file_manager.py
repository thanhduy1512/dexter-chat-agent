#!/usr/bin/env python3
"""
OpenAI File Manager
Handles file operations with OpenAI API including upload, retrieval, and deletion.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenAIFileManager:
    """Manages file operations with OpenAI API"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.base_url = os.getenv('OPENAI_API_BASE_URL')
        if not self.base_url:
            raise ValueError("OPENAI_API_BASE_URL not found in environment variables")
            
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
    
    def get_by_id(self, file_id):
        """Get file by ID"""
        url = f"{self.base_url}/files/{file_id}"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.RequestException:
            return None
    
    def list_all_files(self):
        """List all files in OpenAI"""
        url = f"{self.base_url}/files"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json().get('data', [])
            return []
        except requests.RequestException:
            return []
    
    def upload_file(self, file_path, purpose="assistants"):
        """Upload a file to OpenAI"""
        url = f"{self.base_url}/files"
        
        with open(file_path, 'rb') as file:
            files = {'file': file, 'purpose': (None, purpose)}
            response = requests.post(url, headers=self.headers, files=files)
            response.raise_for_status()
            
            result = response.json()
            return result['id']
    
    def upload_markdown_file(self, md_file_path):
        """Convert markdown to text and upload to OpenAI"""
        from src.utils.file_converter import FileConverter
        
        converter = FileConverter()
        temp_txt_path, temp_dir = converter.convert_md_to_txt(md_file_path)
        
        try:
            file_id = self.upload_file(temp_txt_path, purpose="assistants")
            return file_id
        finally:
            converter.cleanup_temp_files(temp_dir)
    
    def delete(self, file_id):
        """Delete a file from OpenAI"""
        url = f"{self.base_url}/files/{file_id}"
        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False
    
    def replace_file(self, old_file_id, new_file_path, purpose="assistants"):
        """Replace an existing file with a new one"""
        try:
            # Delete the old file
            if old_file_id:
                self.delete(old_file_id)
                print(f"🗑️ Deleted old OpenAI file {old_file_id}")
            
            # Upload the new file
            new_file_id = self.upload_file(new_file_path, purpose)
            print(f"✅ Uploaded new file {new_file_id}")
            
            return new_file_id
        except Exception as e:
            print(f"❌ Error replacing file: {e}")
            return None 