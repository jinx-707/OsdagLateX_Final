"""Formatting utilities for numbers, units, etc."""


def format_number(value, decimals=2):
    """Format a number to a fixed number of decimal places."""
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)
