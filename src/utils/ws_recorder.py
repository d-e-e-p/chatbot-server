import asyncio
import json
import logging as log
from datetime import datetime
from pathlib import Path

import nest_asyncio
from fastapi import WebSocket

from src.utils.models import FlexMessage


class WebSocketRecorder:
    def __init__(self, trace_dir="trace", rpt_dir="rpt"):
        self.trace_dir = Path(trace_dir)
        self.trace_dir.mkdir(exist_ok=True)
        self.trace_file = None

        self.rpt_dir = Path(rpt_dir)
        self.rpt_dir.mkdir(exist_ok=True)
        self.rpt_file = None

        self.session_id = None

    async def start(self):
        # TODO: add suffix in case multiple sessions at same time
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.trace_file = self.trace_dir / f"{self.session_id}.jsonl"
        self.transcript = []

    async def record(self, direction: str, data: str):
        timestamp = datetime.now().isoformat()
        record = {"timestamp": timestamp, "direction": direction, "data": data}
        self.transcript.append(record)
        with open(self.trace_file, "a") as f:
            f.write(json.dumps(record) + "\n")

    async def stop(self):
        await self.record_convertation()
        self.transcript = []

    async def record_convertation(self):
        self.rpt_file = self.rpt_dir / f"{self.session_id}.rpt"
        fp = open(self.rpt_file, "w")
        # extract metadata from first record
        record = self.transcript[0]
        msg = FlexMessage.model_validate_json(record["data"])
        fp.write(f"Datetime: {record['timestamp']}\n")
        fp.write(f"SessionId: {msg.get_data_collector()}\n")

        for record in self.transcript:
            msg = FlexMessage.model_validate_json(record["data"])
            if msg.is_recognize_results:
                text = msg.get_user_text()
                if text:
                    fp.write(f"Patient: {text}\n")
            elif msg.is_conversation_result:
                text = msg.get_input_text()
                if text:
                    fp.write(f"Listener: {text}\n")

        fp.close()
        log.info(f"Transcript saved to {self.rpt_file}")
