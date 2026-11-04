"""Starter XAUUSD Telegram signal backtester.

IMPORTANT: This is a starter template. Adapt parse_signal() to the channel's exact
message format and validate outcomes against your manual spreadsheet before use.
It does not place trades or send orders.
"""
from __future__ import annotations
import asyncio
import json
import logging
import os
import re
import sqlite3
from copy import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import MetaTrader5 as mt5
import pandas as pd
from dotenv import load_dotenv
from openpyxl import load_workbook
from telethon import TelegramClient, events


load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / os.getenv(
    "DB_PATH", "goldxion.sqlite3"
)
OUTPUT_XLSX = Path(
    os.getenv(
        "OUTPUT_XLSX",
        str(ROOT / "new_channel_backtest_output.xlsx")
    )
)
TEMPLATE_XLSX = Path(os.getenv("TEMPLATE_XLSX", "")) if os.getenv("TEMPLATE_XLSX") else None
SHEET_NAME = os.getenv("SHEET_NAME", "Result")
CHANNEL = os.getenv("TELEGRAM_CHANNEL", "https://t.me/Goldxion")
MT5_SYMBOL = os.getenv("MT5_SYMBOL", "XAUUSD")
# ICMarketsSC broker server time offset
# MT5_SERVER_UTC_OFFSET = timedelta(hours=6)

LOOKAHEAD_DAYS = int(os.getenv("LOOKAHEAD_DAYS", "7"))
HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "0"))  # 0 = all accessible history
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "60"))

# Excel columns modeled on the screenshot. Change these labels if your workbook differs.
HEADERS = ["Year","Month","Date", "Time (Here)", "Direction", "Entry Price", "SL",
           "TP1", "PnL", "Result","TP2", "PnL", "Result","TP3", "PnL", "Result","TP4", "PnL", "Result","TP5", "PnL", "Result","TP6", "PnL", "Result"]


