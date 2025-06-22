# Help Center Sync Job

A comprehensive job system that scrapes help center articles, detects changes, and syncs them to OpenAI vector stores with intelligent delta detection.

## 🚀 Features

- **Smart Scraping**: Scrapes all articles from help center
- **Delta Detection**: Only uploads new or updated articles using content hashing
- **OpenAI Integration**: Uploads articles to OpenAI files and vector stores
- **Comprehensive Logging**: Detailed job logs with summaries and history
- **Error Handling**: Robust error handling and recovery
- **Modular Architecture**: Clean, maintainable code structure

## 📁 Project Structure

```
dexter-chat-agent/
├── main.py                          # Main job orchestrator
├── test_main_job.py                 # Test script for setup verification
├── src/                             # Source code modules
│   ├── scrapers/                    # Scraping functionality
│   │   ├── __init__.py
│   │   └── optisigns_scraper.py     # help center scraper
│   ├── openai/                      # OpenAI integration
│   │   ├── __init__.py
│   │   ├── file_manager.py          # OpenAI file operations
│   │   └── vector_store_manager.py  # Vector store operations
│   └── utils/                       # Utility modules
│       ├── __init__.py
│       ├── file_tracker.py          # File tracking and hashing
│       ├── file_converter.py        # File format conversion
│       └── job_logger.py            # Job logging and summaries
├── articles/                        # Local article storage
├── logs/                           # Job logs and summaries
├── upload_tracking.json            # File upload tracking
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables
└── README.md                      # This file
```

## 🛠️ Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd dexter-chat-agent
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE_URL=https://api.openai.com/v1
VECTOR_STORE_ID=your_vector_store_id

# Configuration
OPTISIGNS_API_BASE_URL=https://support.optisigns.com/api/v2/help_center/en-us/articles
ARTICLES_PER_PAGE=30

# Local Configuration
OUTPUT_DIRECTORY=articles
```

## 🚀 Usage

### Run the Main Sync Job

The main job performs the complete sync workflow:

```bash
python main.py
```

**Job Flow:**

1. **Scrape** data from help center
2. **Check** existence in local `/articles` directory
3. **Compare** content (hash, last-modified)
4. **Check** existence in OpenAI files and vector store
5. **Upload** only delta (new/updated articles)
6. **Log** final results with counts and links

### Test Setup

Before running the main job, test your setup:

```bash
python test_main_job.py
```

This will verify:

- All modules can be imported
- Environment variables are set correctly
- Main job can be initialized

### View Job Results

Check job logs and summaries:

```bash
# View latest job summary
cat logs/latest_job_summary.json

# View recent job logs
ls -la logs/
```

## 📊 Job Output

The job provides comprehensive logging and reporting:

### Console Output

```
🚀 Starting Help Center Sync Job
📡 Step 1: Scraping help center...
📁 Step 2: Checking local articles directory...
🔍 Step 3: Comparing scraped vs local articles...
☁️  Step 4: Checking OpenAI and vector store...
📤 Step 5: Uploading delta to OpenAI and vector store...
📊 Step 6: Logging final results...
✅ Help Center Sync Job completed successfully!

📊 Job Summary:
   ⏱️  Duration: 45.23 seconds
   📤 Uploaded: 5
   ✅ Skipped: 120
   ❌ Failed: 0
   📄 Log file: logs/sync_job_20241222_143022.log
```

### Job Summary JSON

```json
{
  "job_start": "2024-12-22T14:30:22.123456",
  "job_end": "2024-12-22T14:31:07.345678",
  "duration_seconds": 45.22,
  "log_file": "logs/sync_job_20241222_143022.log",
  "results": {
    "uploaded": 5,
    "skipped": 120,
    "failed": 0
  },
  "uploaded_articles": ["12345", "67890"],
  "failed_articles": []
}
```

## 🔧 Development

### Project Architecture

The project follows a modular architecture:

- **`main.py`**: Main job orchestrator that coordinates all components
- **`src/scrapers/`**: Handles data extraction from OptiSigns
- **`src/openai/`**: Manages OpenAI API interactions
- **`src/utils/`**: Provides utility functions for file handling and logging

### Adding New Features

1. **New Scraper**: Add to `src/scrapers/`
2. **New OpenAI Integration**: Add to `src/openai/`
3. **New Utilities**: Add to `src/utils/`
4. **Update Main Job**: Modify `main.py` to use new components

### Testing

```bash
# Test imports and setup
python test_main_job.py

# Run with verbose logging
python main.py
```

## 📝 Logging

The job creates detailed logs in the `logs/` directory:

- **`sync_job_YYYYMMDD_HHMMSS.log`**: Detailed job execution log
- **`job_summary_YYYYMMDD_HHMMSS.json`**: Job summary with metrics
- **`latest_job_summary.json`**: Latest job summary for quick access

## 🔍 Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   - Run `python test_main_job.py` to check configuration
   - Ensure all required variables are set in `.env`

2. **Import Errors**
   - Verify Python path includes `src/`
   - Check that all `__init__.py` files exist

3. **API Errors**
   - Verify OpenAI API key and base URL
   - Check vector store ID exists
   - Ensure API is accessible

### Debug Mode

For detailed debugging, modify logging level in `main.py`:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## 📈 Performance

The job is optimized for efficiency:

- **Delta Detection**: Only processes changed content
- **Batch Operations**: Handles multiple files efficiently
- **Error Recovery**: Continues processing on individual failures
- **Memory Efficient**: Processes articles one at a time

## 🤝 Contributing

1. Follow the existing code structure
2. Add appropriate logging
3. Update tests as needed
4. Document new features

## 📄 License

[Add your license information here]
