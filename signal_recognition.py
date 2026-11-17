"""
Local DOCX-based signal format recognition for the XAUUSD backtester.

Supported document layouts:
1. Ordinary paragraphs, with headings such as "Format 001".
2. Word tables, including one table per format.
3. Mixed paragraph/table documents.

This module identifies the closest documented format. It does NOT extract
prices or decide whether a signal is safe to trade; keep extraction and
price validation in the parser.

All processing is local. No external AI/API is used.
"""

from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from docx import Document

logger = logging.getLogger(__name__)

DEFAULT_DOCX_PATH = Path(__file__).resolve().parent / "signal_formats.docx"
DEFAULT_MATCH_THRESHOLD = 0.58

_FORMAT_CACHE: list[dict[str, Any]] = []
_FORMAT_CACHE_MTIME: int | None = None


def _clean_text(value: str) -> str:
    """Normalize common Telegram/Word whitespace without losing line breaks."""
    value = (value or "").replace("\u00a0", " ")
    value = value.replace("\u200b", "")
    value = value.replace("\ufeff", "")
    value = value.replace("\u2011", "-")
    value = value.replace("\u2013", "-")
    value = value.replace("\u2014", "-")
    value = value.replace("\ufe0f", "")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n[ \t]+", "\n", value)
    return value.strip()


def normalize_signal_text(text: str) -> str:
    """
    Produce a price-independent signature.

    Numeric values become NUM, while meaningful words such as BUY, SELL,
    LIMIT, SL, TP, NOW, ZONE, ENTRY and TARGET remain available for matching.
    """
    text = _clean_text(text).upper()

    # Normalize common instrument spellings.
    text = re.sub(r"\bXAU\s*/\s*USD\b", "XAUUSD", text)
    text = re.sub(r"\bXAUUUSD\b", "XAUUSD", text)
    text = re.sub(r"\bGOLD(?=(?:BUY|SELL)\b)", "GOLD ", text)

    # Normalize direction variants without erasing the direction.
    text = re.sub(r"\bBUYS\b", "BUY", text)
    text = re.sub(r"\bSHORT\b", "SELL", text)

    # Normalize TP labels and ordinal target words.
    text = re.sub(r"\bTARGETS?\b", "TP", text)
    text = re.sub(r"\bTAKE\s*PROFIT\b", "TP", text)
    text = re.sub(r"\bSTOP\s*LOSS\b", "SL", text)
    text = re.sub(r"\bFIRST\b", "1", text)
    text = re.sub(r"\bSECOND\b", "2", text)
    text = re.sub(r"\bTHIRD\b", "3", text)

    # Replace numbers (including decimals) with a common token.
    text = re.sub(r"(?<![A-Z])\d+(?:\.\d+)?", " NUM ", text)

    # Punctuation and emojis are separators, not format-defining content.
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _format_name_from_heading(text: str) -> str | None:
    match = re.match(r"^\s*FORMAT\s*0*(\d+)\s*$", text, re.I)
    if not match:
        return None
    return f"Format {int(match.group(1)):03d}"


def _read_paragraph_formats(doc) -> list[dict[str, str]]:
    """Read examples grouped under Format NNN paragraph headings."""
    formats: list[dict[str, str]] = []
    current_name: str | None = None
    current_lines: list[str] = []

    def flush():
        nonlocal current_name, current_lines
        example = _clean_text("\n".join(current_lines))
        if current_name and example:
            formats.append({
                "name": current_name,
                "example": example,
                "signature": normalize_signal_text(example),
                "source": "paragraph",
            })
        current_lines = []

    for paragraph in doc.paragraphs:
        line = _clean_text(paragraph.text)
        if not line:
            continue

        heading_name = _format_name_from_heading(line)
        if heading_name:
            flush()
            current_name = heading_name
        elif current_name:
            current_lines.append(line)

    flush()
    return formats


def _read_table_formats(doc) -> list[dict[str, str]]:
    """Read table-based examples; supports a Format heading in a table cell."""
    formats: list[dict[str, str]] = []

    for table_index, table in enumerate(doc.tables, start=1):
        lines: list[str] = []
        explicit_name: str | None = None

        for row in table.rows:
            for cell in row.cells:
                cell_text = _clean_text(cell.text)
                if not cell_text:
                    continue
                for line in cell_text.splitlines():
                    line = _clean_text(line)
                    if not line:
                        continue
                    heading_name = _format_name_from_heading(line)
                    if heading_name:
                        explicit_name = heading_name
                    else:
                        lines.append(line)

        example = _clean_text("\n".join(lines))
        if example:
            formats.append({
                "name": explicit_name or f"Table Format {table_index:03d}",
                "example": example,
                "signature": normalize_signal_text(example),
                "source": "table",
            })

    return formats


