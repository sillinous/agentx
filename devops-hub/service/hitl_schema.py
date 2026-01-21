"""
Human-in-the-Loop (HITL) Database Schema

Stores requests from AI agents for human actions.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class RequestType(str, Enum):
    API_KEY = "api_key"
    ACCOUNT_CREATION = "account_creation"
    LEGAL_DOCUMENT = "legal_document"
    PAYMENT_AUTHORIZATION = "payment_authorization"
    BUSINESS_SETUP = "business_setup"
    STRATEGIC_DECISION = "strategic_decision"
    CUSTOM = "custom"


class RequestPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class RequestStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    FULFILLED = "fulfilled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class FieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    SECRET = "secret"
    BOOLEAN = "boolean"
    SELECT = "select"
    FILE = "file"
    NUMBER = "number"
    DATE = "date"


class HumanActionRequest:
    """Represents a request from an agent for human action."""
    
    def __init__(
        self,
        id: str,
        request_type: str,
        title: str,
        description: str,
        agent_id: str,
        priority: str = "medium",
        status: str = "pending",
        workflow_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        required_fields: Optional[Dict[str, str]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
        fulfilled_at: Optional[str] = None,
        fulfilled_by: Optional[str] = None,
        notes: Optional[str] = None,
    ):
        self.id = id
        self.request_type = request_type
        self.title = title
        self.description = description
        self.agent_id = agent_id
        self.priority = priority
        self.status = status
        self.workflow_id = workflow_id
        self.context = context or {}
        self.required_fields = required_fields or {}
        self.response_data = response_data
        self.created_at = created_at or datetime.now().isoformat()
        self.fulfilled_at = fulfilled_at
        self.fulfilled_by = fulfilled_by
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "request_type": self.request_type,
            "title": self.title,
            "description": self.description,
            "agent_id": self.agent_id,
            "priority": self.priority,
            "status": self.status,
            "workflow_id": self.workflow_id,
            "context": self.context,
            "required_fields": self.required_fields,
            "response_data": self.response_data,
            "created_at": self.created_at,
            "fulfilled_at": self.fulfilled_at,
            "fulfilled_by": self.fulfilled_by,
            "notes": self.notes,
        }


# SQL Schema for SQLite
CREATE_HITL_REQUESTS_TABLE = """
CREATE TABLE IF NOT EXISTS hitl_requests (
    id TEXT PRIMARY KEY,
    request_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'pending',
    workflow_id TEXT,
    context TEXT,  -- JSON
    required_fields TEXT,  -- JSON
    response_data TEXT,  -- JSON  
    created_at TEXT NOT NULL,
    fulfilled_at TEXT,
    fulfilled_by TEXT,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_hitl_status ON hitl_requests(status);
CREATE INDEX IF NOT EXISTS idx_hitl_priority ON hitl_requests(priority);
CREATE INDEX IF NOT EXISTS idx_hitl_agent ON hitl_requests(agent_id);
CREATE INDEX IF NOT EXISTS idx_hitl_created ON hitl_requests(created_at);
"""
