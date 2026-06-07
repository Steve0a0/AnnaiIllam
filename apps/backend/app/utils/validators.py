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
    """Normalize a phone number to E.164 format (+91XXXXXXXXXX for Indian numbers).

    Accepts:
      9876543210       → +919876543210
      +919876543210    → +919876543210
      919876543210     → +919876543210
      09876543210      → +919876543210
    """
    normalized = phone.strip().replace(" ", "").replace("-", "")

    # Already E.164: +91 followed by exactly 10 digits
    if re.fullmatch(r"\+91\d{10}", normalized):
        return normalized

    # Country code without +: 91 followed by exactly 10 digits
    if re.fullmatch(r"91\d{10}", normalized):
        return "+" + normalized

    # Leading zero: 0 followed by exactly 10 digits
    if re.fullmatch(r"0\d{10}", normalized):
        return "+91" + normalized[1:]

    # Bare 10 digits (most common from mobile app)
    if re.fullmatch(r"\d{10}", normalized):
        return "+91" + normalized

    # Generic E.164 for non-Indian numbers (pass through)
    if re.fullmatch(r"\+\d{7,15}", normalized):
        return normalized

    raise ValueError(f"Invalid phone number format: {phone!r}")


def strip_text(value: str) -> str:
    return _strip_unsafe(value.strip())


def strip_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = _strip_unsafe(value.strip())
    return stripped or None
