import os
import re
from dataclasses import dataclass

NOTE_NAMES = ("DO", "DO#", "RE", "RE#", "MI", "FA", "FA#", "SOL", "SOL#", "LA", "LA#", "SI")
NATURAL_SEMITONES = {"DO": 0, "RE": 2, "MI": 4, "FA": 5, "SOL": 7, "LA": 9, "SI": 11}
NOTE_PATTERN = re.compile(
    r"(?i)(?<![a-z])(do|re|mi|fa|sol|la|si)(#|b)?([0-8])(?![0-9])"
)


@dataclass(frozen=True)
class ParsedNote:
    name: str
    octave: int
    midi_number: int
    start: int
    end: int

    @property
    def display_name(self):
        return f"{self.name}{self.octave}"


def find_note(value):
    """Find a note token in a filename and normalize it to a sharp spelling."""
    if not value:
        return None
    raw_str = str(value).replace("\\", "/").rsplit("/", 1)[-1]
    match = NOTE_PATTERN.search(raw_str)
    if not match:
        return None

    natural = match.group(1).upper()
    accidental = match.group(2)
    octave = int(match.group(3))
    midi = (octave + 1) * 12 + NATURAL_SEMITONES[natural]
    if accidental == "#":
        midi += 1
    elif accidental and accidental.casefold() == "b":
        midi -= 1

    canonical_octave = midi // 12 - 1
    canonical_name = NOTE_NAMES[midi % 12]
    return ParsedNote(
        name=canonical_name,
        octave=canonical_octave,
        midi_number=midi,
        start=match.start(),
        end=match.end(),
    )
