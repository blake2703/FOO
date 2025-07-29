import uuid
import datetime
import time

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    
class EventType(Enum):
    USER_INPUT = "user_input"
    AGENT_RESPONSE = "agent_response"
    COMMAND_EXECUTED = "command_executed"
    AGENT_SWITCHED = "agent_switched"
    ERROR_OCCURRED = "error_occurred"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    SYSTEM_EVENT = "system_event"


@dataclass
class LogEntry:
    """Structured data for logging chat events"""
    timestamp: str
    session_id: str
    event_type: EventType 
    level: LogLevel
    message: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "event_type": self.event_type.value,
            "level": self.level.value,
            "message": self.message,
            "metadata": self.metadata or {}
        }

@dataclass
class AgentInteraction:
    """Specifics logging for agent interactions"""
    agent_name: str
    user_input: str
    agent_response: str
    response_time: float
    tokens_used: Optional[int] = None
    error: Optional[str] = None

class LogHandler:
    def handle(self, entry: LogEntry):
        raise NotImplementedError

class DatabaseLogHandler(LogHandler):
    """Outputs logs to a database"""
    pass


class CommandLineLogger:
    """Main logging class for the command line system
    
    Each method will be generated to account for each different scenario
    """
    def __init__(self, session_id: Optional[str] = None):
        self.sesion_id = session_id or str(uuid.uuid4())
        self.start_time = time.time()
    
    def _log(self, event_type: EventType, level: LogLevel, message: str, metadata: Dict = None):
        entry = LogEntry(
            timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
            session_id=self.sesion_id,
            event_type=event_type,
            level=level,
            message=message,
            metadata=metadata or {}
        )
        try:
            print(entry)
        except Exception as e:
            print(f"Logging error: {e}")
    
    def log_session_start(self, agents: List, config: Dict):
        """Log the start of a chat session

        Args:
            agents (List): List of agent objects available in the system.
            config (Dict): Configuration settings loaded from JSON or defaults.
        """
        metadata = {
            "agent_count": len(agents),
            "model_names": [agent.config.model_name for agent in agents],
            "temperatures": [agent.config.temperature for agent in agents],
            "max_completion_tokens": [agent.config.max_completion_tokens for agent in agents],
            "is_harmonizer": [agent.config.harmonizer for agent in agents],
            "agent_directives": [agent.config.agent_directives for agent in agents],
            "config_summary": {
                "general_instructions": config.get('CONFIG', {}).get('general_instructions', 'None'),
            }
        }
        
        self._log(event_type=EventType.SESSION_START, level=LogLevel.INFO, message="Started", metadata=metadata)
    
    def log_session_end(self, duration: float = None):
        """Log the end of a chat session
        Args:
            duration (float, optional): The total time the chat was open for. Defaults to None.
        """
        if duration is None:
            duration = time.time() - self.start_time
        
        metadata = {
            "session_duration_seconds": round(duration, 2)
        }
        self._log(event_type=EventType.SESSION_END, level=LogLevel.INFO, message="Session ended", metadata=metadata)
        
    
    def log_user_input(self, user_input: str, current_target: Optional[str] = None):
        """Log user input

        Args:
            user_input (str): _description_
            current_target (Optional[str], optional): _description_. Defaults to None.
        """
        metadata = {
            "input_length": len(user_input),
            "target_agent": current_target,
            "is_command": user_input.startswith('/')
        }        
        self._log(event_type=EventType.USER_INPUT, level=LogLevel.INFO, message=f"User: {user_input}", metadata=metadata)
    
    def log_agent_response(self, interaction: AgentInteraction):
        """Log agent response with metrics"""
        metadata = {
            "agent_name": interaction.agent_name,
            "response_time_ms": round(interaction.response_time * 1000, 2),
            "input_length": len(interaction.user_input),
            "response_length": len(interaction.agent_response),
            "tokens_used": interaction.tokens_used,
            "had_error": interaction.error is not None
        }
        if interaction.error:
            self._log(event_type=EventType.ERROR_OCCURRED, level=LogLevel.ERROR, message=f"Agent {interaction.agent_name} error: {interaction.error}", metadata=metadata)
        self._log(event_type=EventType.AGENT_RESPONSE, level=LogLevel.INFO, message=f"Agent {interaction.agent_name} error: {interaction.error}", metadata=metadata)