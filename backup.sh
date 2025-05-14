#!/bin/bash

# Automatic Git backup script for Task Manager project
# This script will commit and push all changes to GitHub
# Run this script daily using a cron job or Windows Task Scheduler

# Set log file path
LOG_FILE="$(dirname "$0")/backup_log.md"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo "$1"
}

# Navigate to the project directory
cd "$(dirname "$0")" || {
    log_message "ERROR: Failed to change to script directory"
    exit 1
}

# Create log file if it doesn't exist
if [ ! -f "$LOG_FILE" ]; then
    echo "# Task Manager Backup Log" > "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    echo "| Timestamp | Action | Status | Details |" >> "$LOG_FILE"
    echo "|-----------|--------|--------|---------|" >> "$LOG_FILE"
fi

# Get current date for commit message
DATE=$(date +"%Y-%m-%d %H:%M:%S")
log_message "Starting backup process at $DATE"

# Check if we have any changes to commit
if git status --porcelain | grep -q '^'; then
    # Add all changes
    git add .
    
    # Commit with the current date as message
    if git commit -m "Automatic backup - $DATE"; then
        log_message "| $DATE | Commit | ✅ Success | Changes committed |" 
    else
        log_message "| $DATE | Commit | ❌ Failed | Git commit failed |"
    fi
    
    # Push changes to GitHub
    if git push origin task-manager-component; then
        log_message "| $DATE | Push | ✅ Success | Changes pushed to GitHub |"
    else
        log_message "| $DATE | Push | ❌ Failed | Git push failed |"
    fi
else
    log_message "| $DATE | Check | ℹ️ Info | No changes to commit |"
fi

echo "Backup completed at $DATE - Check $LOG_FILE for details"
