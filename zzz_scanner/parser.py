"""
Converts raw OCR text from a drive disc's detail view (the Routine Cleanup
popup or the Music Store left panel) into structured data matching the web
app's create schema.

The ZZZ detail view is conveniently labelled, so we anchor on those labels:

    <Set Name> [<slot>]        e.g. "Wuthering Salon [3]"
    Level / Lv. 00 / 15
    Main Stat
        <name>   <value>
    Sub-Stats
        <name>   <value>   [<name>  <value>]   (1 or 2 columns)
        ...
    Set Effect
        ...                (noise — ignored)

Output keys (matching the web app's artifact.create input):
    set, type (slot "1"-"6"), mainStat, numberOfSubstats, substats[]
plus debug fields prefixed with "_".
"""
import re
from rapidfuzz import process, fuzz

from config import ARTIFACT_SETS, MAIN_STATS_BY_SLOT

# ---------------------------------------------------------------------------
# Stat name -> web app value
# ---------------------------------------------------------------------------
# Stats are matched by their *name words* rather than name+value, because OCR
# frequently drops a value, or splits a two-word name around its value
# (e.g. "Anomaly" / "6" / "Proficiency"). Each entry is (word_sequence, base).
# Multi-word entries are listed first so they win over their single-word
# prefixes. For HP/ATK/DEF a trailing/adjacent "%" promotes the base to its
# percent form ("HP" -> "%HP"); the numeric value is otherwise discarded since
# the web app only stores which stats are present.

# Stat names that can be flat or percent — the "%" suffix promotes them.
_PCT_PROMOTABLE = {"HP", "ATK", "DEF"}

# Main stat vocabulary (slots 1-6).
_MAIN_WORDS = [
    (["anomaly", "proficiency"], "AP"),
    (["anomaly", "mastery"], "AM"),
    (["energy", "regen"], "ER"),
    (["pen", "ratio"], "PEN Ratio"),
    (["crit", "rate"], "Crit Rate"),
    (["crit", "dmg"], "Crit DMG"),
    (["physical", "dmg"], "Physical"),
    (["electric", "dmg"], "Electric"),
    (["ether", "dmg"], "Ether"),
    (["fire", "dmg"], "Fire"),
    (["ice", "dmg"], "Ice"),
    (["wind", "dmg"], "Wind"),
    (["impact"], "Impact"),
    (["hp"], "HP"),
    (["atk"], "ATK"),
    (["def"], "DEF"),
]

# Substat vocabulary (the web app's checkbox set).
# In a 2-column layout the wrapped "Anomaly Proficiency" label can be split by
# another substat wedged between its two words, so we also accept either word
# alone -> AP (safe: no other *substat* contains "anomaly" or "proficiency").
# Duplicates collapse during de-duplication.
_SUB_WORDS = [
    (["anomaly", "proficiency"], "AP"),
    (["crit", "rate"], "Crit Rate"),
    (["crit", "dmg"], "Crit DMG"),
    (["pen"], "PEN"),
    (["hp"], "HP"),
    (["atk"], "ATK"),
    (["def"], "DEF"),
    (["anomaly"], "AP"),
    (["proficiency"], "AP"),
]

_VALUE_RE = re.compile(r"^[+\-]?\d+(?:\.\d+)?%?$")

# Section header labels (matched fuzzily/loosely).
_ANCHOR_MAIN = "main stat"
_ANCHOR_SUB = "sub-stats"
_ANCHOR_SET_EFFECT = "set effect"


