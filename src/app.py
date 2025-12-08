# src/app.py
import json
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from src.api.handler import handle_message
from src.utils.models import FlexMessage
from src.utils.ws_recorder import WebSocketRecorder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
recorder = WebSocketRecorder()

app = FastAPI()


@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    await recorder.start()

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            await recorder.record("recv", data)

            try:
                # Handle the message
                await handle_message(websocket, data)

            except ValidationError as e:
                logger.error(f"Validation error: {e}")
                error_response = {
                    "status": "error",
                    "message": "Invalid message format",
                    "errors": e.errors(),
                }
                await websocket.send_json(error_response)

            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                await websocket.send_json({"status": "error", "message": "Invalid JSON"})

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        raise

    finally:
        await recorder.stop()


def main():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="info")


if __name__ == "__main__":
    main()
