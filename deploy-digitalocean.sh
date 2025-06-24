#!/bin/bash

# Simple DigitalOcean Deployment Script
# Deploys the help center sync job as a daily cron job

set -e

echo "🚀 Deploying Help Center Sync Job to DigitalOcean..."

# Build Docker image
echo "📦 Building Docker image..."
docker build -t help-center-sync:latest .

# Create deployment directory
mkdir -p /opt/help-center-sync
cd /opt/help-center-sync

# Copy necessary files
cp -r ./* .

# Create environment file
cat > .env << 'EOF'
# OptiSigns API Configuration
OPTISIGNS_API_BASE_URL=https://support.optisigns.com/api/v2/help_center/en-us/articles
ARTICLES_PER_PAGE=30
OUTPUT_DIRECTORY=articles

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE_URL=https://api.openai.com/v1
VECTOR_STORE_ID=your_vector_store_id_here
EOF

# Create cron job script
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

# Add cron job (runs daily at 2:00 AM)
echo "0 2 * * * /opt/help-center-sync/run-sync.sh >> /opt/help-center-sync/logs/cron.log 2>&1" | crontab -

echo "✅ Deployment completed!"
echo ""
echo "📋 Setup instructions:"
echo "1. Edit /opt/help-center-sync/.env with your actual API keys"
echo "2. The job will run daily at 2:00 AM UTC"
echo "3. Check logs at: /opt/help-center-sync/logs/"
echo ""
echo "🔧 Manual run:"
echo "   cd /opt/help-center-sync && ./run-sync.sh"
echo ""
echo "📊 View cron logs:"
echo "   tail -f /opt/help-center-sync/logs/cron.log" 