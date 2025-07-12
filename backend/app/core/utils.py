"""
Utilities for the application
"""
import re

def clean_landing_ai_text(text: str) -> str:
    """
    Cleans the markdown text from Landing AI by removing non-educational content.
    - Removes HTML-style comments.
    - Removes 'Summary', 'photo', 'illustration' sections.
    - Removes figure/table captions that are descriptive.
    - Removes lines with just 'photo:' or 'illustration:'.
    - Normalizes whitespace.
    """
    if not isinstance(text, str):
        return ""

    # 1. Remove HTML comments
    text = re.sub(r'<!--(.*?)-->', '', text, flags=re.DOTALL)

    # 2. Remove entire sections like "Summary :", "photo:", "illustration:"
    # This pattern looks for the keyword, then everything until the next keyword
    # or a common text marker, trying to capture the whole block.
    text = re.sub(r'Summary\s?:.*?^(?=\S)', '', text, flags=re.DOTALL | re.MULTILINE)
    text = re.sub(r'photo\s?:.*?^(?=\S)', '', text, flags=re.DOTALL | re.MULTILINE)
    text = re.sub(r'illustration\s?:.*?^(?=\S)', '', text, flags=re.DOTALL | re.MULTILINE)

    # 3. Remove standalone lines that might be left
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Skip lines that are just keywords or formatting
        if line.strip().lower() in ['summary :', 'photo:', 'illustration:', '---']:
            continue
        # A more aggressive check for lines that look like auto-generated descriptions
        if re.match(r'^\s*•\s', line) and ('figure' in line.lower() or 'image' in line.lower() or 'scene' in line.lower()):
            continue
        cleaned_lines.append(line)

    text = '\n'.join(cleaned_lines)

    # 4. Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    return text 