#!/bin/bash
# Simple script to run the VCF Credentials Manager

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if requirements are installed
python -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Run the application
echo "Starting VCF Credentials Manager..."
echo "Access the application at: http://localhost:5000"
echo "Default credentials: admin / admin"
echo ""
python app.py

