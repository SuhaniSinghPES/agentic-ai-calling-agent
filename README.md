# Agentic AI Calling Agent

An AI-powered conversational agent backend built with Python, Flask, REST APIs, LLM integration, session memory, knowledge retrieval, and webhook support.

## Architecture

Caller / Voice Interface
        |
        v
Speech-to-Text
        |
        v
Flask REST API
        |
        v
Conversation Agent
   |          |
   v          v
Session     Knowledge
Memory      Base
        |
        v
       LLM
        |
        v
Generated Response
        |
        v
Text-to-Speech / Voice Platform

## Features

- Conversational AI agent
- Flask REST API
- Session-based conversation memory
- Lightweight knowledge-base retrieval
- Prompt engineering
- Webhook endpoint
- Error handling
- Environment variable configuration
- Automated API tests
- Architecture ready for voice-platform integration

## API Endpoints

### GET /
Basic application status.

### GET /health
Health check.

### POST /chat

Example:
```json
{
  "session_id": "user123",
  "message": "What services do you provide?"
}
```

### POST /webhook
Receives events from an external calling/voice service.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your OpenAI API key to `.env`.

Run:
```bash
python app.py
```

Server:
`http://localhost:5000`

Test:
```bash
pytest
```

## GitHub Safety

Never commit `.env`. The real API keys must remain private.

## Future Improvements

- Persistent database-backed memory
- Vector database and embeddings for scalable RAG
- Production ElevenLabs integration
- Call analytics
- Authentication
- CRM integration
- Appointment scheduling
- Call summarization
