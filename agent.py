import os
import json

from openai import OpenAI

from knowledge_base import search_knowledge
from tools import (
    book_appointment,
    get_business_hours,
    get_services
)


# ==================================================
# OPENROUTER CLIENT
# ==================================================

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise RuntimeError(
        "OPENROUTER_API_KEY is not configured."
    )


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)


# Use OpenRouter's free model router.
# We keep the response size small for this voice agent.
MODEL = "openrouter/free"


# ==================================================
# SESSION MANAGEMENT
# ==================================================

sessions = {}


def get_session(session_id):

    if session_id not in sessions:

        sessions[session_id] = {
            "history": []
        }

    return sessions[session_id]


# ==================================================
# SYSTEM PROMPT
# ==================================================

SYSTEM_PROMPT = """
You are TechNova Solutions' AI customer support
and consultation booking agent.

You are designed for natural voice conversations.

Your responsibilities:

1. Answer customer questions accurately.
2. Use the company knowledge retrieved from the
   knowledge base.
3. Never invent company information.
4. Maintain conversation context.
5. Help customers book consultations.
6. Use the available tools when they are appropriate.
7. Keep responses short, clear and natural.

GROUNDING RULES:

- If the knowledge base contains relevant information,
  use it.
- If a tool can provide official company information,
  use the tool.
- For company services, use the get_services tool.
- For business hours, use the get_business_hours tool.
- If information is unavailable, say that it is not
  available instead of making it up.
- Never claim that an email, SMS, payment, notification,
  or other external action happened unless a tool actually
  performed that action.

BOOKING RULES:

To book a consultation, you need:

1. Customer name
2. Preferred date
3. Preferred time

If any information is missing, ask the customer for
the missing information.

Only call book_appointment when all three details
are available.

After the booking tool succeeds, tell the customer
that the consultation has been booked and provide
the appointment ID.

Do not claim that an email confirmation was sent.
"""


# ==================================================
# TOOL DEFINITIONS
# ==================================================

TOOLS = [

    {
        "type": "function",
        "function": {
            "name": "get_services",
            "description": (
                "Get the official services provided "
                "by TechNova Solutions."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_business_hours",
            "description": (
                "Get the official business hours "
                "of TechNova Solutions."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": (
                "Book a customer consultation. "
                "Only use this when the customer's "
                "name, preferred date and preferred "
                "time are all known."
            ),
            "parameters": {
                "type": "object",
                "properties": {

                    "name": {
                        "type": "string",
                        "description": (
                            "Customer's full name."
                        )
                    },

                    "date": {
                        "type": "string",
                        "description": (
                            "Preferred consultation date."
                        )
                    },

                    "time": {
                        "type": "string",
                        "description": (
                            "Preferred consultation time."
                        )
                    }

                },
                "required": [
                    "name",
                    "date",
                    "time"
                ]
            }
        }
    }
]


# ==================================================
# TOOL EXECUTION
# ==================================================

def execute_tool(tool_name, arguments):

    try:

        if tool_name == "get_services":

            return {
                "success": True,
                "services": get_services()
            }


        if tool_name == "get_business_hours":

            return {
                "success": True,
                "business_hours": get_business_hours()
            }


        if tool_name == "book_appointment":

            name = arguments.get("name")
            date = arguments.get("date")
            time = arguments.get("time")


            if not name or not date or not time:

                return {
                    "success": False,
                    "error": (
                        "Name, date and time are required "
                        "to book an appointment."
                    )
                }


            return book_appointment(
                name,
                date,
                time
            )


        return {
            "success": False,
            "error": (
                f"Unknown tool: {tool_name}"
            )
        }


    except Exception as error:

        return {
            "success": False,
            "error": str(error)
        }


# ==================================================
# MAIN AGENT FUNCTION
# ==================================================

def get_response(session_id, user_message):

    session = get_session(session_id)


    # ------------------------------------------------
    # Retrieve relevant knowledge
    # ------------------------------------------------

    knowledge = search_knowledge(
        user_message,
        top_k=3
    )


    # ------------------------------------------------
    # Build conversation
    # ------------------------------------------------

    messages = [

        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },

        {
            "role": "system",
            "content": (
                "Relevant company knowledge retrieved "
                "from the knowledge base:\n\n"
                + knowledge
            )
        }

    ]


    # Add previous conversation

    messages.extend(
        session["history"]
    )


    # Add current user message

    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )


    # ------------------------------------------------
    # Agentic tool-calling loop
    # ------------------------------------------------

    for _ in range(5):

        response = client.chat.completions.create(

            model=MODEL,

            messages=messages,

            tools=TOOLS,

            tool_choice="auto",

            max_tokens=300
        )


        assistant_message = (
            response.choices[0].message
        )


        # ------------------------------------------------
        # No tool call → final answer
        # ------------------------------------------------

        if not assistant_message.tool_calls:

            answer = assistant_message.content


            if not answer:

                answer = (
                    "I'm sorry, I couldn't generate "
                    "a response."
                )


            # Save conversation

            session["history"].append(
                {
                    "role": "user",
                    "content": user_message
                }
            )

            session["history"].append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )


            return answer


        # ------------------------------------------------
        # Tool call requested
        # ------------------------------------------------

        messages.append(
            {
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }
                    for tool_call in assistant_message.tool_calls
                ]
            }
        )


        # ------------------------------------------------
        # Execute each requested tool
        # ------------------------------------------------

        for tool_call in assistant_message.tool_calls:

            tool_name = (
                tool_call.function.name
            )

            arguments_text = (
                tool_call.function.arguments
            )


            # Parse JSON arguments

            try:

                arguments = json.loads(
                    arguments_text
                )

            except json.JSONDecodeError:

                arguments = {}


            # Execute Python function

            result = execute_tool(
                tool_name,
                arguments
            )


            # Return result to model

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                }
            )


    # ------------------------------------------------
    # Safety fallback
    # ------------------------------------------------

    return (
        "I'm sorry, I couldn't complete "
        "that request. Please try again."
    )