def load_signal_formats(
    docx_path: str | Path = DEFAULT_DOCX_PATH,
    force_reload: bool = False,
) -> list[dict[str, str]]:
    """
    Load and cache all documented examples.

    The file's modification time is checked on each call. A changed DOCX is
    reloaded automatically, so restarting the backtester is not required.
    """
    global _FORMAT_CACHE, _FORMAT_CACHE_MTIME

    path = Path(docx_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path

    if not path.exists():
        logger.warning("Signal format DOCX not found: %s", path)
        return []

    mtime = path.stat().st_mtime_ns
    if not force_reload and _FORMAT_CACHE_MTIME == mtime:
        return _FORMAT_CACHE

    try:
        doc = Document(path)
        paragraph_formats = _read_paragraph_formats(doc)
        table_formats = _read_table_formats(doc)

        # If the document contains paragraph examples, prefer those.
        # Tables are also retained, but duplicate examples are removed below.
        combined = paragraph_formats + table_formats

        unique: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for item in combined:
            key = (item["name"], item["signature"])
            if item["signature"] and key not in seen:
                seen.add(key)
                unique.append(item)

        # If there are no explicit Format headings or tables, use each
        # non-empty paragraph as a fallback example.
        if not unique:
            for index, paragraph in enumerate(doc.paragraphs, start=1):
                example = _clean_text(paragraph.text)
                if example and not _format_name_from_heading(example):
                    unique.append({
                        "name": f"Paragraph Format {index:03d}",
                        "example": example,
                        "signature": normalize_signal_text(example),
                        "source": "paragraph",
                    })

        _FORMAT_CACHE = unique
        _FORMAT_CACHE_MTIME = mtime
        logger.info("Loaded %d documented formats from %s", len(unique), path.name)
        return unique

    except Exception:
        logger.exception("Unable to load signal format DOCX: %s", path)
        return []


def _message_has_signal_fields(message: str) -> bool:
    text = _clean_text(message).upper()
    instrument = bool(re.search(r"\b(?:XAU\s*/?\s*USD|XAUUUSD|GOLD)\b", text))
    direction = bool(re.search(r"\b(?:BUY|BUYS|SELL|SHORT)\b", text))
    stop_loss = bool(re.search(r"\b(?:SL|STOP\s*LOSS|STOP)\b", text))
    take_profit = bool(re.search(
        r"\b(?:TP|TARGET|TARGETS|TAKE\s*PROFIT)\b", text
    ))
    return instrument and direction and stop_loss and take_profit


def _similarity(message_signature: str, example_signature: str) -> float:
    """Blend sequence similarity with token overlap for short Telegram texts."""
    sequence_score = SequenceMatcher(
        None, message_signature, example_signature
    ).ratio()

    message_tokens = set(message_signature.split())
    example_tokens = set(example_signature.split())

    if not message_tokens or not example_tokens:
        return sequence_score

    overlap = len(message_tokens & example_tokens) / len(
        message_tokens | example_tokens
    )
    return (0.70 * sequence_score) + (0.30 * overlap)


def match_signal_format(
    message: str,
    docx_path: str | Path = DEFAULT_DOCX_PATH,
    threshold: float = DEFAULT_MATCH_THRESHOLD,
) -> dict[str, Any] | None:
    """
    Return the best documented-format match or None.

    A match is informational only. The caller should still run the normal
    parser and validate direction, entry, SL and TP prices.
    """
    if not message or not _message_has_signal_fields(message):
        return None

    formats = load_signal_formats(docx_path)
    if not formats:
        logger.warning("No documented signal formats are available.")
        return None

    message_signature = normalize_signal_text(message)
    best: dict[str, Any] | None = None
    best_score = 0.0

    for item in formats:
        score = _similarity(message_signature, item["signature"])
        if score > best_score:
            best_score = score
            best = item

    if best is None or best_score < threshold:
        logger.warning(
            "Unmatched signal format | best score=%.3f | message=%r",
            best_score, message[:180]
        )
        return None

    result = {
        "name": best["name"],
        "score": round(best_score, 4),
        "example": best["example"],
        "source": best["source"],
    }
    logger.info(
        "Matched %s | score=%.3f | source=%s",
        result["name"], result["score"], result["source"]
    )
    return result


def clear_format_cache() -> None:
    """Force the next load/match call to reread the DOCX."""
    global _FORMAT_CACHE, _FORMAT_CACHE_MTIME
    _FORMAT_CACHE = []
    _FORMAT_CACHE_MTIME = None
