# src/models.py
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class FlexMessage(BaseModel):
    """Flexible message that handles various WebSocket message structures"""

    # Core fields present in all messages
    category: str
    kind: str
    name: str

    # Optional body - can contain various structures
    body: Optional[Dict[str, Any]] = None

    # Timestamp (added by recorder, not in original message)
    timestamp: Optional[str] = None

    model_config = ConfigDict(
        extra="allow",  # Allow additional fields we haven't defined
        populate_by_name=True,
    )

    # Message type detection helpers
    @property
    def message_type(self) -> str:
        """Identify the message type"""
        return self.name

    @property
    def is_state_message(self) -> bool:
        """Check if this is a state update message"""
        return self.name == "state"

    @property
    def is_conversation_result(self) -> bool:
        """Check if this is a conversation result message"""
        return self.name == "conversationResult"

    @property
    def is_persona_response(self) -> bool:
        """Check if this is a persona response message"""
        return self.name == "personaResponse"

    @property
    def is_recognize_results(self) -> bool:
        """Check if this is a speech recognition result"""
        return self.name == "recognizeResults"

    # State message helpers
    def get_session_state(self) -> Optional[str]:
        """Extract session state if available"""
        if self.body and "session" in self.body:
            return self.body["session"].get("state")
        return None

    def get_session_id(self) -> Optional[str]:
        """Extract session ID"""
        if self.body and "session" in self.body:
            return self.body["session"].get("sessionId")
        # Also check in configuration
        if self.body and "configuration" in self.body:
            session = self.body.get("session", {})
            return session.get("sessionId")
        return None

    def get_recognizing_state(self) -> Optional[bool]:
        """Check if speech recognition is active"""
        if self.body and "recognizing" in self.body:
            return self.body["recognizing"]
        return None

    def get_speech_state(self) -> Optional[str]:
        """Get persona speech state"""
        if self.body and "persona" in self.body:
            personas = self.body["persona"]
            for persona_id, persona_data in personas.items():
                if "speechState" in persona_data:
                    return persona_data["speechState"]
        return None

    def get_camera_state(self) -> Optional[str]:
        """Get camera animation state"""
        if self.body and "persona" in self.body:
            personas = self.body["persona"]
            for persona_id, persona_data in personas.items():
                if "cameraAnimating" in persona_data:
                    return persona_data["cameraAnimating"]
        return None

    def get_conversation_turn(self) -> Optional[str]:
        """Get whose turn it is in the conversation"""
        if self.body and "persona" in self.body:
            personas = self.body["persona"]
            for persona_id, persona_data in personas.items():
                users = persona_data.get("users", [])
                if users and len(users) > 0:
                    conversation = users[0].get("conversation", {})
                    return conversation.get("turn")
        return None

    # Conversation result helpers
    def get_input_text(self) -> Optional[str]:
        """Extract input text from conversation result"""
        if self.body and "input" in self.body:
            return self.body["input"].get("text")
        return None

    def get_user_text(self) -> Optional[str]:
        """Extract user text from conversation result"""
        """ msg.body
        {'results': [{'alternatives': [{'confidence': 0.79052734, 'transcript': 'Hello?'}], 'final': True}], 'status': 0}
        """
        if not self.body or "results" not in self.body:
            return None

        for result in self.body["results"]:
            if result.get("final") is True:
                alts = result.get("alternatives", [])
                if not alts:
                    return None
                # Pick alternative with highest confidence
                best = max(alts, key=lambda a: a.get("confidence", 0))
                return best.get("transcript")

        return None

    def get_output_text(self) -> Optional[str]:
        """Extract output text from conversation result"""
        if self.body and "output" in self.body:
            return self.body["output"].get("text")
        return None

    def get_persona_id(self) -> Optional[str]:
        """Extract persona ID"""
        if self.body:
            return self.body.get("personaId")
        return None

    def get_provider_kind(self) -> Optional[str]:
        """Get provider kind"""
        if self.body and "provider" in self.body:
            return self.body["provider"].get("kind")
        return None

    def get_end_conversation(self) -> Optional[bool]:
        """Check if conversation should end"""
        if self.body and "provider" in self.body:
            meta = self.body["provider"].get("meta", {})
            return meta.get("endConversation")
        return None

    def get_traces(self) -> List[Dict[str, Any]]:
        """Extract trace information"""
        if self.body and "provider" in self.body:
            return self.body["provider"].get("trace", [])
        return []

    def get_total_latency(self) -> int:
        """Calculate total latency from traces"""
        traces = self.get_traces()
        return sum(trace.get("latency_ms", 0) for trace in traces)

    # Persona response helpers
    def get_current_speech(self) -> Optional[str]:
        """Get current speech text"""
        if self.body:
            return self.body.get("currentSpeech")
        return None

    def get_data_collector(self) -> Optional[str]:
        """Get data collector text"""
        if self.body:
            return self.body.get("dataCollector")
        return None

    def get_user_input(self) -> Optional[str]:
        """Get user input that triggered response"""
        if self.body:
            return self.body.get("userInput")
        return None

    def get_speech_markers(self) -> List[Any]:
        """Get speech markers"""
        if self.body:
            return self.body.get("speechMarkers", [])
        return []

    # Recognition results helpers
    def get_recognition_transcript(self) -> Optional[str]:
        """Get speech recognition transcript"""
        if self.body and "results" in self.body:
            results = self.body["results"]
            if results and len(results) > 0:
                alternatives = results[0].get("alternatives", [])
                if alternatives and len(alternatives) > 0:
                    return alternatives[0].get("transcript")
        return None

    def get_recognition_confidence(self) -> Optional[float]:
        """Get recognition confidence"""
        if self.body and "results" in self.body:
            results = self.body["results"]
            if results and len(results) > 0:
                alternatives = results[0].get("alternatives", [])
                if alternatives and len(alternatives) > 0:
                    return alternatives[0].get("confidence")
        return None

    def is_final_recognition(self) -> bool:
        """Check if recognition result is final"""
        if self.body and "results" in self.body:
            results = self.body["results"]
            if results and len(results) > 0:
                return results[0].get("final", False)
        return False

    # Context helpers
    def get_context(self) -> Dict[str, Any]:
        """Get conversation context"""
        if self.body and "persona" in self.body:
            personas = self.body["persona"]
            for persona_id, persona_data in personas.items():
                users = persona_data.get("users", [])
                if users and len(users) > 0:
                    conversation = users[0].get("conversation", {})
                    return conversation.get("context", {})
        return {}

    def get_turn_id(self) -> Optional[str]:
        """Get current turn ID"""
        context = self.get_context()
        return context.get("Turn_Id")

    # Scene information helpers
    def get_scene_id(self) -> Optional[str]:
        """Get scene ID"""
        if self.body and "scene" in self.body:
            return self.body["scene"].get("sceneId")
        return None

    def get_feature_flags(self) -> List[str]:
        """Get enabled feature flags"""
        if self.body and "scene" in self.body:
            return self.body["scene"].get("featureFlags", [])
        return []

    # String representation for debugging
    def __str__(self) -> str:
        """Readable string representation"""
        parts = [f"Message(name={self.name}"]

        if self.is_conversation_result:
            parts.append(f"input='{self.get_input_text()}'")
            parts.append(f"output='{self.get_output_text()}'")
        elif self.is_persona_response:
            parts.append(f"speech='{self.get_current_speech()}'")
        elif self.is_recognize_results:
            parts.append(f"transcript='{self.get_recognition_transcript()}'")
        elif self.is_state_message:
            if self.get_session_state():
                parts.append(f"session={self.get_session_state()}")
            if self.get_speech_state():
                parts.append(f"speech={self.get_speech_state()}")
            if self.get_conversation_turn():
                parts.append(f"turn={self.get_conversation_turn()}")

        parts.append(")")
        return " ".join(parts)


