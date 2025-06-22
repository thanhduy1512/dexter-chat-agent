#!/usr/bin/env python3
"""
File Converter
Handles conversion of markdown files to text format for OpenAI upload.
"""

import os
import tempfile
import shutil
from pathlib import Path

class FileConverter:
    """Handles file conversion operations"""
    
    @staticmethod
    def convert_md_to_txt(md_file_path):
        """Convert a markdown file to a temporary .txt file for OpenAI upload"""
        article_id = Path(md_file_path).stem
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        temp_dir = tempfile.mkdtemp()
        temp_txt_path = os.path.join(temp_dir, f"{article_id}.txt")
        with open(temp_txt_path, 'w', encoding='utf-8') as out:
            out.write(content)
        return temp_txt_path, temp_dir
    
    @staticmethod
    def cleanup_temp_files(temp_dir):
        """Clean up temporary files"""
        shutil.rmtree(temp_dir) 