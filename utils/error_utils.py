"""
Standardized error handling for Pulse modules.
"""

class PulseError(Exception):
    """Base exception for Pulse errors."""
    pass

class DataValidationError(PulseError):
    """Raised when data validation fails."""
    pass
