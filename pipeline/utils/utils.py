import re


def clean_text(self, text):
    # Convert to string if not already
    if not isinstance(text, str):
        text = str(text)
    # Replace non-breaking spaces, tabs, carriage returns, and form feeds with a space
    text = re.sub(r"[\xa0\t\r\f]", " ", text)
    # Replace multiple spaces (including those created by above) with a single space
    text = re.sub(r" +", " ", text)
    # Replace multiple newlines (with optional spaces/tabs in between) with a single newline
    text = re.sub(r" *\n+", "\n", text)
    # Remove leading/trailing whitespace and newlines
    text = text.strip()
    return text
