"""LaTeX escaping utilities."""


# Replacement table: (character, escaped form)
# Order matters: backslash must be replaced first.
_REPLACEMENTS = [
    ('\\', r'\textbackslash{}'),
    ('&', r'\&'),
    ('%', r'\%'),
    ('$', r'\$'),
    ('#', r'\#'),
    ('_', r'\_'),
    ('{', r'\{'),
    ('}', r'\}'),
    ('~', r'\textasciitilde{}'),
    ('^', r'\textasciicircum{}'),
]

_PLACEHOLDER = '\x00'


def escape_latex(text: str) -> str:
    """
    Escape LaTeX special characters in plain text.

    Uses a two-pass placeholder approach to prevent replacement strings
    (e.g. ``\\textbackslash{}``) from being re-processed by later
    replacements (the ``{`` and ``}`` in the replacement would otherwise
    get escaped).

    Args:
        text: Input string to escape.

    Returns:
        Escaped string safe for LaTeX.

    Raises:
        TypeError: If text is None.
    """
    if text is None:
        raise TypeError("escape_latex() expects a string, got None")

    # Pass 1: replace each special char with a unique placeholder
    result = text
    for i, (char, _) in enumerate(_REPLACEMENTS):
        result = result.replace(char, f'{_PLACEHOLDER}{i}')

    # Pass 2: replace placeholders with final LaTeX replacements
    for i, (_, escaped) in enumerate(_REPLACEMENTS):
        result = result.replace(f'{_PLACEHOLDER}{i}', escaped)

    return result