def db_connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS signals (
        chat_id TEXT NOT NULL, message_id INTEGER NOT NULL, message_date TEXT NOT NULL,
        raw_text TEXT NOT NULL, direction TEXT, entry REAL, sl REAL,
        tp1 REAL, tp2 REAL, tp3 REAL,
        tp4 REAL, tp5 REAL, tp6 REAL,
        excel_row INTEGER,PRIMARY KEY(chat_id, message_id))""")
    # Add TP4-TP6 to existing databases if they are missing.
    existing_columns = {
        row["name"]
        for row in con.execute("PRAGMA table_info(signals)").fetchall()
    }

    for i in range(4, 7):
        column = f"tp{i}"

        if column not in existing_columns:
            con.execute(
                f"ALTER TABLE signals ADD COLUMN {column} REAL"
            )

    con.commit()
    return con



def parse_signal(text: str, message_date: datetime) -> dict | None:
    """Parse XAUUSD market, stop, and limit signals."""

    t = text.upper().replace(",", "")
    t = re.sub(r"[ \t]+", " ", t)

    # Accept XAUUSD or GOLD.
    if not re.search(r"\b(?:XAUUSD|GOLD)\b", t):
        return None

    # Identify BUY or SELL, including formats such as:
    # BUY, BUY SETUP, SELL SETUP.
    direction_match = re.search(
        r"\b(BUY|SELL)(?:\s+SETUP)?\b",
        t
    )

    if not direction_match:
        return None

    side = direction_match.group(1)

    # Identify the order type and entry price.
    entry = None
    order_type = None

    price = r"\d{3,5}(?:\.\d+)?"

    entry_prices = (
        rf"(?P<first>{price})"
        rf"(?:\s*(?:-|–|—|\bTO\b)\s*(?P<second>{price}))?"
    )

    def select_entry(first, second=None):
        prices = [float(first)]

        if second is not None:
            prices.append(float(second))

        return min(prices) if side == "BUY" else max(prices)

    # Buy Stop, Sell Stop, Buy Limit, Sell Limit.
    order_match = re.search(
        rf"\b(BUY|SELL)\s+(STOP|LIMIT)\b"
        rf"[^\d\r\n]*?{entry_prices}",
        t,
        re.I,
    )

    if order_match:
        order_side = order_match.group(1).upper()
        order_type = order_match.group(2).title()

        if order_side != side:
            logging.warning("Direction and entry order do not match: %r", text)
            return None

        entry = select_entry(
            order_match.group("first"),
            order_match.group("second"),
        )

    # Price Now or Entry formats.
    if entry is None:
        entry_match = re.search(
            rf"\b(?:PRICE\s+NOW|ENTRY(?:\s+PRICE)?)\b"
            rf"[^\d\r\n]*?{entry_prices}",
            t,
            re.I,
        )

        if entry_match:
            entry = select_entry(
                entry_match.group("first"),
                entry_match.group("second"),
            )
            order_type = "Market"

    # BUY NOW / SELL NOW.
    # Allows emojis between NOW and the entry price.
    if entry is None:
        entry_match = re.search(
            rf"\b(?:BUY|SELL)\s+NOW\b"
            rf"[^\d\r\n]*?{entry_prices}",
            t,
            re.I,
        )

        if entry_match:
            entry = select_entry(
                entry_match.group("first"),
                entry_match.group("second"),
            )
            order_type = "Market"

    # Stop loss: allow emojis between SL and the price.
    sl_match = re.search(
        rf"\b(?:SL|STOP\s*LOSS)\b"
        rf"[^\d\r\n]*?({price})",
        t,
        re.I,
    )
    sl = float(sl_match.group(1)) if sl_match else None

    # Take-profit targets: allow emojis between TP and the price.
    targets = [
        float(match.group(1))
        for match in re.finditer(
            rf"\b(?:TP\s*[1-6]?|TARGET\s*[1-6]?|TAKE\s*PROFIT)\b"
            rf"[^\d\r\n]*?({price})",
            t,
            re.I,
        )
    ]

    if entry is None or sl is None or not targets:
        logging.debug("Message did not match signal format: %r", text[:180])
        return None

    # Preserve up to three TP targets.


    targets = targets[:6]

    tp_values = {
        f"tp{i + 1}": targets[i] if i < len(targets) else None
        for i in range(6)
    }

    # Validate price direction.
    if side == "BUY":
        valid = sl < entry and all(
            tp > entry for tp in targets
        )
    else:
        valid = sl > entry and all(
            tp < entry for tp in targets
        )

    if not valid:
        logging.warning("Signal has inconsistent prices: %r", text[:180])
        return None

    direction = (
        f"{side.title()} {order_type}"
        if order_type in ("Stop", "Limit")
        else side.title()
    )

  #  return {
  #      "direction": direction,
  #       "entry": entry,
  #      "sl": sl,
  #      "tp1": tp1,
  #      "tp2": tp2,
  #      "tp3": tp3,
  #  }

    return {
        "direction": direction,
        "entry": entry,
        "sl": sl,
        **tp_values,
    }

def save_message(chat_id, msg_id, msg_date, text):
    con = db_connect()
    parsed = parse_signal(text or "", msg_date)
    if parsed is None:
        con.close()
        return False
    #con.execute("""INSERT OR IGNORE INTO signals
    #    (chat_id,message_id,message_date,raw_text,direction,entry,sl,tp1,tp2,tp3)
    #    VALUES (?,?,?,?,?,?,?,?,?,?)""",
    #    (str(chat_id), int(msg_id), msg_date.astimezone(timezone.utc).isoformat(), text,
    #     parsed["direction"], parsed["entry"], parsed["sl"], parsed["tp1"], parsed["tp2"], parsed["tp3"]))


    con.execute("""
        INSERT OR IGNORE INTO signals
        (chat_id, message_id, message_date, raw_text,
        direction, entry, sl,
        tp1, tp2, tp3, tp4, tp5, tp6)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(chat_id),
        int(msg_id),
        msg_date.astimezone(timezone.utc).isoformat(),
        text,
        parsed["direction"],
        parsed["entry"],
        parsed["sl"],
        parsed["tp1"],
        parsed["tp2"],
        parsed["tp3"],
        parsed["tp4"],
        parsed["tp5"],
        parsed["tp6"],
    ))

    con.commit()
    con.close()
    return True


def get_rates(start: datetime, end: datetime) -> pd.DataFrame:
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}. Open MT5 and log in first.")
    try:
        info = mt5.symbol_info(MT5_SYMBOL)

        print("MT5 terminal:", mt5.terminal_info())
        print("MT5 account:", mt5.account_info())
        print("Symbol info:", info)


        if info is None:
            raise RuntimeError(f"MT5 symbol {MT5_SYMBOL!r} not found. Check broker's exact symbol, e.g. XAUUSD.a or GOLD.")
        if not info.visible:
            mt5.symbol_select(MT5_SYMBOL, True)

        # There's a BUG in mt5.copy_rates_range (they treat their server timezone
        # to be ALWAYS UTC, which is fucking wrong)
        # start = start + timedelta(hours=3)

        # Adjust MT5 historical data request according to DST schedule.
        year = start.year

        dst_start = datetime(year, 3, 8, tzinfo=start.tzinfo)
        dst_end = datetime(year, 11, 2, tzinfo=start.tzinfo)

        if dst_start <= start < dst_end:
            server_offset = 3
        else:
            server_offset = 2

        start = start + timedelta(hours=server_offset)
        end = end + timedelta(hours=server_offset)

        print(f"MT5 server offset: UTC+{server_offset}")

        
        rates = mt5.copy_rates_range(MT5_SYMBOL, mt5.TIMEFRAME_M1, start, end)

        if rates is not None and len(rates) > 0:
            print("Raw first candle UTC:",
                datetime.fromtimestamp(
                    int(rates[0]["time"]),
                    tz=timezone.utc
                ))
            print("Raw first candle OHLC:",
                rates[0]["open"],
                rates[0]["high"],
                rates[0]["low"],
                rates[0]["close"])
        
        if rates is None or len(rates) == 0:
            return pd.DataFrame()
        df = pd.DataFrame(rates)

        print("\n--- RAW MT5 DATA ---")
        print("Requested symbol:", MT5_SYMBOL)
        print("Requested start UTC:", start)
        print("Requested end UTC:", end)
        print("Raw first timestamp:", rates[0]["time"])
        print("Raw first OHLC:", {
            "open": rates[0]["open"],
            "high": rates[0]["high"],
            "low": rates[0]["low"],
            "close": rates[0]["close"],
        })
        print("Raw last timestamp:", rates[-1]["time"])    

        # Convert MT5 timestamps to datetime.
        # df["time"] = pd.to_datetime(df["time"], unit="s")
        df["time"] = pd.to_datetime(df["time"], unit="s").dt.tz_localize("Etc/GMT-3")

        return df.sort_values("time").reset_index(drop=True)
    finally:
        mt5.shutdown()


def evaluate_target(signal, bars: pd.DataFrame, target: float | None) -> tuple[str, float | None]:
    """Evaluate one TP independently. PnL is measured in R-multiples."""

    if target is None:
        return "N/A", None

    entry = float(signal["entry"])
    sl = float(signal["sl"])
    risk = abs(entry - sl)

    if risk <= 0 or bars.empty:
        return "Pending", None

    direction = signal["direction"]
    is_buy = direction.startswith("Buy")
    is_market = direction in ("Buy", "Sell")

    # Market orders are treated as filled immediately.
    # Limit orders must first reach their entry price.
    filled = is_market

    for row in bars.itertuples(index=False):
        if not filled:

            if direction.lower().endswith("stop"):
                touched = (
                    row.high >= entry if is_buy else row.low <= entry
                )

            elif direction.lower().endswith("limit"):
                touched = (
                    row.low <= entry if is_buy else row.high >= entry
                )

            else:
                continue

            if not touched:
                continue

            filled = True

        stop_touched = row.low <= sl if is_buy else row.high >= sl
        target_touched = row.high >= target if is_buy else row.low <= target

        # M1 OHLC data cannot reliably establish which level was hit first.
        if stop_touched and target_touched:
            return "Ambiguous", None

        if stop_touched:
            return "Loss", -1.0

        if target_touched:
            return "Win", abs(target - entry) / risk

    return ("Open at end" if filled else "Pending"), None


def evaluate_signal(signal) -> dict:
    """Evaluate each TP independently.

    TP reached before entry:
        That TP = No Take; continue monitoring other targets.

    After entry:
        Each TP is evaluated independently.
        SL closes all remaining unresolved targets.
    """

    msg_time = datetime.fromisoformat(signal["message_date"])

    if msg_time.tzinfo is None:
        msg_time = msg_time.replace(tzinfo=timezone.utc)

    msg_time = msg_time.astimezone(timezone.utc)
    now = datetime.now(timezone.utc)
    end = min(now, msg_time + timedelta(days=LOOKAHEAD_DAYS))

    if end <= msg_time:
        return {"results": [("Pending", None)] * 3, "filled": False}

    bars = get_rates(msg_time, end)

    direction = str(signal["direction"]).lower()
    is_buy = direction.startswith("buy")
    is_market = direction in ("buy", "sell")

    entry = float(signal["entry"])
    sl = float(signal["sl"])

    #targets = [
    #    signal["tp1"],
    #    signal["tp2"],
    #    signal["tp3"],
    #]

    targets = [
    signal[f"tp{i}"]
    for i in range(1, 7)
    ]

    print("\n--- EVALUATION DEBUG ---")
    print("Message ID:", signal["message_id"])
    print("Message time UTC:", msg_time)
    print("Direction:", direction)
    print("Entry:", entry, "SL:", sl, "TPs:", targets)
    print("MT5 symbol:", MT5_SYMBOL)
    print("Bars loaded:", len(bars))

    if bars.empty:
        return {"results": [("Pending", None)] * 3, "filled": False}

    risk = abs(entry - sl)

    if risk <= 0:
        return {"results": [("Pending", None)] * 3, "filled": False}

    #results = [None, None, None]
    results = [None] * 6

    filled = False

    for bar in bars.itertuples(index=False):

        # Check entry activation.
        if not filled:

            if is_market:
                entry_touched = bar.low <= entry <= bar.high

            elif direction.endswith("stop"):

                # Reject a pending Stop order if the first available
                # candle has already opened beyond its entry price.
                if is_buy and bar.open > entry:
                    results = [
                        ("No Take", 0.0) if target is not None
                        else ("N/A", None)
                        for target in targets
                    ]
                    print(f"{bar.time} | Buy Stop already passed at open | NO TAKE")
                    break

                if not is_buy and bar.open < entry:
                    results = [
                        ("No Take", 0.0) if target is not None
                        else ("N/A", None)
                        for target in targets
                    ]
                    print(f"{bar.time} | Sell Stop already passed at open | NO TAKE")
                    break

                entry_touched = (
                    bar.high >= entry if is_buy else bar.low <= entry
                )

            elif direction.endswith("limit"):
                entry_touched = (
                    bar.low <= entry if is_buy else bar.high >= entry
                )

            else:
                continue

            hit_sl_before_entry = (
                bar.low <= sl if is_buy else bar.high >= sl
            )

            hit_tp_before_entry = [
                target is not None and (
                    bar.high >= float(target)
                    if is_buy
                    else bar.low <= float(target)
                )
                for target in targets
            ]

            # Entry and exit levels reached in the same candle.
            # Their exact order cannot be established from M1 OHLC.
            if entry_touched:

                if hit_sl_before_entry:
                    for i, target in enumerate(targets):
                        if target is not None and results[i] is None:
                            results[i] = ("Ambiguous", None)

                    print(f"{bar.time} | Entry and SL touched in same candle | AMBIGUOUS")
                    break

                # Only targets touched in this candle are ambiguous.
                for i, target in enumerate(targets):
                    if target is not None and results[i] is None:
                        if hit_tp_before_entry[i]:
                            results[i] = ("Ambiguous", None)

                filled = True

            else:
                # TP reached before entry:
                # Mark only the corresponding TP as No Take.
                for i, target in enumerate(targets):
                    if (
                        target is not None
                        and results[i] is None
                        and hit_tp_before_entry[i]
                    ):
                        results[i] = ("No Take", 0.0)
                        print(
                            f"{bar.time} | TP{i + 1} reached before entry "
                            "| NO TAKE"
                        )

                # SL reached before entry:
                # Invalidate all remaining unresolved targets.
                if hit_sl_before_entry:
                    for i, target in enumerate(targets):
                        if target is not None and results[i] is None:
                            results[i] = ("No Take", 0.0)

                    print(
                        f"{bar.time} | SL reached before entry "
                        "| Remaining targets NO TAKE"
                    )
                    break

                # Continue waiting for entry.
                continue

        # Normal trade evaluation after entry.
        unresolved = [
            i for i, result in enumerate(results)
            if result is None and targets[i] is not None
        ]

        if not unresolved:
            break

        hit_sl = (
            bar.low <= sl if is_buy else bar.high >= sl
        )

        hit_targets = [
            target is not None and (
                bar.high >= float(target)
                if is_buy
                else bar.low <= float(target)
            )
            for target in targets
        ]
        # print each bar's OHLC value
        print(
           f"{bar.time} | O={bar.open} H={bar.high} "
            f"L={bar.low} C={bar.close} | "
            f"Entry filled={filled} | "
            f"SL hit={hit_sl} | TP hits={hit_targets}"
        )

        # SL and unresolved TP touched in the same candle.
        if hit_sl and any(hit_targets[i] for i in unresolved):

            for i in unresolved:
                if hit_targets[i]:
                    results[i] = ("Ambiguous", None)
                else:
                    results[i] = ("Loss", -1.0)

            break

        # Record independently reached targets.
        for i in unresolved:
            if hit_targets[i]:
                results[i] = (
                    "Win",
                    abs(float(targets[i]) - entry) / risk,
                )

        # SL closes all remaining unresolved targets.
        if hit_sl:
            #for i in range(3):
            for i in range(6):
                if results[i] is None and targets[i] is not None:
                    results[i] = ("Loss", -1.0)

            break

    # Assign remaining results.
    for i, target in enumerate(targets):
        if target is None:
            results[i] = ("N/A", None)

        elif results[i] is None:
            results[i] = (
                "Open at end" if filled else "Pending",
                None,
            )

    print("ORDER FILLED:", filled)
    print("FINAL RESULTS:", results)

    return {"results": results, "filled": filled}







def ensure_workbook():
    if OUTPUT_XLSX.exists():
        wb = load_workbook(OUTPUT_XLSX)
        ws = wb[SHEET_NAME] if SHEET_NAME in wb.sheetnames else wb.active
        for col, value in enumerate(HEADERS, 1):
            ws.cell(1, col, value)
        return wb, ws
    if TEMPLATE_XLSX and TEMPLATE_XLSX.exists():
        wb = load_workbook(TEMPLATE_XLSX)
        ws = wb[SHEET_NAME] if SHEET_NAME in wb.sheetnames else wb.active
        for col, value in enumerate(HEADERS, 1):
                    ws.cell(1, col, value)
        return wb, ws
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    for col, value in enumerate(HEADERS, 1):
        ws.cell(1, col, value)
        for col, value in enumerate(HEADERS, 1):
                    ws.cell(1, col, value)
    return wb, ws



def write_signal_to_excel(row_data, signal_key):
    OUTPUT_XLSX.parent.mkdir(parents=True, exist_ok=True)

    wb, ws = ensure_workbook()
    con = db_connect()

    try:
        record = con.execute(
            "SELECT excel_row FROM signals WHERE chat_id=? AND message_id=?",
            signal_key
        ).fetchone()

        row_num = record["excel_row"] if record and record["excel_row"] else None

        if row_num is None:
            row_num = ws.max_row + 1

            # Copy formatting from previous row.
            if row_num > 2:
                for col in range(1, max(ws.max_column, len(row_data)) + 1):
                    src = ws.cell(row_num - 1, col)
                    dst = ws.cell(row_num, col)

                    if src.has_style:
                        dst._style = copy(src._style)

                    if src.number_format:
                        dst.number_format = src.number_format

                    if src.alignment:
                        dst.alignment = copy(src.alignment)

            con.execute(
                "UPDATE signals SET excel_row=? WHERE chat_id=? AND message_id=?",
                (row_num, *signal_key)
            )
            con.commit()

        # Write data.
        for col, value in enumerate(row_data, 1):
            ws.cell(row_num, col, value)

        # Save to temporary file first.
        temp_path = OUTPUT_XLSX.with_name(
            OUTPUT_XLSX.stem + "_temp.xlsx"
        )

        wb.save(temp_path)
        wb.close()

        # Validate temporary workbook.
        check_wb = load_workbook(temp_path, read_only=True)
        check_ws = check_wb[SHEET_NAME]

        if check_ws.max_row < row_num:
            raise RuntimeError("Excel validation failed: missing data rows.")

        check_wb.close()

        # Replace original only after successful validation.
        os.replace(temp_path, OUTPUT_XLSX)

        logging.info(
            "Excel saved successfully: %s | Size: %s bytes | Rows: %s",
            OUTPUT_XLSX.resolve(),
            OUTPUT_XLSX.stat().st_size,
            row_num
        )

    except Exception:
        wb.close()
        logging.exception("Excel writing failed")
        raise

    finally:
        con.close()



def process_signal(signal):
    evaluation = evaluate_signal(signal)
    results = evaluation["results"]

    dt = datetime.fromisoformat(signal["message_date"]).astimezone()

    year = dt.strftime("%Y")
    month = dt.strftime("%Y.%m")
    date = dt.strftime("%Y.%m.%d")
    time = dt.strftime("%H:%M")

    row = [
        year,
        month,
        date,
        time,
        signal["direction"],
        signal["entry"],
        signal["sl"]
    ]

    # for idx, (status, pnl) in enumerate(results, start=1):
    #    row.extend([signal[f"tp{idx}"], pnl, status])

    for idx, (status, pnl) in enumerate(results, start=1):
        row.extend([signal[f"tp{idx}"], pnl, status])

    write_signal_to_excel(
        row,
        (signal["chat_id"], signal["message_id"])
    )

    logging.info(
        "Updated message %s: %s",
        signal["message_id"],
        [x[0] for x in results]
    )


def process_all_saved():
    con = db_connect()
    signals = con.execute("SELECT * FROM signals ORDER BY message_date, message_id").fetchall()
    #signals = con.execute("SELECT * FROM signals ORDER BY message_date DESC, message_id DESC LIMIT 10").fetchall()
    
    con.close()
    for signal in signals:
        try:
            process_signal(dict(signal))
        except Exception:
            logging.exception("Failed to process Telegram message %s", signal["message_id"])


async def main():
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    if not api_id or not api_hash:
        raise RuntimeError("Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env first.")
    client = TelegramClient(str(ROOT / "telegram_session"), int(api_id), api_hash)
    await client.start()  # First run asks for your Telegram phone/login code.
    entity = await client.get_entity(CHANNEL)
    chat_id = getattr(entity, "id", CHANNEL)

    logging.info("Importing accessible historical messages from %s", CHANNEL)
    count = 0
    async for msg in client.iter_messages(entity, limit=(HISTORY_LIMIT or None), reverse=True):
        if not msg.message:
            continue
        if save_message(chat_id, msg.id, msg.date, msg.message):
            count += 1
    logging.info("Imported %d newly parsed signals. Recalculating workbook...", count)
    process_all_saved()

    @client.on(events.NewMessage(chats=entity))
    async def new_message_handler(event):
        text = event.raw_text or ""
        if save_message(chat_id, event.id, event.date, text):
            logging.info("New signal parsed: message %s", event.id)
            process_all_saved()
        else:
            logging.info("New message %s did not match parser; review raw message manually.", event.id)

    @client.on(events.MessageEdited(chats=entity))
    async def edited_message_handler(event):
        # Edits can change entry/SL/TP. Update stored parsed values if the edited message still parses.
        parsed = parse_signal(event.raw_text or "", event.date)
        if not parsed:
            logging.warning("Edited message %s no longer parses; review it manually.", event.id)
            return
        con = db_connect()
        #con.execute("""UPDATE signals SET raw_text=?, message_date=?, direction=?, entry=?, sl=?, tp1=?, tp2=?, tp3=?
        #    WHERE chat_id=? AND message_id=?""",
        #    (event.raw_text, event.date.astimezone(timezone.utc).isoformat(), parsed["direction"],
        #     parsed["entry"], parsed["sl"], parsed["tp1"], parsed["tp2"], parsed["tp3"], str(chat_id), event.id))
        
        con.execute("""
        UPDATE signals
        SET raw_text=?, message_date=?, direction=?,
            entry=?, sl=?,
            tp1=?, tp2=?, tp3=?, tp4=?, tp5=?, tp6=?
        WHERE chat_id=? AND message_id=?
    """, (
        event.raw_text,
        event.date.astimezone(timezone.utc).isoformat(),
        parsed["direction"],
        parsed["entry"],
        parsed["sl"],
        parsed["tp1"],
        parsed["tp2"],
        parsed["tp3"],
        parsed["tp4"],
        parsed["tp5"],
        parsed["tp6"],
        str(chat_id),
        event.id,
    ))
        
        con.commit(); con.close()
        process_all_saved()
        logging.info("Reprocessed edited message %s", event.id)

    async def periodic_refresh():
        while True:
            await asyncio.sleep(POLL_SECONDS)
            process_all_saved()  # Pending live signals are re-evaluated as price history grows.

    asyncio.create_task(periodic_refresh())
    logging.info("Listening for new channel messages. Press Ctrl+C to stop.")
    await client.run_until_disconnected()


#test_message = """🔥GOLD BUY NOW 🔥 @ 3900-3890

#TP ⬅️ 3904
#TP ⬅️ 3920
#TP ⬅️ 3930

#SL 🚪 3883

#🛡 use BE & TP for risk management"""

#result = parse_signal(test_message, datetime.now(timezone.utc))
#print("PARSER TEST RESULT:", result)

if __name__ == "__main__":
    asyncio.run(main())
