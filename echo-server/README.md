# Echo Server

A simple REST server that echoes whatever is sent to it via POST, along with a timestamp.

## Features

- 📡 **Echo Endpoint**: POST to `/echo` to get your data back with a timestamp
- 🏥 **Health Check**: GET `/health` for server status
- 🏠 **Home Page**: GET `/` for usage instructions
- ⏰ **Timestamps**: All responses include ISO format timestamps
- 🔧 **Content Type Support**: Handles JSON and plain text requests

## Quick Start

1. **Install dependencies:**
   ```bash
   cd echo-server
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   python server.py
   ```

3. **Server will start on http://localhost:5000**

## Usage Examples

### JSON Data
```bash
curl -X POST http://localhost:5000/echo \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello World!", "user": "john"}'
```

**Response:**
```json
{
  "echo": {
    "message": "Hello World!",
    "user": "john"
  },
  "timestamp": "2024-06-16T19:45:32.123456",
  "content_type": "application/json",
  "method": "POST"
}
```

### Plain Text
```bash
curl -X POST http://localhost:5000/echo \
  -H "Content-Type: text/plain" \
  -d "This is a test message"
```

**Response:**
```json
{
  "echo": "This is a test message",
  "timestamp": "2024-06-16T19:45:32.123456",
  "content_type": "text/plain",
  "method": "POST"
}
```

### Health Check
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-06-16T19:45:32.123456"
}
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/echo`  | Echo back the request data with timestamp |
| GET    | `/health`| Health check endpoint |
| GET    | `/`      | Home page with usage instructions |

## Development

The server runs in debug mode by default, so it will automatically reload when you make changes to the code.

## Requirements

- Python 3.6+
- Flask 2.3.3+

