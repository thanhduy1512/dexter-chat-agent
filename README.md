# Help Center Sync Job

Scrapes help center articles and syncs them to OpenAI vector stores with intelligent delta detection.

## Quick Start

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**

   ```bash
   cp env.example .env
   # Edit .env with your OpenAI API key and vector store ID
   ```

   See [Environment Variables](#environment-variables) below for details.

3. **Run the sync job**

   ```bash
   python main.py
   ```

## What it does

- Scrapes all articles from help center
- Detects new/updated articles using content hashing
- Uploads only changes to OpenAI files and vector store
- Provides detailed logging and job summaries

## Environment Variables

Required variables in `.env`:

- `OPENAI_API_KEY`: Your OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- `VECTOR_STORE_ID`: Your OpenAI vector store ID ([Create one here](https://platform.openai.com/docs/assistants/tools/knowledge-retrieval))
- `OPTISIGNS_API_BASE_URL`: Help center API endpoint

## Test Setup

```bash
python test_main_job.py
```

## Verification

![Successful Test Screenshot](assets/youtube_test.jp2)

The assistant correctly answered: "How do I add a YouTube video?" with detailed instructions.
