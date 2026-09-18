import os
import json
import hashlib
import sqlite3
from datetime import datetime

from flask import Flask, request, jsonify, render_template, Response
from dotenv import load_dotenv

from elevenlabs.client import ElevenLabs
from elevenlabs.errors import BadRequestError

from twilio.twiml.voice_response import VoiceResponse, Gather

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

elevenlabs = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY")
)

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# Current Cloudflare Quick Tunnel URL
PUBLIC_URL = "https://unsigned-solution-clicks-africa.trycloudflare.com"

from agent import get_response
from tts import text_to_speech
from tools import get_services, get_business_hours


app = Flask(__name__)

WEBHOOK_DB = "data/webhooks.db"


# ============================================================
# WEBHOOK DATABASE
# ============================================================

def init_webhook_db():
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(WEBHOOK_DB)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS webhook_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_hash TEXT UNIQUE NOT NULL,
            event_type TEXT,
            request_id TEXT,
            received_at TEXT NOT NULL,
            payload TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_webhook_db()


# ============================================================
# HOME
# ============================================================

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy"
    })


# ============================================================
# BROWSER CHAT API
# ============================================================

@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True) or {}

    session_id = data.get(
        "session_id",
        "default"
    )

    message = data.get("message")

    if not message:
        return jsonify({
            "error": "message is required"
        }), 400

    try:

        response = get_response(
            session_id,
            message
        )

        return jsonify({
            "session_id": session_id,
            "response": response
        })

    except Exception as e:

        print("Chat error:", e)

        return jsonify({
            "error": "Failed to process the request."
        }), 500


# ============================================================
# ELEVENLABS TEXT TO SPEECH
# ============================================================

@app.route("/tts", methods=["POST"])
def tts():

    data = request.get_json(silent=True) or {}

    text = data.get("text")

    if not text:
        return jsonify({
            "error": "text is required"
        }), 400

    try:

        audio = text_to_speech(text)

        return Response(
            audio,
            mimetype="audio/mpeg"
        )

    except Exception as e:

        print("TTS error:", e)

        return jsonify({
            "error": "Failed to generate speech."
        }), 500


# ============================================================
# TWILIO PHONE ENTRY POINT
# ============================================================

@app.route("/voice", methods=["GET", "POST"])
def voice():

    response = VoiceResponse()

    gather = Gather(
        input="speech",
        action=f"{PUBLIC_URL}/voice/process",
        method="POST",
        speech_timeout="auto",
        language="en-IN"
    )

    gather.say(
        "Hello! Welcome to TechNova Solutions. "
        "I am your AI calling assistant. "
        "How can I help you today?"
    )

    response.append(gather)

    response.say(
        "I didn't hear anything. "
        "Please call again if you need assistance."
    )

    response.hangup()

    return Response(
        str(response),
        mimetype="text/xml"
    )


# ============================================================
# TWILIO SPEECH PROCESSING
# ============================================================

@app.route("/voice/process", methods=["POST"])
def voice_process():

    # --------------------------------------------------------
    # Speech recognized by Twilio
    # --------------------------------------------------------

    speech = request.form.get(
        "SpeechResult",
        ""
    ).strip()

    # --------------------------------------------------------
    # Unique Twilio call identifier
    # --------------------------------------------------------

    call_sid = request.form.get(
        "CallSid",
        "unknown"
    )

    print()
    print("========================================")
    print("TWILIO VOICE INPUT")
    print("========================================")
    print("Call SID:", call_sid)
    print("Speech:", speech)
    print("========================================")
    print()

    response = VoiceResponse()


    # --------------------------------------------------------
    # No speech detected
    # --------------------------------------------------------

    if not speech:

        gather = Gather(
            input="speech",
            action=f"{PUBLIC_URL}/voice/process",
            method="POST",
            speech_timeout="auto",
            language="en-IN"
        )

        gather.say(
            "I didn't catch that. "
            "Please tell me how I can help."
        )

        response.append(gather)

        return Response(
            str(response),
            mimetype="text/xml"
        )


    # --------------------------------------------------------
    # PROCESS CALLER REQUEST
    # --------------------------------------------------------

    try:

        session_id = f"twilio-{call_sid}"

        speech_lower = speech.lower()


        # ====================================================
        # FAST PATH 1: SERVICES
        # ====================================================

        if (
            "service" in speech_lower
            or "services" in speech_lower
            or "what do you provide" in speech_lower
            or "what do you offer" in speech_lower
        ):

            services = get_services()

            ai_response = (
                "We provide "
                + ", ".join(services[:-1])
                + ", and "
                + services[-1]
                + "."
            )


        # ====================================================
        # FAST PATH 2: BUSINESS HOURS
        # ====================================================

        elif (
            "hour" in speech_lower
            or "hours" in speech_lower
            or "open" in speech_lower
            or "when are you open" in speech_lower
        ):

            hours = get_business_hours()

            ai_response = (
                "Our business hours are "
                "Monday to Friday, 9 AM to 6 PM, "
                "Saturday, 10 AM to 2 PM, "
                "and we are closed on Sunday."
            )


        # ====================================================
        # FAST PATH 3: PRICING
        # ====================================================

        elif (
            "price" in speech_lower
            or "pricing" in speech_lower
            or "cost" in speech_lower
            or "how much" in speech_lower
        ):

            ai_response = (
                "Pricing depends on project requirements. "
                "Please book a consultation for an exact quote."
            )


        # ====================================================
        # FAST PATH 4: COMPANY INFORMATION
        # ====================================================

        elif (
            "company" in speech_lower
            or "who are you" in speech_lower
            or "what is technova" in speech_lower
        ):

            ai_response = (
                "TechNova Solutions is a software technology "
                "company providing digital solutions for businesses."
            )


        # ====================================================
        # FULL AI AGENT
        # ====================================================

        else:

            print("Using full AI agent...")

            ai_response = get_response(
                session_id,
                speech
            )


    except Exception as e:

        print("AI agent error:", e)

        ai_response = (
            "I'm sorry, I am having trouble processing "
            "your request right now."
        )


    # --------------------------------------------------------
    # LOG RESPONSE
    # --------------------------------------------------------

    print()
    print("========================================")
    print("TWILIO AI RESPONSE")
    print("========================================")
    print("Response:", ai_response)
    print("========================================")
    print()


    # --------------------------------------------------------
    # SPEAK AI RESPONSE TO CALLER
    # --------------------------------------------------------

    gather = Gather(
        input="speech",
        action=f"{PUBLIC_URL}/voice/process",
        method="POST",
        speech_timeout="auto",
        language="en-IN"
    )

    gather.say(
        ai_response
    )

    response.append(gather)


    # --------------------------------------------------------
    # FALLBACK IF CALLER DOES NOT RESPOND
    # --------------------------------------------------------

    response.say(
        "Thank you for calling TechNova Solutions. "
        "Goodbye."
    )

    response.hangup()


    return Response(
        str(response),
        mimetype="text/xml"
    )


