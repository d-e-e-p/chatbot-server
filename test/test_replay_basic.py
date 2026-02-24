import json
import logging as log

import fastapi
import pytest
from fastapi.testclient import TestClient

from src.app import app


def load_recording(recording_file):
    records = []
    with open(recording_file, "r") as f:
        for line in f:
            records.append(json.loads(line))
    return records


@pytest.mark.parametrize(
    "recording",
    [
        "trace/test.jsonl",
    ],
)
def test_websocket_with_recording(recording):
    records = load_recording(recording)
    client = TestClient(app)
    with client.websocket_connect("/") as websocket:
        # Track expected responses
        expected_responses = [r["data"] for r in records if r["direction"] == "sent"]
        response_index = 0

        # Send all received messages
        for record in records:
            # log.info(f"{record=}")
            if record["direction"] == "received" or record["direction"] == "recv":
                websocket.send_text(record["data"])

                # Check response if available
                if response_index < len(expected_responses):
                    response = websocket.receive_text()
                    assert response == expected_responses[response_index]
                    response_index += 1
