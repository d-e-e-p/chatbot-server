# chatbot-server

[![GitHub license](https://img.shields.io/badge/license-Apache%202.0-blue)](./LICENSE)
[![Python Version](https://img.shields.io/badge/python-v3.12-blue)](https://www.python.org/)
[![FastAPI Version](https://img.shields.io/badge/fastAPI-v0.124.0-blue)](https://pypi.org/project/fastapi/)


A WebSocket-based chatbot orchestration server for [Soul Machines](https://soulmachines.com) avatars, handling conversation flow and speech coordination.

## Features

- Real-time WebSocket communication
- Message validation using Pydantic models
- Conversation logging in structured formats
- Error handling for invalid messages/JSON
- Session recording and replay capabilities
- Automated testing with session recordings

## Installation

### Using UV (recommended)
```bash
uv venv
uv pip install -e .
```

## Usage

### Running the Server
```bash
chatbot-server
```
Server runs on `0.0.0.0:5001` by default

### Key Operations
- Handles `recognizeResults`/`conversationRequest` messages
- Sends `startSpeaking`/`conversationResponse` commands
- Maintains conversation state
- Records sessions in `trace/` (full logs) and `rpt/` (spoken dialog)

### Example Request/Response
```json
// Client request
{"type": "recognizeResults", "text": "Hello", "sessionId": "123"}

// Server response
{"type": "startSpeaking", "text": "Hello there!", "sessionId": "123"}
```

## API Documentation
Interactive API docs available at `/docs` when server is running:
- Swagger UI: http://localhost:5001/docs
- Redoc: http://localhost:5001/redoc

## Testing

### Running Tests
```bash
pytest
```
Tests verify server behavior using recorded sessions from `trace/`

### Test Features
- WebSocket connection handling
- Message validation
- Response generation
- Session recording verification


## Project Structure
```
chatbot-server/
├── src/                    # Core application code
│   ├── api/                # WebSocket handlers
│   ├── utils/              # Utilities and helpers
│   └── app.py              # Main application entrypoint
├── test/                   # Test cases
├── trace/                  # Full session recordings
├── rpt/                    # Simplified conversation logs
└── pyproject.toml          # Project configuration
```

## Contributing
1. Fork the repository
2. Create feature branch (`git checkout -b feature/your-feature`)
3. Commit changes following existing style
4. Push to branch (`git push origin feature/your-feature`)
5. Open Pull Request

### Code Style
- Follow PEP8 guidelines
- Use Black formatting
- Type hints encouraged
- 100 character line length

## License
Apache 2.0 - See [LICENSE](./LICENSE) for details

