#!/usr/bin/env python3
"""
File Tracker
Handles tracking of uploaded files and their metadata.
"""

import os
import json
import hashlib
from datetime import datetime

class FileTracker:
    """Handles file tracking and hash generation"""
    
    def __init__(self, tracking_file="upload_tracking.json"):
        self.tracking_file = tracking_file
        self.file_tracking = self.load_file_tracking()
    
    def load_file_tracking(self):
        """Load file tracking data from JSON file"""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("Warning: Corrupted tracking file, starting fresh")
        return {}
    
    def save_file_tracking(self):
        """Save file tracking data to JSON file"""
        with open(self.tracking_file, 'w') as f:
            json.dump(self.file_tracking, f, indent=2)
    
    def clear_tracking(self):
        """Clear all tracking data and reset upload state"""
        self.file_tracking = {}
        self.save_file_tracking()
        print("✅ Upload tracking cleared")
    
    def get_file_hash(self, file_path):
        """Generate SHA-256 hash of file content"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def get_file_hash_from_content(self, content):
        """Generate SHA-256 hash from content string"""
        hash_sha256 = hashlib.sha256()
        hash_sha256.update(content.encode('utf-8'))
        return hash_sha256.hexdigest()
    
    def get_tracking_info(self, file_key):
        """Get tracking info for a file"""
        return self.file_tracking.get(file_key)
    
    def update_tracking(self, file_key, file_id, vector_store_file_id, file_hash=None, file_path=None):
        """Update tracking information for a file"""
        if file_hash is None and file_path:
            file_hash = self.get_file_hash(file_path)
        
        self.file_tracking[file_key] = {
            'file_id': file_id,
            'vector_store_file_id': vector_store_file_id,
            'hash': file_hash,
            'uploaded_at': datetime.now().isoformat(),
            'file_path': file_path
        }
        self.save_file_tracking()
    
    def update_vector_store_file_id(self, file_key, vector_store_file_id):
        """Update only the vector store file ID in tracking"""
        if file_key in self.file_tracking:
            self.file_tracking[file_key]['vector_store_file_id'] = vector_store_file_id
            self.save_file_tracking() 