"""Helper Utilities"""


def validate_identifier(identifier):
    """Validate identifier"""
    if not identifier or not isinstance(identifier, str):
        return False
    return len(identifier) > 0 and len(identifier) <= 255


def validate_tokens(tokens):
    """Validate token count"""
    if not isinstance(tokens, int):
        return False
    return tokens > 0


def format_response(data):
    """Format API response"""
    return {
        "data": data,
        "timestamp": __import__('time').time()
    }
