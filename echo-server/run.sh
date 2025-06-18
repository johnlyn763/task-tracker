#!/bin/bash

echo "🚀 Starting Echo Server..."
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "🌟 Starting server on http://localhost:5000"
echo "📡 Echo endpoint: POST /echo"
echo "🏥 Health check: GET /health"
echo "🏠 Home page: GET /"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python server.py