# Optional: Specific message types for type safety
class StateMessage(FlexMessage):
    """State update message"""

    name: Literal["state"] = "state"


class ConversationResultMessage(FlexMessage):
    """Conversation result message"""

    name: Literal["conversationResult"] = "conversationResult"


class PersonaResponseMessage(FlexMessage):
    """Persona response message"""

    name: Literal["personaResponse"] = "personaResponse"


class RecognizeResultsMessage(FlexMessage):
    """Speech recognition results"""

    name: Literal["recognizeResults"] = "recognizeResults"


# src/models.py (add to existing models)
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ConversationInput(BaseModel):
    """Conversation input"""

    text: str


class ConversationOutput(BaseModel):
    """Conversation output"""

    text: str
    context: Optional[Dict[str, Any]] = None


class OptionalArgs(BaseModel):
    """Optional arguments in conversation request"""

    kind: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class ConversationRequestBody(BaseModel):
    """Conversation request body"""

    input: ConversationInput
    optionalArgs: Optional[OptionalArgs] = None
    context: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="allow")


class ConversationRequestMessage(FlexMessage):
    """Conversation request message"""

    name: Literal["conversationRequest"] = "conversationRequest"
    body: ConversationRequestBody

    def get_input_text(self) -> Optional[str]:
        """Get input text from request"""
        if isinstance(self.body, dict):
            input_data = self.body.get("input", {})
            return input_data.get("text")
        return self.body.input.text if self.body else None

    def get_optional_args(self) -> Optional[Dict[str, Any]]:
        """Get optional arguments"""
        if isinstance(self.body, dict):
            return self.body.get("optionalArgs")
        return self.body.optionalArgs.model_dump() if self.body and self.body.optionalArgs else None

    def is_init_request(self) -> bool:
        """Check if this is an initialization request"""
        optional_args = self.get_optional_args()
        if optional_args:
            return optional_args.get("kind") == "init"
        return False

    def get_context(self) -> Dict[str, Any]:
        """Get conversation context"""
        if isinstance(self.body, dict):
            return self.body.get("context", {})
        return self.body.context if self.body and self.body.context else {}


class ConversationResponseBody(BaseModel):
    """Conversation response body"""

    input: ConversationInput
    output: ConversationOutput
    variables: Dict[str, Any] = Field(default_factory=dict)
    fallback: Optional[bool] = None

    model_config = ConfigDict(extra="allow")


class ConversationResponseMessage(BaseModel):
    """Conversation response message"""

    category: Literal["scene"] = "scene"
    kind: Literal["request"] = "request"
    name: Literal["conversationResponse"] = "conversationResponse"
    body: ConversationResponseBody
