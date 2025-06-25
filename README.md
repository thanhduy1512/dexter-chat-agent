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

## Deploying to a DigitalOcean Droplet (Short Guide)

1. **Upload or git clone your project to the droplet**
2. **Build the Docker image:**

   ```bash
   docker build -t help-center-sync:latest .
   ```

3. **Create deployment directory and copy files:**

   ```bash
   mkdir -p /opt/help-center-sync
   cp -r * /opt/help-center-sync/
   cd /opt/help-center-sync
   ```

4. **Set up your `.env` file** (see `env.example` for required variables)
5. **Create the run script:**

   ```bash
   cat > run-sync.sh << 'EOF'
   #!/bin/bash
   cd /opt/help-center-sync
   docker run --rm \
       --env-file .env \
       -v "$(pwd)/logs:/app/logs" \
       -v "$(pwd)/articles:/app/articles" \
       -v "$(pwd)/upload_tracking.json:/app/upload_tracking.json" \
       help-center-sync:latest python main.py
   EOF
   chmod +x run-sync.sh
   ```

6. **(Optional) Set up the log viewer:**
   - Copy `log_viewer.py` to `/opt/help-center-sync/`
   - Install Flask: `apt install python3-flask -y`
   - Run: `python3 log_viewer.py` or set up as a service
7. **Set up a cron job (example: run daily at 9 PM UTC):**

   ```bash
   crontab -e
   # Add this line:
   0 21 * * * /opt/help-center-sync/run-sync.sh >> /opt/help-center-sync/logs/cron.log 2>&1
   ```

**That's it!**

_This does not affect the local/Docker usage instructions above._
