#!/usr/bin/env python3
"""
Debug script to test filename comparison logic
"""

import os
from dotenv import load_dotenv
from src.openai.vector_store_manager import VectorStoreManager
from src.openai.file_manager import OpenAIFileManager

# Load environment variables
load_dotenv()

def debug_filename_issue():
    """Debug the filename comparison issue"""
    print("🔍 Debugging filename comparison issue...")
    
    vector_store_id = os.getenv('VECTOR_STORE_ID')
    if not vector_store_id:
        print("❌ VECTOR_STORE_ID not found")
        return
    
    vector_manager = VectorStoreManager()
    file_manager = OpenAIFileManager()
    
    print(f"🔍 Vector Store ID: {vector_store_id}")
    
    # Check vector store files directly
    print("\n📁 Checking vector store files...")
    vector_files = vector_manager.list_all_files(vector_store_id)
    print(f"   Vector store has {len(vector_files)} files")
    
    if vector_files:
        print("   First few vector store files:")
        for file in vector_files[:3]:
            print(f"     Vector ID: {file.get('id')}, OpenAI ID: {file.get('file_id')}")
    else:
        print("   ❌ No files found in vector store!")
    
    # Check OpenAI files
    print("\n📄 Checking OpenAI files...")
    openai_files = file_manager.list_all_files()
    print(f"   OpenAI has {len(openai_files)} files")
    
    if openai_files:
        print("   First few OpenAI files:")
        for file in openai_files[:3]:
            print(f"     OpenAI ID: {file.get('id')}, Filename: {file.get('filename')}")
    else:
        print("   ❌ No files found in OpenAI!")
    
    # Test file index creation
    print("\n📝 Testing file index creation...")
    try:
        file_index = vector_manager.create_file_index(vector_store_id)
        print(f"   File index created with {len(file_index)} entries")
        
        if file_index:
            print("   First few index keys:")
            for key in list(file_index.keys())[:3]:
                print(f"     {key}")
        else:
            print("   ❌ File index is empty!")
            
    except Exception as e:
        print(f"   ❌ Error creating file index: {e}")
    
    # Test specific file lookup
    print("\n🔍 Testing specific file lookup...")
    test_filename = "28421615261971.md"
    txt_filename = test_filename.replace('.md', '.txt')
    
    print(f"   Looking for: {txt_filename}")
    
    # Check if it exists in OpenAI
    found_in_openai = False
    for file in openai_files:
        if file.get('filename') == txt_filename:
            found_in_openai = True
            print(f"   ✅ Found in OpenAI: {file.get('filename')} (ID: {file.get('id')})")
            break
    
    if not found_in_openai:
        print(f"   ❌ Not found in OpenAI files")
    
    # Check if it exists in vector store
    found_in_vector = False
    for file in vector_files:
        openai_file_id = file.get('file_id')
        if openai_file_id:
            file_info = file_manager.get_by_id(openai_file_id)
            if file_info and file_info.get('filename') == txt_filename:
                found_in_vector = True
                print(f"   ✅ Found in vector store: {file_info.get('filename')} (Vector ID: {file.get('id')}, OpenAI ID: {openai_file_id})")
                break
    
    if not found_in_vector:
        print(f"   ❌ Not found in vector store")

if __name__ == "__main__":
    debug_filename_issue() 