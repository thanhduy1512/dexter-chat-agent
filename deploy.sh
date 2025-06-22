#!/bin/bash

# DigitalOcean Deployment Script for Help Center Sync Job
# This script deploys the scraper as a daily job

set -e

echo "🚀 Deploying Help Center Sync Job to DigitalOcean..."

# Build Docker image
echo "📦 Building Docker image..."
docker build -t help-center-sync:latest .

# Create a simple cron job script
cat > cron-job.sh << 'EOF'
#!/bin/bash
# Daily sync job script
cd /app
python main.py
EOF

chmod +x cron-job.sh

# Create docker-compose for easy deployment
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  help-center-sync:
    image: help-center-sync:latest
    container_name: help-center-sync
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - VECTOR_STORE_ID=${VECTOR_STORE_ID}
      - OPTISIGNS_API_BASE_URL=${OPTISIGNS_API_BASE_URL}
    volumes:
      - ./logs:/app/logs
      - ./articles:/app/articles
      - ./upload_tracking.json:/app/upload_tracking.json
    restart: unless-stopped

  cron:
    image: help-center-sync:latest
    container_name: help-center-sync-cron
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - VECTOR_STORE_ID=${VECTOR_STORE_ID}
      - OPTISIGNS_API_BASE_URL=${OPTISIGNS_API_BASE_URL}
    volumes:
      - ./logs:/app/logs
      - ./articles:/app/articles
      - ./upload_tracking.json:/app/upload_tracking.json
      - ./cron-job.sh:/app/cron-job.sh
    command: >
      sh -c "
        echo '0 2 * * * /app/cron-job.sh >> /app/logs/cron.log 2>&1' > /etc/cron.d/sync-job &&
        chmod 0644 /etc/cron.d/sync-job &&
        crontab /etc/cron.d/sync-job &&
        cron -f
      "
    restart: unless-stopped
EOF

echo "✅ Deployment files created!"
echo ""
echo "📋 Next steps:"
echo "1. Upload these files to your DigitalOcean droplet:"
echo "   - Dockerfile"
echo "   - docker-compose.yml"
echo "   - cron-job.sh"
echo "   - All source code files"
echo ""
echo "2. Set environment variables on the droplet:"
echo "   export OPENAI_API_KEY='your_key'"
echo "   export VECTOR_STORE_ID='your_vector_store_id'"
echo "   export OPTISIGNS_API_BASE_URL='your_api_url'"
echo ""
echo "3. Run the deployment:"
echo "   docker-compose up -d"
echo ""
echo "4. Check logs:"
echo "   docker-compose logs -f help-center-sync"
echo ""
echo "📊 Job will run daily at 2:00 AM UTC"
echo "📁 Logs available at: ./logs/" 