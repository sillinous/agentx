"""
Standardized API Responses - Consistent response format across all endpoints.

Provides:
- Standard error response format with error codes
- Pagination support for list endpoints
- Response envelope for consistent structure
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import math

T = TypeVar('T')


# ============ Error Response Models ============

class ErrorDetail(BaseModel):
    """Detail about a specific error."""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str = Field(..., description="Error type/category")
    message: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Machine-readable error code")
    details: List[ErrorDetail] = Field(default_factory=list, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")


# Error codes mapping
ERROR_CODES = {
    400: ("BAD_REQUEST", "Invalid request"),
    401: ("UNAUTHORIZED", "Authentication required"),
    403: ("FORBIDDEN", "Permission denied"),
    404: ("NOT_FOUND", "Resource not found"),
    409: ("CONFLICT", "Resource conflict"),
    422: ("VALIDATION_ERROR", "Validation failed"),
    429: ("RATE_LIMITED", "Too many requests"),
    500: ("INTERNAL_ERROR", "Internal server error"),
    502: ("BAD_GATEWAY", "Upstream service error"),
    503: ("SERVICE_UNAVAILABLE", "Service temporarily unavailable"),
}


def create_error_response(
    status_code: int,
    message: str,
    code: Optional[str] = None,
    details: Optional[List[Dict[str, Any]]] = None,
    request_id: Optional[str] = None,
) -> JSONResponse:
    """
    Create a standardized error response.

    Args:
        status_code: HTTP status code
        message: Human-readable error message
        code: Machine-readable error code (auto-generated if not provided)
        details: Additional error details
        request_id: Request ID for tracing

    Returns:
        JSONResponse with standardized error format
    """
    error_type, default_message = ERROR_CODES.get(status_code, ("UNKNOWN_ERROR", "Unknown error"))

    response_data = {
        "error": error_type,
        "message": message or default_message,
        "code": code or f"ERR_{status_code}",
        "details": [ErrorDetail(**d).model_dump() for d in (details or [])],
    }

    if request_id:
        response_data["request_id"] = request_id

    return JSONResponse(status_code=status_code, content=response_data)


class APIException(HTTPException):
    """
    Custom API exception with standardized error format.

    Usage:
        raise APIException(
            status_code=404,
            message="Agent not found",
            code="AGENT_NOT_FOUND",
            details=[{"field": "agent_id", "message": "No agent with this ID exists"}]
        )
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        code: Optional[str] = None,
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or []
        super().__init__(status_code=status_code, detail=message)


# ============ Pagination Models ============

class PaginationParams(BaseModel):
    """Pagination parameters extracted from request."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Alias for page_size."""
        return self.page_size


class PaginationMeta(BaseModel):
    """Pagination metadata for responses."""
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there's a next page")
    has_prev: bool = Field(..., description="Whether there's a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    data: List[T] = Field(..., description="List of items")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")


def paginate(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """
    Create a paginated response.

    Args:
        items: Items for current page (already sliced)
        total: Total number of items across all pages
        page: Current page number
        page_size: Items per page

    Returns:
        Dictionary with data and pagination metadata
    """
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0

    return {
        "data": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }
    }


def paginate_list(
    items: List[Any],
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """
    Paginate an in-memory list.

    Args:
        items: Full list of items
        page: Page number (1-indexed)
        page_size: Items per page

    Returns:
        Dictionary with paginated data and metadata
    """
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]

    return paginate(page_items, total, page, page_size)


# ============ Response Envelope ============

class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response envelope."""
    success: bool = True
    data: T
    message: Optional[str] = None


def success_response(
    data: Any,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a standard success response.

    Args:
        data: Response data
        message: Optional success message

    Returns:
        Dictionary with success response format
    """
    response = {"success": True, "data": data}
    if message:
        response["message"] = message
    return response
