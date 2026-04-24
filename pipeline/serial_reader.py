# serial_reader.py
# Middle layer of the data pipeline. Reads CSV lines from either stdin
# (piped from fake_pico.py) or a real USB serial port, validates each row,
# and yields clean data dictionaries for the logger to consume.
# Usage: python fake_pico.py --fast | python serial_reader.py

import argparse
import sys

# ── SCHEMA ───────────────────────────────────────────────────────────
FIELDS = [
    "timestamp",
    "cell_voltage",
    "cell_current",
    "panel_voltage",
    "panel_current",
    "panel_power",
    "cell_temp",
    "panel_temp",
    "battery_soc",
]

FIELD_COUNT = len(FIELDS)

# Sanity bounds that flag sensor faults — not physical limits.
_BOUNDS = {
    "cell_voltage" : (0.0,  3.0),
    "cell_current" : (0.0, 10.0),
    "battery_soc"  : (0.0,  1.0),
}


# ── VALIDATION ───────────────────────────────────────────────────────

def _validate(values):
    """
    Applies bounds checks to a parsed row.

    values  : dict mapping field name → float
    returns : (bool, str) — (True, "") if valid, or (False, reason) if not
    """
    for field, (lo, hi) in _BOUNDS.items():
        v = values[field]
        if not (lo <= v <= hi):
            return False, f"{field}={v:.4f} outside [{lo}, {hi}]"
    return True, ""


# ── CORE GENERATOR ───────────────────────────────────────────────────

def read_stream(source):
    """
    Reads CSV lines from source and yields validated data dicts.

    Skips blank lines, comment lines, lines with the wrong field count,
    lines that contain non-numeric values, and rows that fail bounds checks.
    All skipped lines are reported to stderr.

    source  : any iterable of str lines — sys.stdin, a serial port wrapped
              in io.TextIOWrapper, or a list of strings for testing
    yields  : dict mapping each field name to a float value
    """
    header_seen = False

    for raw in source:
        line = raw.strip()

        if not line or line.startswith("#"):
            continue

        # First non-blank, non-comment line is the header — consume and skip.
        if not header_seen:
            header_seen = True
            continue

        fields = line.split(",")

        if len(fields) != FIELD_COUNT:
            print(
                f"[skip] wrong field count ({len(fields)} != {FIELD_COUNT}): {line!r}",
                file=sys.stderr,
            )
            continue

        try:
            values = {name: float(f) for name, f in zip(FIELDS, fields)}
        except ValueError as exc:
            print(f"[skip] parse error — {exc}: {line!r}", file=sys.stderr)
            continue

        ok, reason = _validate(values)
        if not ok:
            print(f"[skip] bounds check failed — {reason}: {line!r}", file=sys.stderr)
            continue

        yield values


# ── SERIAL PORT HELPERS ───────────────────────────────────────────────

def _open_serial(port, baud):
    """
    Opens a serial port and returns a TextIOWrapper suitable for iteration.

    Defers the pyserial import so the module loads cleanly without it
    installed; only raises ImportError when --port is actually used.

    port  : device string, e.g. "COM3" or "/dev/ttyACM0"
    baud  : baud rate integer
    returns : (serial.Serial instance, io.TextIOWrapper)
    """
    try:
        import serial
        import io
    except ImportError:
        sys.exit(
            "pyserial is required for --port. Install it with: pip install pyserial"
        )

    ser = serial.Serial(port, baudrate=baud, timeout=1)
    stream = io.TextIOWrapper(ser, encoding="utf-8", errors="replace")
    return ser, stream


# ── CLI ──────────────────────────────────────────────────────────────

def parse_args():
    """
    Parses command-line arguments for input source selection.

    returns : argparse.Namespace with attributes: port, baud
    """
    parser = argparse.ArgumentParser(
        description="Read and validate Pico CSV stream from stdin or a serial port."
    )
    parser.add_argument(
        "--port",
        default=None,
        metavar="PORT",
        help="Serial port to read from (e.g. COM3 or /dev/ttyACM0). "
             "Reads from stdin if omitted.",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=115200,
        help="Baud rate for serial port (default: 115200)",
    )
    return parser.parse_args()


# ── ENTRY POINT ──────────────────────────────────────────────────────

if __name__ == "__main__":
    args   = parse_args()
    ser    = None

    try:
        if args.port:
            ser, source = _open_serial(args.port, args.baud)
        else:
            source = sys.stdin

        for record in read_stream(source):
            print(record, flush=True)

    except KeyboardInterrupt:
        print("\n[serial_reader] interrupted by user", file=sys.stderr)

    finally:
        if ser is not None:
            ser.close()
