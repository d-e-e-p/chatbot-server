# src/handlers.py
import json
import logging as log
from typing import Any, Dict, Optional

from fastapi import WebSocket

from src.utils.models import ConversationRequestMessage, ConversationResponseMessage, FlexMessage


async def handle_message(ws: WebSocket, message: str) -> None:
    """
    Handle incoming WebSocket message

    Args:
        ws: WebSocket connection
        message: Raw message string
    """
    try:
        # Parse as flexible message
        msg = FlexMessage.model_validate_json(message)
        log.info(f"Received message type: {msg.name}")
        log.info(msg)

        if msg.name == "conversationRequest":
            request = ConversationRequestMessage.model_validate_json(message)
            await handle_conversation_request(ws, request)
        else:
            # Handle other message types
            log.info(f"Received message type: {msg.name}")

    except Exception as e:
        log.error(f"Unrecognized message: {message}")
        log.error(f"Error: {e}")


async def handle_conversation_request(ws: WebSocket, request: ConversationRequestMessage) -> None:
    """
    Handle conversation request message

    Args:
        ws: WebSocket connection
        request: Parsed conversation request
    """
    log.info(f"Conv request: {request.get_input_text()}")

    # Get input text
    input_text = request.get_input_text() or ""

    # Create base response
    response_body = {
        "input": {"text": input_text},
        "output": {"text": f"Echo: {input_text}"},
        "variables": {},
    }

    # Handle welcome/init message
    if request.is_init_request():
        response_body["output"]["text"] = "Hello there!"

    # Handle fallback example
    if input_text.lower().startswith("why"):
        response_body["output"]["text"] = "I do not know how to answer that"
        response_body["fallback"] = True

    # Handle content cards example
    if input_text.lower() == "cat":
        response_body["output"]["text"] = "Here is a cat @showcards(cat)"
        response_body["variables"]["public-cat"] = {
            "component": "image",
            "data": {"alt": "A cute kitten", "url": "https://i.imgur.com/s7Erio7.jpeg"},
        }

    # Send response
    await send_conversation_response(ws, response_body)


async def send_conversation_response(ws: WebSocket, response_body: Dict[str, Any]) -> None:
    """
    Send conversation response message

    Args:
        ws: WebSocket connection
        response_body: Response body data
    """
    message = {
        "category": "scene",
        "kind": "request",
        "name": "conversationResponse",
        "body": response_body,
    }

    await ws.send_text(json.dumps(message))
    log.info(f"Sent response: {response_body['output']['text']}")
