# src/handlers.py
import json
import logging as log
from typing import Any, Dict, Optional

from fastapi import WebSocket
from rapidfuzz import fuzz, process

from src.utils.models import (
    ConversationRequestMessage,
    ConversationResponseMessage,
    ConversationResultMessage,
    FlexMessage,
)

questions = {
    "Thank you for joining me": "q1",
    "First, how did you find your care services today": "q1",
    "How could we provide better services next time": "q2",
    "What do you like most about the Harvard Medicine Family Van": "q3",
    "Is there anything else you'd like to share with us": "q4",
}


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

        if msg.name == "conversationResult":
            conversation_result = ConversationResultMessage.model_validate_json(message)
            log.info(f"Received conversation_result {conversation_result}")
            await handle_conversation_result(ws, conversation_result)
        else:
            # Handle other message types
            log.info(f"Received message {msg}")

    except Exception as e:
        log.error(f"Unrecognized message: {message}")
        log.error(f"Error: {e}")


def match_question(input_sentence: str, threshold: int = 70):
    """
    Returns the key (ID) of the best-matching question if score >= threshold.
    Otherwise returns None.
    """

    # Create a list of question texts
    question_texts = list(questions.keys())

    # Get best match using RapidFuzz (similar to fuzzywuzzy)
    best_match, score, idx = process.extractOne(input_sentence, question_texts, scorer=fuzz.ratio)

    if score >= threshold:
        return questions[best_match]  # return the q1/q2/q3/q4 identifier
    else:
        return None


async def handle_conversation_result(ws: WebSocket, request: ConversationRequestMessage) -> None:
    """
    Handle conversation request message

    Args:
        ws: WebSocket connection
        request: Parsed conversation request
    """
    input_text = request.get_input_text()
    if not input_text:
        return

    # Try to match question number
    qnum = match_question(input_text)
    log.info(f"Conv result: {request.get_input_text()} {qnum=}")
    if qnum:
        url = f"https://clinicfeedback.org/images/en_{qnum}.png"

        # Build WS response
        response_body = {
            "input": {"text": input_text},
            "output": {"text": ""},  # assistant says nothing; image will show separately
            "variables": {
                qnum: {
                    "component": "image",
                    "data": {
                        "alt": qnum,
                        "url": url,
                    },
                }
            },
        }

        await send_conversation_response(ws, response_body)
        return


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
    log.info(f"Sent response: {response_body['variables']}")
