#!/bin/bash
# Run VCF Credentials Manager with Gunicorn

# Create logs directory if it doesn't exist
mkdir -p logs

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting VCF Credentials Manager with Gunicorn..."
echo "Access at: http://localhost:5000"
echo "Logs: logs/gunicorn_*.log"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run Gunicorn with configuration file
gunicorn --config gunicorn_config.py app:app

