#!/usr/bin/env python3
"""
Simple REST Echo Server
Echoes back whatever is sent via POST with a timestamp
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

@app.route('/echo', methods=['POST'])
def echo():
    """
    Echo endpoint that returns the received data with a timestamp
    """
    try:
        # Get the current timestamp
        timestamp = datetime.now().isoformat()
        
        # Get the request data
        if request.is_json:
            data = request.get_json()
        else:
            # Handle text/plain or other content types
            data = request.get_data(as_text=True)
        
        # Create response
        response = {
            "echo": data,
            "timestamp": timestamp,
            "content_type": request.content_type,
            "method": request.method
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with usage instructions"""
    return jsonify({
        "message": "Echo Server is running!",
        "usage": "Send POST requests to /echo to get your data echoed back with a timestamp",
        "health_check": "GET /health",
        "timestamp": datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    print("🚀 Starting Echo Server...")
    print("📡 Send POST requests to http://localhost:5000/echo")
    print("🏥 Health check available at http://localhost:5000/health")
    print("🏠 Home page at http://localhost:5000/")
    app.run(host='0.0.0.0', port=5000, debug=True)

