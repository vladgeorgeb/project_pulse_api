from __future__ import annotations


class AppError(Exception):
    """Base application error."""


class AuthenticationError(AppError):
    """Raised when authentication fails."""


class AuthorizationError(AppError):
    """Raised when authorization fails."""


class ConflictError(AppError):
    """Raised when a resource already exists or conflicts with state."""


class NotFoundError(AppError):
    """Raised when a resource cannot be found."""


class ValidationError(AppError):
    """Raised when domain validation fails."""


class BusinessRuleError(AppError):
    """Raised when a valid request breaks a domain rule."""
