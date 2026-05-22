import re

# Matches <script ...>, </script>, inline event handlers (onclick=, onload=, etc.)
# and javascript: URI schemes — stripped from any free-text field before persistence.
_UNSAFE_HTML_RE = re.compile(
    r"<script[\s\S]*?>[\s\S]*?</script>|"  # full <script> blocks
    r"<[^>]*?\bon\w+\s*=|"                 # inline event handlers (onclick=, onload=…)
    r"javascript\s*:",                      # javascript: URI scheme
    re.IGNORECASE,
)


def _strip_unsafe(value: str) -> str:
    """Remove null bytes and obvious script-injection patterns from a string."""
    # Strip null bytes (can confuse parsers / loggers)
    value = value.replace("\x00", "")
    # Strip dangerous HTML patterns
    value = _UNSAFE_HTML_RE.sub("", value)
    return value


def normalize_phone(phone: str) -> str:
    normalized = phone.strip().replace(" ", "")
    if not re.fullmatch(r"\d{10,15}", normalized):
        raise ValueError("Invalid phone number format")
    return normalized


def strip_text(value: str) -> str:
    return _strip_unsafe(value.strip())


def strip_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = _strip_unsafe(value.strip())
    return stripped or None
