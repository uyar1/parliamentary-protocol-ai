import unicodedata

def is_latin_extended(char: chr):
    """
    Überprüft, ob ein Zeichen im Bereich der lateinischen Unicode-Blöcke liegt.
    Unicode-Bereiche der lateinischen Erweiterungen:
        - Basic Latin: U+0000–U+007F
        - Latin-1 Supplement: U+0080–U+00FF
        - Latin Extended-A: U+0100–U+017F
        - Latin Extended-B: U+0180–U+024F
        - Latin Extended Additional: U+1E00–U+1EFF
    """
    return (
            ('\u0000' <= char <= '\u007F') or  # Basic Latin
            ('\u0080' <= char <= '\u00FF') or  # Latin-1 Supplement
            ('\u0100' <= char <= '\u017F') or  # Latin Extended-A
            ('\u0180' <= char <= '\u024F') or  # Latin Extended-B
            ('\u1E00' <= char <= '\u1EFF')    # Latin Extended Additional
    )

def filter_latin_chars(text: str):
    """
    Nur lateinische Zeichen aus den entsprechenden Unicode-Blöcken behalten
    """
    return ''.join(char for char in text if is_latin_extended(char))
