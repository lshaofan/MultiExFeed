class APIError(Exception):
    """Exception raised for API errors."""
    pass

class NetworkError(Exception):
    """Exception raised for network-related errors."""
    pass

class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass
