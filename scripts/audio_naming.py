"""Shared note-name parsing for SEMIMUS audio scripts."""
import os
import re


RE_ES = re.compile(r"(do|re|mi|fa|sol|la|si)(#|b)?[^\d]*(\d)", re.IGNORECASE)
RE_EN = re.compile(r"([a-g])(#|b)?[^\d]*(\d)", re.IGNORECASE)

ES_TO_NOTE = {
    "do": "DO", "do#": "DO#", "re": "RE", "re#": "RE#",
    "mi": "MI", "fa": "FA", "fa#": "FA#", "sol": "SOL",
    "sol#": "SOL#", "la": "LA", "la#": "LA#", "si": "SI",
}
EN_TO_NOTE = {
    "c": "DO", "c#": "DO#", "db": "DO#", "d": "RE", "d#": "RE#",
    "eb": "RE#", "e": "MI", "f": "FA", "f#": "FA#", "g": "SOL",
    "g#": "SOL#", "a": "LA", "a#": "LA#", "b": "SI",
}


def parse_note(filename):
    """Return (catalog note, octave), tolerating prefixes and extra punctuation."""
    name = os.path.splitext(os.path.basename(filename))[0].lower()
    match = RE_ES.search(name)
    if match:
        token = match.group(1) + (match.group(2) or "")
        return ES_TO_NOTE.get(token), int(match.group(3))
    match = RE_EN.search(name)
    if match:
        token = match.group(1) + (match.group(2) or "")
        return EN_TO_NOTE.get(token), int(match.group(3))
    return None, None


if __name__ == "__main__":
    cases = {
        "8..la3.wma": ("LA", 3),
        "9..la#3.wma": ("LA#", 3),
        "31.si4.wma": ("SI", 4),
        "30. la#4.wma": ("LA#", 4),
    }
    for filename, expected in cases.items():
        assert parse_note(filename) == expected, (filename, parse_note(filename))
    print(f"parse_note: {len(cases)} casos OK")
