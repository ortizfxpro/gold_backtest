# XAUUSD Telegram Backtester (starter)

This is a local research/backtesting starter, not a trading bot. It does not place orders.

## Requirements
- Windows 10/11
- Python 3.11 recommended
- MetaTrader 5 desktop terminal installed and logged in (demo is fine)
- Telegram account that can access the target channel
- Channel message format that can be parsed by `parse_signal()`

## Install
Open PowerShell in this folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Set `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` from https://my.telegram.org. Keep these private. On first run, Telethon asks for your phone number and login code. The resulting `telegram_session.session` file is sensitive; do not share it.

Open MT5 and log into the broker account that has the historical XAUUSD data you want. Search Market Watch for the exact symbol name. Some brokers use suffixes such as `XAUUSD.a` or `GOLD`.

## Excel
- If `OUTPUT_XLSX` points to an existing workbook, the script writes to the named sheet (or active sheet if that name is absent).
- If it does not exist and `TEMPLATE_XLSX` points to a template, the script uses that template.
- Otherwise it creates a new workbook with headers modeled on the screenshot.
- Back up the workbook before first run. The program writes data rows and copies style from the previous row, but cannot perfectly reproduce merged date-group labels, conditional formatting rules, or formulas without inspecting the real workbook.

## Run
```powershell
python main.py
```

The first run imports accessible history, then keeps listening for new messages. Press Ctrl+C to stop. The SQLite database `signals.sqlite3` stores parsed messages and avoids duplicate imports.

## Important limitations to fix before trusting results
1. **Parser:** `parse_signal()` is only an example parser. It assumes a text message includes `BUY LIMIT` or `SELL LIMIT`, entry, SL, TP1, TP2 and TP3. Modify it to match actual channel messages. Messages that fail parsing are skipped and logged.
2. **MT5 symbol and data:** MT5 must be open/logged in; broker history may be incomplete. Download sufficient M1 history first.
3. **Independent TP results:** each target is evaluated as a separate hypothetical trade with the same entry and SL. This is not a single trade with partial closes.
4. **PnL:** PnL is stored as R-multiple: win = target distance / stop distance; loss = -1R. It is not dollar PnL or the exact formula in your screenshot. Adjust the calculation to match your sheet.
5. **Ambiguous M1 candles:** if one candle touches both SL and TP, result is `Ambiguous`; OHLC bars cannot prove which level came first. Use MT5 tick data for finer sequencing.
6. **Entry fill model:** this starter assumes a limit fills if candle low/high touches entry; it does not model spread, slippage, commissions, gaps, partial fills, expiry, or order cancellation.
7. **Historical timestamps:** Telegram timestamps are normalized to UTC for querying MT5; the Excel date/time is displayed in the Windows local timezone. Verify this matches your manual sheet.
8. **Message edits/deletions:** edits are reprocessed. Telegram does not guarantee every deletion event is delivered; the original text is stored in SQLite for audit.
9. **Excel row mapping:** Excel row numbers are saved in SQLite. If you sort or delete rows manually, clear the stored `excel_row` mappings or rebuild the output workbook.

## Validate before using
Manually check at least 30 signals across wins, losses, unfilled limits, and ambiguous candles. Compare entry fill, each target outcome, timestamps, and PnL against your existing workbook. Do not use results for financial decisions until these differences are explained.
