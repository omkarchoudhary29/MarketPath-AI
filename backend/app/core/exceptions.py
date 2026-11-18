import uuid
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class MarketPathException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


class UnauthorizedException(MarketPathException):
    def __init__(self, message: str = "Authentication credentials were not provided or are invalid."):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenException(MarketPathException):
    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class NotFoundException(MarketPathException):
    def __init__(self, resource: str = "Resource", message: Optional[str] = None):
        super().__init__(
            code="NOT_FOUND",
            message=message or f"{resource} not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictException(MarketPathException):
    def __init__(self, message: str = "A resource conflict occurred."):
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


def format_error_response(
    code: str,
    message: str,
    status_code: int = 400,
    details: Optional[List[Dict[str, Any]]] = None,
    request_id: Optional[str] = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
                "request_id": request_id or f"req_{uuid.uuid4().hex[:12]}",
            }
        },
    )

