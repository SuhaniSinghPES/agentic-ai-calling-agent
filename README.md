# Agentic AI Calling Agent

An AI-powered voice customer support and consultation booking system built using Python, Flask, Twilio Voice, OpenRouter, ElevenLabs, and SQLite.

The system accepts spoken customer queries, processes them through an AI agent and company knowledge base, maintains conversation sessions, and provides voice responses. It also supports consultation booking through tool calling and stores appointment data in SQLite.

## Features

- AI-powered conversational voice agent
- Twilio Voice integration for phone calls
- Speech-based customer input using Twilio `<Gather>`
- OpenRouter-powered LLM agent
- Session-based conversation management
- Knowledge-base retrieval using TF-IDF
- Function/tool calling
- Consultation appointment booking
- SQLite persistence for appointments
- ElevenLabs Text-to-Speech integration
- ElevenLabs Speech-to-Text webhook integration
- Webhook signature verification using HMAC
- Flask REST API
- Public HTTPS webhook testing through Cloudflare Tunnel

## System Architecture

```text
                    Customer
                       |
                       | Phone Call
                       v
                 Twilio Voice
                       |
                       | Speech Recognition
                       v
              Flask /voice/process
                       |
             +---------+---------+
             |                   |
             v                   v
       Fast FAQ Paths        AI Agent
                                 |
                    +------------+------------+
                    |            |            |
                    v            v            v
              Knowledge Base   LLM        Tools
                 TF-IDF       OpenRouter      |
                                             |
                                             v
                                      SQLite Database
                                             |
                                             v
                                      Appointment
                    |
                    v
              Twilio <Say>
                    |
                    v
               Voice Reply

ElevenLabs Webhook Flow
Audio
  |
  v
ElevenLabs Speech-to-Text
  |
  v
Transcription Webhook
  |
  v
Cloudflare HTTPS Tunnel
  |
  v
Flask Webhook Endpoint
  |
  v
Signature Verification
  |
  v
SQLite Webhook Event Storage

Technology Stack
Technology	Purpose
Python	Core application logic
Flask	REST API and webhook server
OpenRouter	LLM access
Twilio Voice	Phone calling and voice interaction
ElevenLabs	Text-to-Speech and Speech-to-Text
SQLite	Appointment and webhook persistence
Scikit-learn	TF-IDF knowledge retrieval
Cloudflare Tunnel	Public HTTPS endpoint for local webhook testing
HTML/CSS/JavaScript	Browser interface


PROJECT STRUCTURE
agentic-ai-calling-agent/
│
├── app.py
├── agent.py
├── knowledge_base.py
├── tools.py
├── tts.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
│
├── data/
│   └── knowledge.txt
│
├── templates/
│   └── index.html
│
└── tests/
    ├── test_api.py
    ├── test_elevenlabs.py
    └── test_webhook.py
