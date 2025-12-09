#!/bin/bash
# Run VCF Credentials Manager with Gunicorn and HTTPS

# Create logs directory if it doesn't exist
mkdir -p logs
mkdir -p ssl

# Check if SSL certificates exist
if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
    echo "SSL certificates not found. Generating self-signed certificate..."
    echo ""
    
    # Generate self-signed certificate
    openssl req -x509 -newkey rsa:4096 -nodes \
        -out ssl/cert.pem \
        -keyout ssl/key.pem \
        -days 365 \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    
    echo ""
    echo "✅ Self-signed certificate generated"
    echo "   Certificate: ssl/cert.pem"
    echo "   Key: ssl/key.pem"
    echo ""
    echo "⚠️  WARNING: Self-signed certificate - browsers will show security warning"
    echo "   For production, use a proper SSL certificate (Let's Encrypt, etc.)"
    echo ""
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting VCF Credentials Manager with Gunicorn (HTTPS)..."
echo "Access at: https://localhost:5000"
echo "Logs: logs/gunicorn_*.log"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run Gunicorn with SSL
gunicorn \
    --certfile=ssl/cert.pem \
    --keyfile=ssl/key.pem \
    --bind 0.0.0.0:5000 \
    --workers 1 \
    --timeout 30 \
    --access-logfile logs/gunicorn_access.log \
    --error-logfile logs/gunicorn_error.log \
    --log-level info \
    app:app

