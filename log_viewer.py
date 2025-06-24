#!/usr/bin/env python3
"""
Simple Log Viewer for Help Center Sync Job
Provides web interface to view logs and statistics
"""

from flask import Flask, render_template_string, jsonify
import os
import glob
import json
from datetime import datetime
import re

app = Flask(__name__)

# Configuration
LOG_DIR = '/opt/help-center-sync/logs'
CRON_LOG = os.path.join(LOG_DIR, 'cron.log')

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Help Center Sync Job - Logs</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: #2c3e50; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: #ecf0f1; padding: 15px; border-radius: 5px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #2c3e50; }
        .stat-label { color: #7f8c8d; margin-top: 5px; }
        .log-section { margin-bottom: 30px; }
        .log-title { background: #34495e; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
        .log-content { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; font-family: 'Courier New', monospace; font-size: 12px; max-height: 400px; overflow-y: auto; white-space: pre-wrap; }
        .refresh-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-bottom: 20px; }
        .refresh-btn:hover { background: #2980b9; }
        .auto-refresh { margin-left: 10px; }
        .success { color: #27ae60; }
        .warning { color: #f39c12; }
        .error { color: #e74c3c; }
        .info { color: #3498db; }
    </style>
    <script>
        function refreshLogs() {
            fetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('cron-log').textContent = data.cron_log;
                    document.getElementById('latest-job-log').textContent = data.latest_job_log;
                    document.getElementById('stats').innerHTML = data.stats_html;
                });
        }
        
        function toggleAutoRefresh() {
            const checkbox = document.getElementById('auto-refresh');
            if (checkbox.checked) {
                setInterval(refreshLogs, 10000); // Refresh every 10 seconds
            }
        }
        
        // Initial load
        document.addEventListener('DOMContentLoaded', function() {
            refreshLogs();
        });
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Help Center Sync Job - Logs</h1>
            <p>Real-time monitoring of article sync process</p>
        </div>
        
        <button class="refresh-btn" onclick="refreshLogs()">🔄 Refresh Logs</button>
        <label class="auto-refresh">
            <input type="checkbox" id="auto-refresh" onchange="toggleAutoRefresh()"> Auto-refresh every 10 seconds
        </label>
        
        <div id="stats">
            <!-- Stats will be loaded here -->
        </div>
        
        <div class="log-section">
            <div class="log-title">📊 Latest Job Statistics</div>
            <div id="latest-job-log" class="log-content">
                Loading...
            </div>
        </div>
        
        <div class="log-section">
            <div class="log-title">📝 Cron Job Logs (Last 50 lines)</div>
            <div id="cron-log" class="log-content">
                Loading...
            </div>
        </div>
    </div>
</body>
</html>
"""

def get_latest_job_log():
    """Get the latest job log file"""
    pattern = os.path.join(LOG_DIR, 'sync_job_*.log')
    log_files = glob.glob(pattern)
    if not log_files:
        return "No job logs found"
    
    latest_log = max(log_files, key=os.path.getctime)
    try:
        with open(latest_log, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading log: {e}"

def get_cron_log():
    """Get the cron log"""
    try:
        with open(CRON_LOG, 'r') as f:
            lines = f.readlines()
            return ''.join(lines[-50:])  # Last 50 lines
    except Exception as e:
        return f"Error reading cron log: {e}"

def extract_stats(log_content):
    """Extract statistics from log content"""
    stats = {
        'uploaded': 0,
        'updated': 0,
        'skipped': 0,
        'failed': 0,
        'total_articles': 0,
        'last_run': 'Never'
    }
    
    # Extract numbers from log
    uploaded_match = re.search(r'(\d+) uploaded', log_content)
    if uploaded_match:
        stats['uploaded'] = int(uploaded_match.group(1))
    
    updated_match = re.search(r'(\d+) updated', log_content)
    if updated_match:
        stats['updated'] = int(updated_match.group(1))
    
    skipped_match = re.search(r'(\d+) skipped', log_content)
    if skipped_match:
        stats['skipped'] = int(skipped_match.group(1))
    
    failed_match = re.search(r'(\d+) failed', log_content)
    if failed_match:
        stats['failed'] = int(failed_match.group(1))
    
    total_match = re.search(r'Scraped (\d+) articles', log_content)
    if total_match:
        stats['total_articles'] = int(total_match.group(1))
    
    # Get last run time
    time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', log_content)
    if time_match:
        stats['last_run'] = time_match.group(1)
    
    return stats

def generate_stats_html(stats):
    """Generate HTML for statistics"""
    return f"""
    <div class="stats">
        <div class="stat-card">
            <div class="stat-number success">{stats['uploaded']}</div>
            <div class="stat-label">Uploaded</div>
        </div>
        <div class="stat-card">
            <div class="stat-number info">{stats['updated']}</div>
            <div class="stat-label">Updated</div>
        </div>
        <div class="stat-card">
            <div class="stat-number warning">{stats['skipped']}</div>
            <div class="stat-label">Skipped</div>
        </div>
        <div class="stat-card">
            <div class="stat-number error">{stats['failed']}</div>
            <div class="stat-label">Failed</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{stats['total_articles']}</div>
            <div class="stat-label">Total Articles</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{stats['last_run']}</div>
            <div class="stat-label">Last Run</div>
        </div>
    </div>
    """

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/logs')
def api_logs():
    cron_log = get_cron_log()
    latest_job_log = get_latest_job_log()
    stats = extract_stats(latest_job_log)
    stats_html = generate_stats_html(stats)
    
    return jsonify({
        'cron_log': cron_log,
        'latest_job_log': latest_job_log,
        'stats_html': stats_html
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False) 