# ---------------------------------------------------------------------------
# Text cleanup
# ---------------------------------------------------------------------------
def _normalize(text: str) -> str:
    """Strip OCR artifacts: fullwidth chars, stray symbols, extra whitespace."""
    text = text.replace("（", "(").replace("）", ")").replace("　", " ")
    text = text.replace("［", "[").replace("］", "]")
    # Remove non-printable except newline
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _loose(s: str) -> str:
    """Lowercase alphanumerics only, for tolerant anchor matching."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


# ---------------------------------------------------------------------------
# Title: set name + slot
# ---------------------------------------------------------------------------
def _parse_title(lines: list[str]) -> tuple[str | None, str | None, int]:
    """
    Find the title line carrying the slot in brackets, e.g. "Wuthering Salon [3]".
    Returns (set_name, slot, line_index). The set/slot may span two OCR lines
    (the reference popup wraps "Wuthering\nSalon [2]"), so we also peek back.
    """
    for i, line in enumerate(lines):
        m = re.search(r"[\[(]\s*([1-6])\s*[\])]", line)
        if not m:
            continue
        slot = m.group(1)
        # Set name = everything before the bracket, possibly joined with the
        # previous line if the name wrapped.
        before = line[: m.start()].strip()
        candidate = before
        if i > 0 and not _looks_like_anchor(lines[i - 1]):
            candidate = f"{lines[i - 1].strip()} {before}".strip()
        set_name = _match_set(candidate) or _match_set(before)
        return set_name, slot, i
    # No bracketed slot found — still try to find a set name anywhere.
    for i, line in enumerate(lines):
        s = _match_set(line)
        if s:
            return s, None, i
    return None, None, -1


def _match_set(candidate: str) -> str | None:
    candidate = candidate.strip().strip(":").strip()
    if not candidate:
        return None
    match, score, _ = process.extractOne(
        candidate, ARTIFACT_SETS, scorer=fuzz.token_sort_ratio
    )
    return match if score >= 72 else None


def _looks_like_anchor(line: str) -> bool:
    l = _loose(line)
    return any(a in l for a in ("mainstat", "substats", "seteffect", "level", "lv"))


# ---------------------------------------------------------------------------
# Section splitting
# ---------------------------------------------------------------------------
def _find_anchor(lines: list[str], anchor: str, start: int = 0) -> int:
    target = _loose(anchor)
    for i in range(start, len(lines)):
        if target in _loose(lines[i]):
            return i
    return -1


def _split_sections(lines: list[str]) -> tuple[list[str], list[str]]:
    """Return (main_stat_lines, substat_lines) using the section labels."""
    main_idx = _find_anchor(lines, _ANCHOR_MAIN)
    sub_idx = _find_anchor(lines, _ANCHOR_SUB, max(main_idx, 0))
    set_idx = _find_anchor(lines, _ANCHOR_SET_EFFECT, max(sub_idx, 0))

    main_lines: list[str] = []
    sub_lines: list[str] = []
    if main_idx >= 0:
        end = sub_idx if sub_idx > main_idx else len(lines)
        main_lines = lines[main_idx + 1: end]
    if sub_idx >= 0:
        end = set_idx if set_idx > sub_idx else len(lines)
        sub_lines = lines[sub_idx + 1: end]
    return main_lines, sub_lines


# ---------------------------------------------------------------------------
# Stat extraction (token matcher)
# ---------------------------------------------------------------------------
def _is_value(tok: str) -> bool:
    return bool(_VALUE_RE.match(tok))


def _norm_word(tok: str) -> str:
    return re.sub(r"[^a-z]", "", tok.lower())


def _word_eq(tok: str, word: str) -> bool:
    n = _norm_word(tok)
    if not n:
        return False
    return n == word or fuzz.ratio(n, word) >= 82


def _match_seq(toks: list[str], start: int, words: list[str]):
    """
    Try to match a name word-sequence beginning at `start`, tolerating value
    tokens that OCR may have wedged BETWEEN the words. Returns (is_pct,
    next_index) on success, else None.
    """
    j = start
    is_pct = False
    for wi, w in enumerate(words):
        if wi > 0:  # skip values interleaved between name words
            while j < len(toks) and _is_value(toks[j]):
                if "%" in toks[j]:
                    is_pct = True
                j += 1
        if j >= len(toks) or not _word_eq(toks[j], w):
            return None
        if "%" in toks[j]:  # value merged into the name token, e.g. "HP3%"
            is_pct = True
        j += 1
    # Consume the stat's own trailing value (if present) to read its "%".
    if j < len(toks) and _is_value(toks[j]):
        if "%" in toks[j]:
            is_pct = True
        j += 1
    return is_pct, j


def _extract_stats(lines: list[str], table: list) -> list[str]:
    """Return web-app stat values found in a section, in order."""
    text = " ".join(l.strip() for l in lines if l.strip())
    toks = text.split()
    out: list[str] = []
    i = 0
    while i < len(toks):
        if _is_value(toks[i]):
            i += 1
            continue
        for words, base in table:
            res = _match_seq(toks, i, words)
            if res is not None:
                is_pct, nxt = res
                value = f"%{base}" if (base in _PCT_PROMOTABLE and is_pct) else base
                out.append(value)
                i = nxt
                break
        else:
            i += 1
    return out


def _parse_main_stat(main_lines: list[str], slot: str | None) -> str | None:
    entries = _extract_stats(main_lines, _MAIN_WORDS)
    if not entries:
        return None
    # Prefer a stat that's valid for the known slot; else take the first read.
    if slot and slot in MAIN_STATS_BY_SLOT:
        for stat in entries:
            if stat in MAIN_STATS_BY_SLOT[slot]:
                return stat
    return entries[0]


def _parse_substats(sub_lines: list[str]) -> list[str]:
    substats: list[str] = []
    for stat in _extract_stats(sub_lines, _SUB_WORDS):
        if stat not in substats:
            substats.append(stat)
    return substats


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def parse_popup_text(raw_text: str) -> dict:
    """
    Convert raw OCR text from a disc's detail view into a dict ready for the
    web app's create/import endpoint.

    Returned keys:
      set, type, mainStat, numberOfSubstats, substats,
      score, source (filled in later by the UI), plus _raw/_lines/_ok debug.
    """
    text = _normalize(raw_text)
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    set_name, slot, _ = _parse_title(lines)
    main_lines, sub_lines = _split_sections(lines)
    main_stat = _parse_main_stat(main_lines, slot)
    substats = _parse_substats(sub_lines)

    return {
        "set": set_name,
        "type": slot,
        "mainStat": main_stat,
        "numberOfSubstats": len(substats),
        "substats": substats,
        # Debug fields
        "_raw": raw_text,
        "_lines": lines,
        "_ok": {
            "set": set_name is not None,
            "type": slot is not None,
            "mainStat": main_stat is not None,
            "substats": len(substats) in (3, 4),
        },
    }
