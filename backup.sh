#!/bin/bash

# Automatic Git backup script
# Run this script daily using a cron job or Windows Task Scheduler

# Navigate to the project directory
cd "$(dirname "$0")"

# Get current date for commit message
DATE=$(date +"%Y-%m-%d %H:%M:%S")

# Add all changes
git add .

# Commit with the current date as message
git commit -m "Automatic backup - $DATE"

# Push changes to GitHub
git push origin task-manager-component

echo "Backup completed at $DATE"
