# Help Center Article Scraper

A Python script to scrape articles from a help center API and save them as clean markdown files.

## Features

- ✅ **Scrapes 30 articles** from the help center API
- ✅ **Preserves relative links** to other articles
- ✅ **Preserves code blocks** and formatting
- ✅ **Preserves headings** (h1, h2, h3, etc.)
- ✅ **Removes navigation/ads** and unwanted elements
- ✅ **Clean markdown output** with proper formatting
- ✅ **Metadata included** (Article ID, URLs, creation/update dates)
- ✅ **Modular design** with separate scraper class and main script

## File Structure

```
├── optisigns_scraper.py  # Main scraper class
├── main.py               # Entry point script
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── articles/            # Output directory (created automatically)
└── venv/               # Virtual environment (created during setup)
```

## Installation

1. **Clone or download** this repository
2. **Create a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Activate the virtual environment:**

   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Run the scraper:**

   ```bash
   python main.py
   ```

3. **Check the results:**
   - Articles will be saved in the `articles/` directory
   - Each file is named `[article_id].md`
   - Example: `31960461758611.md`

## Using the Scraper Class

You can also use the `OptiSignsScraper` class directly in your own scripts:

```python
from optisigns_scraper import OptiSignsScraper

# Create scraper instance
scraper = OptiSignsScraper()

# Scrape 50 articles
articles_scraped = scraper.scrape_articles(count=50)

# Customize output directory
scraper.output_dir = "my_articles"
scraper.scrape_articles(count=10)
```

## Output Format

Each markdown file contains:

```markdown
# Article Title

**Article ID:** 31960461758611  
**Original URL:** https://support.example.com/hc/en-us/articles/...  
**Created:** 2024-08-02T15:58:54Z  
**Updated:** 2025-02-17T20:31:14Z

---

[Article content converted to clean markdown]

---
*Scraped from Help Center*
```

## Features Implemented

### HTML to Markdown Conversion

- Uses `html2text` library for clean conversion
- Preserves formatting, links, and structure
- Removes excessive whitespace and newlines

### Link Preservation

- **Relative links** to other articles are preserved
- **Absolute URLs** to the help center are converted to relative links
- **External links** are maintained as-is

### Content Cleaning

- Removes navigation elements, ads, and unwanted content
- Preserves code blocks and technical content
- Maintains heading hierarchy
- Keeps images and their alt text

### File Management

- Creates `articles/` directory automatically
- Uses article ID for filename (e.g., `31960461758611.md`)
- Handles UTF-8 encoding properly
- Includes error handling for file operations

### Modular Design

- **`optisigns_scraper.py`** - Contains the scraper class
- **`main.py`** - Entry point script with error handling
- Easy to import and use in other projects
- Clean separation of concerns

## Dependencies

- `requests` - HTTP requests to the API
- `beautifulsoup4` - HTML parsing and cleaning
- `html2text` - HTML to markdown conversion
- `lxml` - Fast XML/HTML parser

## API Endpoint

The scraper uses the help center API:

```
https://support.example.com/api/v2/help_center/en-us/articles?page=1&per_page=30
```

## Customization

You can modify the scraper to:

- Change the number of articles to scrape (edit `count=30` in main.py)
- Adjust HTML cleaning rules (modify `unwanted_selectors` list in the scraper class)
- Change output directory (modify `output_dir` in the class)
- Add more metadata fields
- Import and use the scraper class in your own projects

## Example Output

The scraper successfully scraped 30 articles with clean markdown formatting, preserved links, and removed unwanted navigation elements while maintaining the original content structure.

## License

This script is provided as-is for educational and personal use. Please respect the help center's terms of service when using this scraper.
