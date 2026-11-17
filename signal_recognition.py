"""DOCX-driven XAUUSD signal recognition and parsing.

The Word document is the editable library of example messages and shared rule
families. This module loads it locally, detects file changes, matches examples,
and extracts the fields used by the existing backtester. No external AI/API is
used. A new format using the documented rule families can be added to the DOCX
without changing Python code.
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
DEFAULT_MATCH_THRESHOLD = 0.45
_FORMAT_CACHE: list[dict[str, Any]] = []
_FORMAT_CACHE_MTIME: int | None = None
_CONFIG_CACHE: dict[str, Any] = {}

_SUPERSCRIPT_DIGITS = str.maketrans("¹²³⁴⁵⁶", "123456")
_CIRCLED_DIGITS = str.maketrans("①②③④⑤⑥", "123456")


def _clean_text(value: str) -> str:
    value = (value or "").replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    value = value.translate(_SUPERSCRIPT_DIGITS).translate(_CIRCLED_DIGITS)
    value = value.replace("\ufe0f", "").replace("\u20e3", "")
    return re.sub(r"[ \t]+", " ", value).strip()


def normalize_signal_text(text: str) -> str:
    text = _clean_text(text).upper()
    text = re.sub(r"XAU\s*/\s*USD|XAU\s+USD|XAUUUSD", "XAUUSD", text)
    text = re.sub(r"\bBUYS\b", "BUY", text)
    text = re.sub(r"\bSHORT\b", "SELL", text)
    text = re.sub(r"\bTARGETS?\b|\bTAKE\s*PROFIT\b", "TP", text)
    text = re.sub(r"\bSTOP\s*LOSS\b|\bSTOPLOSS\b", "SL", text)
    text = re.sub(r"\d+(?:\.\d+)?", " NUM ", text)
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _format_name_from_heading(text: str) -> str | None:
    m = re.match(r"^\s*FORMAT\s*0*(\d+)\s*$", text, re.I)
    return f"Format {int(m.group(1)):03d}" if m else None


def _read_docx(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    doc = Document(path)
    examples: list[dict[str, Any]] = []
    current_name: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_lines
        example = "\n".join(x for x in current_lines if x).strip()
        if current_name and example:
            examples.append({"name": current_name, "example": example,
                             "signature": normalize_signal_text(example), "source": "paragraph"})
        current_lines = []

    for p in doc.paragraphs:
        line = _clean_text(p.text)
        if not line:
            continue
        name = _format_name_from_heading(line)
        if name:
            flush()
            current_name = name
        elif current_name:
            current_lines.append(line)
    flush()

    # Table layouts are supported too. The first table describes shared
    # extraction rule families; the second defines output keys; the third
    # contains exceptional validation requirements. They are loaded as config.
    config: dict[str, Any] = {"rule_families": [], "output_contract": {}, "special_notes": {}}
    for ti, table in enumerate(doc.tables):
        rows = [[_clean_text(c.text) for c in row.cells] for row in table.rows]
        if ti == 0:
            config["rule_families"] = [
                {"family": row[0], "forms": row[1], "behavior": row[2]}
                for row in rows[1:] if len(row) >= 3 and row[0]
            ]
        elif ti == 1:
            config["output_contract"] = {
                row[0]: row[1] for row in rows[1:] if len(row) >= 2 and row[0]
            }
        elif ti == 2:
            config["special_notes"] = {
                row[0]: row[1] for row in rows[1:] if len(row) >= 2 and row[0]
            }

    if not examples:
        # Also support one-format-per-table documents.
        for ti, table in enumerate(doc.tables, 1):
            lines = [_clean_text(c.text) for row in table.rows for c in row.cells if _clean_text(c.text)]
            if lines:
                name = next((_format_name_from_heading(x) for x in lines if _format_name_from_heading(x)), f"Table Format {ti:03d}")
                example = "\n".join(x for x in lines if not _format_name_from_heading(x))
                if example:
                    examples.append({"name": name, "example": example,
                                     "signature": normalize_signal_text(example), "source": "table"})
    return examples, config


def load_signal_formats(docx_path: str | Path = DEFAULT_DOCX_PATH, force_reload: bool = False) -> list[dict[str, Any]]:
    global _FORMAT_CACHE, _FORMAT_CACHE_MTIME, _CONFIG_CACHE
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
        examples, config = _read_docx(path)
        unique, seen = [], set()
        for item in examples:
            key = (item["name"], item["signature"])
            if item["signature"] and key not in seen:
                seen.add(key)
                unique.append(item)
        _FORMAT_CACHE, _CONFIG_CACHE, _FORMAT_CACHE_MTIME = unique, config, mtime
        logger.info("Loaded %d signal examples and %d rule families from %s",
                    len(unique), len(config.get("rule_families", [])), path.name)
        return _FORMAT_CACHE
    except Exception:
        logger.exception("Unable to load signal format DOCX: %s", path)
        return []


def load_signal_config(docx_path: str | Path = DEFAULT_DOCX_PATH) -> dict[str, Any]:
    load_signal_formats(docx_path)
    return _CONFIG_CACHE


def _similarity(a: str, b: str) -> float:
    seq = SequenceMatcher(None, a, b).ratio()
    aa, bb = set(a.split()), set(b.split())
    overlap = len(aa & bb) / len(aa | bb) if aa or bb else 0.0
    return 0.70 * seq + 0.30 * overlap


def match_signal_format(message: str, docx_path: str | Path = DEFAULT_DOCX_PATH,
                        threshold: float = DEFAULT_MATCH_THRESHOLD) -> dict[str, Any] | None:
    if not message:
        return None
    formats = load_signal_formats(docx_path)
    if not formats:
        return None
    sig = normalize_signal_text(message)
    best = max(formats, key=lambda x: _similarity(sig, x["signature"]), default=None)
    score = _similarity(sig, best["signature"]) if best else 0.0
    if best is None or score < threshold:
        return None
    return {"name": best["name"], "score": round(score, 4),
            "example": best["example"], "source": best["source"]}


def _numbers(text: str) -> list[float]:
    return [float(x.replace(",", "")) for x in re.findall(r"(?<!\d)\d{3,5}(?:\.\d+)?(?!\d|\.\d)", text)]


def _expand_range(a: str, b: str) -> tuple[float, float]:
    av = float(a)
    if "." not in a and "." not in b and len(b) < len(a):
        scale = 10 ** len(b)
        candidate = (int(a) // scale) * scale + int(b)
        if candidate - int(a) < -(scale / 2):
            candidate += scale
        elif candidate - int(a) > scale / 2:
            candidate -= scale
        bv = float(candidate)
    else:
        bv = float(b)
    return min(av, bv), max(av, bv)


def _entry_from_header(text: str, side: str) -> tuple[float | None, float | None, float | None, str]:
    # Ignore everything from the first SL/TP label onward; entry lives in header.
    header = re.split(r"\b(?:SL|STOP\s*LOSS|STOPLOSS|TP\s*\d*|TARGET\s*\d*)\b", text, maxsplit=1, flags=re.I)[0]
    # Prefer explicit entry/price-now/order-type labels.
    explicit = re.search(r"\b(?:ENTRY(?:\s+PRICE)?|PRICE\s+NOW|BUY\s+STOP|SELL\s+STOP|BUY\s+LIMIT|SELL\s+LIMIT|BUY\s+NOW|SELL\s+NOW)\b[^\d\n]{0,20}", header, re.I)
    order = "UNKNOWN"
    if re.search(r"\b(?:BUY|SELL)\s+STOP\b", header, re.I):
        order = "STOP"
    elif re.search(r"\b(?:BUY|SELL)\s+LIMIT\b|\bLIMIT\b", header, re.I):
        order = "LIMIT"
    elif re.search(r"\bNOW\b", header, re.I):
        order = "MARKET"
    elif explicit:
        order = "MARKET"

    # Numbered range and common separators; handle 4134_37 and 3277.3275.
    range_match = re.search(r"(?<!\d)(\d{3,5}(?:\.\d+)?)\s*(?:-|–|—|/|_|:|\.\s*\.)\s*(\d{1,5}(?:\.\d+)?)(?!\d)", header)
    if not range_match:
        compact = re.search(r"(?<!\d)(\d{4})\.(\d{4})(?!\d)", header)
        if compact:
            range_match = compact
    if range_match:
        lo, hi = _expand_range(range_match.group(1), range_match.group(2))
        chosen = lo if side == "BUY" else hi
        return chosen, lo, hi, order if order != "UNKNOWN" else "MARKET"

    # Remove years/other incidental small numbers and use the first price in header.
    candidates = _numbers(header)
    if candidates:
        value = candidates[-1] if explicit and len(candidates) > 1 else candidates[0]
        return value, value, value, order if order != "UNKNOWN" else "MARKET"
    return None, None, None, order


def _extract_sl(text: str) -> tuple[float | None, list[str]]:
    matches = list(re.finditer(r"\b(?:STOP\s*LOSS|STOPLOSS|SL|STOP)\b\s*[:：=@-]?\s*[^\d\n]{0,12}(\d{3,5}(?:\.\d+)?)", text, re.I))
    # In "Buy Stop: 4040.5", STOP labels the pending order, not the stop loss.
    matches = [m for m in matches if not re.search(r"\b(?:BUY|SELL)\s+$", text[max(0, m.start()-12):m.start()], re.I)]
    values = [float(m.group(1)) for m in matches]
    warnings = []
    if len(values) > 1:
        warnings.append(f"Multiple stop-loss values found: {values}")
    return (values[0] if values else None), warnings


def _extract_targets(text: str) -> tuple[list[dict[str, Any]], list[str]]:
    # Superscript ordinals are normalized before parsing. Target labels include
    # TP, TP1..6, TARGET, TAKE PROFIT and ordinal words.
    label = re.compile(r"\b(?:TP|TARGET|TAKE\s*PROFIT)(?:\s*[1-6])?\b|\b(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH)\s+(?:TP|TARGET)\b", re.I)
    matches = list(label.finditer(text))
    results: list[dict[str, Any]] = []
    warnings: list[str] = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        # A SL label terminates a target's value region.
        region = re.split(r"\b(?:SL|STOP\s*LOSS|STOPLOSS)\b", text[m.end():end], maxsplit=1, flags=re.I)[0]
        if re.search(r"(?<![A-Z])(?:OPEN|RUNNER)\b", region, re.I) and not re.search(r"\d{3,5}(?:\.\d+)?", region):
            results.append({"price": None, "status": "open", "alternatives": []})
            continue
        # Capture prices after label, including a pair separated by slash.
        vals = _numbers(region)
        if not vals:
            continue
        alternatives = vals if len(vals) > 1 else []
        status = "alternative" if len(vals) > 1 else "numeric"
        results.append({"price": vals[0], "status": status, "alternatives": alternatives})
        if len(vals) > 1:
            warnings.append(f"Multiple/alternative values for one target label: {vals}")
        if re.search(r"(?<![A-Z])(?:OPEN|RUNNER)\b", region, re.I):
            results[-1]["status"] = "open"
    return results, warnings


def parse_signal(message: str, docx_path: str | Path = DEFAULT_DOCX_PATH,
                 match_threshold: float = DEFAULT_MATCH_THRESHOLD) -> dict[str, Any] | None:
    if not message:
        return None
    text = _clean_text(message).replace("\r", "\n")
    text = re.sub(r"XAU\s*/\s*USD|XAU\s+USD|XAUUUSD", "XAUUSD", text, flags=re.I)
    text = re.sub(r"\bGOLD(?=(?:BUY|SELL)\b)", "GOLD ", text, flags=re.I)
    if not re.search(r"\b(?:XAUUSD|GOLD)\b", text, re.I):
        return None
    direction_hits = re.findall(r"\b(BUY|BUYS|SELL|SHORT)\b", text, re.I)
    sides = {"SELL" if x.upper() == "SHORT" else "BUY" if x.upper() in ("BUY", "BUYS") else "SELL" for x in direction_hits}
    if len(sides) != 1:
        return None
    side = sides.pop()
    matched = match_signal_format(text, docx_path, match_threshold)
    entry, entry_low, entry_high, order_type = _entry_from_header(text, side)
    sl, warnings = _extract_sl(text)
    targets, target_warnings = _extract_targets(text)
    warnings.extend(target_warnings)
    if entry is None or sl is None or not targets:
        return None
    # Keep all target states in the rich result; expose numeric targets in the
    # legacy six-column contract. Do not silently correct suspicious prices.
    tp_values = [x["price"] for x in targets if x.get("price") is not None][:6]
    if len(targets) > 6:
        warnings.append("More than six targets found; legacy backtester stores the first six numeric targets")
    if side == "BUY":
        if sl >= entry:
            warnings.append(f"BUY stop loss {sl} is not below entry {entry}")
        for x in targets:
            if x.get("price") is not None and x["price"] <= entry:
                warnings.append(f"BUY target {x['price']} is not above entry {entry}")
    else:
        if sl <= entry:
            warnings.append(f"SELL stop loss {sl} is not above entry {entry}")
        for x in targets:
            if x.get("price") is not None and x["price"] >= entry:
                warnings.append(f"SELL target {x['price']} is not below entry {entry}")
    if warnings:
        logger.warning("Signal parse warnings (%s): %s", matched["name"] if matched else "unmatched", "; ".join(warnings))
    return {"instrument": "XAUUSD", "side": side, "order_type": order_type,
            "entry": entry, "entry_low": entry_low, "entry_high": entry_high,
            "sl": sl, "targets": targets, "tp_values": tp_values,
            "matched_format": matched, "warnings": warnings}


def clear_format_cache() -> None:
    global _FORMAT_CACHE, _FORMAT_CACHE_MTIME, _CONFIG_CACHE
    _FORMAT_CACHE, _FORMAT_CACHE_MTIME, _CONFIG_CACHE = [], None, {}
