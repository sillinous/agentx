"""
Human-in-the-Loop (HITL) Service

Manages requests from AI agents for human actions.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4
import json
import logging

from service.hitl_schema import (
    HumanActionRequest,
    CREATE_HITL_REQUESTS_TABLE,
)
from core.database import get_database

logger = logging.getLogger(__name__)


class HITLService:
    """Service for managing human-in-the-loop requests."""

    def __init__(self):
        self.db = get_database()
        self._initialize_db()

    def _initialize_db(self):
        """Create HITL tables if they don't exist."""
        try:
            # Get connection and execute the schema
            conn = self.db._get_connection()
            conn.executescript(CREATE_HITL_REQUESTS_TABLE)
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize HITL database: {e}")

    def create_request(
        self,
        agent_id: str,
        request_type: str,
        title: str,
        description: str,
        required_fields: Dict[str, str] = None,
        priority: str = "medium",
        workflow_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> HumanActionRequest:
        """Create a new human action request."""
        request_id = f"har_{uuid4().hex[:12]}"
        now = datetime.now().isoformat()

        request = HumanActionRequest(
            id=request_id,
            request_type=request_type,
            title=title,
            description=description,
            agent_id=agent_id,
            priority=priority,
            status="pending",
            workflow_id=workflow_id,
            context=context or {},
            required_fields=required_fields or {},
            created_at=now,
        )

        # Save to database
        self.db.execute(
            """
            INSERT INTO hitl_requests (
                id, request_type, title, description, agent_id, priority, status,
                workflow_id, context, required_fields, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request.id,
                request.request_type,
                request.title,
                request.description,
                request.agent_id,
                request.priority,
                request.status,
                request.workflow_id,
                json.dumps(request.context),
                json.dumps(request.required_fields),
                request.created_at,
            ),
        )

        logger.info(f"Created HITL request {request.id} for agent {agent_id}")
        return request

    def get_request(self, request_id: str) -> Optional[HumanActionRequest]:
        """Get a request by ID."""
        row = self.db.fetch_one(
            "SELECT * FROM hitl_requests WHERE id = ?", (request_id,)
        )
        if not row:
            return None
        return self._dict_to_request(row)

    def list_requests(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[HumanActionRequest]:
        """List requests with optional filters."""
        query = "SELECT * FROM hitl_requests WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = self.db.fetch_all(query, tuple(params))
        return [self._dict_to_request(row) for row in rows]

    def fulfill_request(
        self,
        request_id: str,
        fulfilled_by: str,
        response_data: Dict[str, Any],
        notes: Optional[str] = None,
    ) -> Optional[HumanActionRequest]:
        """Fulfill a request with human-provided data."""
        request = self.get_request(request_id)
        if not request:
            return None

        if request.status not in ["pending", "in_review"]:
            raise ValueError(f"Request {request_id} cannot be fulfilled (status: {request.status})")

        now = datetime.now().isoformat()

        self.db.execute(
            """
            UPDATE hitl_requests
            SET status = ?, response_data = ?, fulfilled_at = ?, fulfilled_by = ?, notes = ?
            WHERE id = ?
            """,
            (
                "fulfilled",
                json.dumps(response_data),
                now,
                fulfilled_by,
                notes,
                request_id,
            ),
        )

        logger.info(f"Fulfilled HITL request {request_id} by {fulfilled_by}")
        return self.get_request(request_id)

    def reject_request(
        self,
        request_id: str,
        rejected_by: str,
        reason: str,
    ) -> Optional[HumanActionRequest]:
        """Reject a request."""
        request = self.get_request(request_id)
        if not request:
            return None

        if request.status not in ["pending", "in_review"]:
            raise ValueError(f"Request {request_id} cannot be rejected (status: {request.status})")

        now = datetime.now().isoformat()

        self.db.execute(
            """
            UPDATE hitl_requests
            SET status = ?, fulfilled_at = ?, fulfilled_by = ?, notes = ?
            WHERE id = ?
            """,
            (
                "rejected",
                now,
                rejected_by,
                reason,
                request_id,
            ),
        )

        logger.info(f"Rejected HITL request {request_id} by {rejected_by}: {reason}")
        return self.get_request(request_id)

    def get_statistics(self) -> Dict[str, Any]:
        """Get HITL request statistics."""
        total_row = self.db.fetch_one("SELECT COUNT(*) as count FROM hitl_requests")
        total = total_row['count'] if total_row else 0

        # By status
        status_rows = self.db.fetch_all(
            "SELECT status, COUNT(*) as count FROM hitl_requests GROUP BY status"
        )
        by_status = {row['status']: row['count'] for row in status_rows}

        # By priority
        priority_rows = self.db.fetch_all(
            "SELECT priority, COUNT(*) as count FROM hitl_requests GROUP BY priority"
        )
        by_priority = {row['priority']: row['count'] for row in priority_rows}

        # By type
        type_rows = self.db.fetch_all(
            "SELECT request_type, COUNT(*) as count FROM hitl_requests GROUP BY request_type"
        )
        by_type = {row['request_type']: row['count'] for row in type_rows}

        # Average response time (for fulfilled requests)
        avg_response_row = self.db.fetch_one(
            """
            SELECT AVG(
                (julianday(fulfilled_at) - julianday(created_at)) * 24
            ) as avg_hours
            FROM hitl_requests
            WHERE status = 'fulfilled' AND fulfilled_at IS NOT NULL
            """
        )
        avg_response_hours = avg_response_row['avg_hours'] if avg_response_row and avg_response_row['avg_hours'] else 0.0

        return {
            "total_requests": total,
            "pending_requests": by_status.get("pending", 0) + by_status.get("in_review", 0),
            "by_status": by_status,
            "by_priority": by_priority,
            "by_type": by_type,
            "average_response_time_hours": round(avg_response_hours, 2),
        }

    def _dict_to_request(self, row: Dict[str, Any]) -> HumanActionRequest:
        """Convert database row dict to HumanActionRequest object."""
        return HumanActionRequest(
            id=row['id'],
            request_type=row['request_type'],
            title=row['title'],
            description=row['description'],
            agent_id=row['agent_id'],
            priority=row['priority'],
            status=row['status'],
            workflow_id=row.get('workflow_id'),
            context=json.loads(row['context']) if row.get('context') else {},
            required_fields=json.loads(row['required_fields']) if row.get('required_fields') else {},
            response_data=json.loads(row['response_data']) if row.get('response_data') else None,
            created_at=row['created_at'],
            fulfilled_at=row.get('fulfilled_at'),
            fulfilled_by=row.get('fulfilled_by'),
            notes=row.get('notes'),
        )


# Singleton instance
_hitl_service: Optional[HITLService] = None


def get_hitl_service() -> HITLService:
    """Get the singleton HITL service instance."""
    global _hitl_service
    if _hitl_service is None:
        _hitl_service = HITLService()
    return _hitl_service