# ============================================================
# ELEVENLABS TRANSCRIPTION WEBHOOK
# ============================================================

@app.route(
    "/webhook/elevenlabs",
    methods=["POST"]
)
def elevenlabs_webhook():

    if not WEBHOOK_SECRET:

        return jsonify({
            "error": "Webhook secret is not configured."
        }), 500


    # --------------------------------------------------------
    # Read raw webhook body
    # --------------------------------------------------------

    raw_body = request.get_data(
        cache=True
    )


    # --------------------------------------------------------
    # Get ElevenLabs signature
    # --------------------------------------------------------

    signature = request.headers.get(
        "ElevenLabs-Signature"
    )


    if not signature:

        return jsonify({
            "error": "Missing ElevenLabs-Signature header."
        }), 401


    # --------------------------------------------------------
    # Verify ElevenLabs webhook signature
    # --------------------------------------------------------

    try:

        event = elevenlabs.webhooks.construct_event(
            rawBody=raw_body.decode("utf-8"),
            sig_header=signature,
            secret=WEBHOOK_SECRET
        )

    except BadRequestError:

        print(
            "Invalid ElevenLabs webhook signature."
        )

        return jsonify({
            "error": "Invalid webhook signature."
        }), 401

    except Exception as e:

        print(
            "Webhook verification error:",
            e
        )

        return jsonify({
            "error": "Webhook verification failed."
        }), 401


    # --------------------------------------------------------
    # Extract event information
    # --------------------------------------------------------

    event_type = event.get(
        "type"
    )

    event_data = event.get(
        "data",
        {}
    )

    request_id = event_data.get(
        "request_id"
    )


    # --------------------------------------------------------
    # Create event hash for duplicate protection
    # --------------------------------------------------------

    event_hash = hashlib.sha256(
        raw_body
    ).hexdigest()


    # --------------------------------------------------------
    # Store webhook event
    # --------------------------------------------------------

    try:

        conn = sqlite3.connect(
            WEBHOOK_DB
        )

        conn.execute(
            """
            INSERT INTO webhook_events
            (
                event_hash,
                event_type,
                request_id,
                received_at,
                payload
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                event_hash,
                event_type,
                request_id,
                datetime.utcnow().isoformat(),
                json.dumps(event)
            )
        )

        conn.commit()
        conn.close()


    except sqlite3.IntegrityError:

        print(
            "Duplicate webhook ignored:",
            event_hash
        )

        return jsonify({
            "status": "already_processed"
        }), 200


    # --------------------------------------------------------
    # Process transcription event
    # --------------------------------------------------------

    if event_type == "speech_to_text_transcription":

        transcription = event_data.get(
            "transcription",
            {}
        )

        text = transcription.get(
            "text",
            ""
        )

        language = transcription.get(
            "language_code"
        )


        print()
        print("========================================")
        print("ELEVENLABS TRANSCRIPTION WEBHOOK")
        print("========================================")
        print("Request ID:", request_id)
        print("Language:", language)
        print("Transcript:", text)
        print("========================================")
        print()


    else:

        print(
            "Received ElevenLabs event:",
            event_type
        )


    return jsonify({
        "status": "received"
    }), 200


# ============================================================
# GENERIC WEBHOOK TEST
# ============================================================

@app.route(
    "/webhook",
    methods=["POST"]
)
def webhook():

    data = request.get_json(
        silent=True
    ) or {}

    print(
        "Webhook received:"
    )

    print(
        data
    )

    return jsonify({
        "status": "received"
    }), 200


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )