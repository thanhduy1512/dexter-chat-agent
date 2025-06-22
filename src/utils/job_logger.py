#!/usr/bin/env python3
"""
Job Logger
Handles job summaries and logging functionality.
"""

import os
import json
from datetime import datetime
from pathlib import Path

class JobLogger:
    """Handles job logging and summary management"""
    
    def __init__(self, logs_dir="logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
    
    def save_job_summary(self, summary):
        """Save job summary to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = self.logs_dir / f"job_summary_{timestamp}.json"
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Also save latest summary
        latest_file = self.logs_dir / "latest_job_summary.json"
        with open(latest_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return str(summary_file)
    
    def get_latest_summary(self):
        """Get the latest job summary"""
        latest_file = self.logs_dir / "latest_job_summary.json"
        if latest_file.exists():
            with open(latest_file, 'r') as f:
                return json.load(f)
        return None
    
    def get_job_history(self, limit=10):
        """Get recent job summaries"""
        summaries = []
        for summary_file in sorted(self.logs_dir.glob("job_summary_*.json"), reverse=True):
            if len(summaries) >= limit:
                break
            try:
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
                    summary['file'] = str(summary_file)
                    summaries.append(summary)
            except:
                continue
        return summaries 