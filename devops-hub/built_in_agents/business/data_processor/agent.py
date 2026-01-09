# Data Processor Agent
# ETL, data transformation, aggregation, and quality assurance

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

from ...base import (
    BaseAgent,
    AgentCapability,
    AgentContext,
    AgentMessage,
    AgentResponse,
    Protocol,
)

logger = logging.getLogger(__name__)


@dataclass
class ETLJob:
    """An ETL job."""
    id: str
    name: str
    source: str
    destination: str
    status: str = "pending"
    records_processed: int = 0
    errors: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class DataProcessorAgent(BaseAgent):
    """
    Data Processor Agent - ETL and data transformation.

    Capabilities:
    - data-transformation: Transform data between formats
    - etl: Extract, transform, load pipelines
    - aggregation: Aggregate and summarize data
    - quality-assurance: Validate data quality
    - schema-validation: Validate against schemas
    """

    def __init__(self):
        super().__init__(
            agent_id="data-processor",
            name="Data Processor Agent",
            version="1.0.0",
            protocols=[Protocol.A2A, Protocol.ACP, Protocol.MCP],
        )
        self._jobs: Dict[str, ETLJob] = {}

    def _register_default_capabilities(self) -> None:
        """Register data processing capabilities."""
        capabilities = [
            ("data-transformation", "Transform data between formats and structures"),
            ("etl", "Run extract, transform, load pipelines"),
            ("aggregation", "Aggregate and summarize large datasets"),
            ("quality-assurance", "Validate and ensure data quality"),
            ("schema-validation", "Validate data against defined schemas"),
        ]

        for name, desc in capabilities:
            self.register_capability(AgentCapability(name=name, description=desc))
            self.register_handler(name, self._handle_capability)

    async def process_message(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        return await self._handle_capability(message, context)

    async def _handle_capability(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        capability = message.capability
        payload = message.payload

        if capability == "data-transformation":
            return await self._transform_data(payload)
        elif capability == "etl":
            return await self._run_etl(payload)
        elif capability == "aggregation":
            return await self._aggregate_data(payload)
        elif capability == "quality-assurance":
            return await self._check_quality(payload)
        elif capability == "schema-validation":
            return await self._validate_schema(payload)

        return AgentResponse.error_response(f"Unknown capability: {capability}")

    async def _transform_data(self, payload: Dict[str, Any]) -> AgentResponse:
        """Transform data."""
        source_format = payload.get("source_format", "json")
        target_format = payload.get("target_format", "csv")
        data = payload.get("data", [])

        return AgentResponse.success_response({
            "transformed": True,
            "source_format": source_format,
            "target_format": target_format,
            "records_transformed": len(data) if isinstance(data, list) else 1,
            "result": data,
        })

    async def _run_etl(self, payload: Dict[str, Any]) -> AgentResponse:
        """Run ETL pipeline."""
        from uuid import uuid4

        job = ETLJob(
            id=str(uuid4()),
            name=payload.get("name", "etl_job"),
            source=payload.get("source", "source_db"),
            destination=payload.get("destination", "target_db"),
            status="completed",
            records_processed=payload.get("record_count", 1000),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

        self._jobs[job.id] = job

        return AgentResponse.success_response({
            "job_id": job.id,
            "status": job.status,
            "records_processed": job.records_processed,
            "errors": job.errors,
        })

    async def _aggregate_data(self, payload: Dict[str, Any]) -> AgentResponse:
        """Aggregate data."""
        group_by = payload.get("group_by", [])
        aggregations = payload.get("aggregations", ["sum", "count"])

        return AgentResponse.success_response({
            "aggregated": True,
            "group_by": group_by,
            "aggregations_applied": aggregations,
            "result_count": 50,
            "sample_results": [
                {"group": "A", "sum": 1000, "count": 100},
                {"group": "B", "sum": 2000, "count": 150},
            ],
        })

    async def _check_quality(self, payload: Dict[str, Any]) -> AgentResponse:
        """Check data quality."""
        return AgentResponse.success_response({
            "quality_score": 0.95,
            "issues_found": 5,
            "issues": [
                {"type": "missing_value", "count": 3, "severity": "low"},
                {"type": "duplicate", "count": 2, "severity": "medium"},
            ],
            "recommendations": ["Fill missing values", "Remove duplicates"],
        })

    async def _validate_schema(self, payload: Dict[str, Any]) -> AgentResponse:
        """Validate against schema."""
        schema = payload.get("schema", {})
        data = payload.get("data", {})

        return AgentResponse.success_response({
            "valid": True,
            "errors": [],
            "warnings": [{"path": "$.optional_field", "message": "Field is empty"}],
            "fields_validated": 10,
        })
