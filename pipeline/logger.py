# logger.py
# Final stage of the data pipeline. Reads validated sensor dicts from
# serial_reader.read_stream() and writes them to a timestamped CSV file.
# Pipeline usage: python fake_pico.py --fast | python logger.py

import argparse
import csv
import os
import sys
from datetime import datetime

from serial_reader import read_stream, FIELDS

# ── OUTPUT PATH ──────────────────────────────────────────────────────
_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "logs")

STATUS_INTERVAL = 10    # print a stderr status line every N rows


# ── FILE HELPERS ─────────────────────────────────────────────────────

def make_log_path():
    """
    Builds a timestamped log file path inside data/logs/.

    Creates the directory if it does not exist.
    returns : absolute path string for the new CSV file
    """
    os.makedirs(_LOG_DIR, exist_ok=True)
    filename = "log_{}.csv".format(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    return os.path.join(_LOG_DIR, filename)


# ── SERIAL PORT HELPER ───────────────────────────────────────────────

def _open_serial(port, baud=115200):
    """
    Opens a serial port and returns a TextIOWrapper suitable for read_stream.

    Defers the pyserial import so the module loads without it installed;
    only fails if --port is actually used.

    port  : device string, e.g. "COM3" or "/dev/ttyACM0"
    baud  : baud rate integer
    returns : (serial.Serial, io.TextIOWrapper)
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


# ── CORE LOGGER ──────────────────────────────────────────────────────

def log_stream(source, log_path):
    """
    Reads validated dicts from source via read_stream and writes them to CSV.

    Flushes to disk after every row so data survives an abrupt power loss.
    Prints a status line to stderr every STATUS_INTERVAL rows.
    Returns the total number of rows written.

    source   : iterable of raw CSV lines (sys.stdin or serial TextIOWrapper)
    log_path : absolute path to the output CSV file
    returns  : int — total rows written
    """
    rows_written = 0
    log_name = os.path.basename(log_path)

    with open(log_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDS)
        writer.writeheader()
        csvfile.flush()

        for record in read_stream(source):
            writer.writerow(record)
            csvfile.flush()
            rows_written += 1

            if rows_written % STATUS_INTERVAL == 0:
                print(
                    f"[logger] {rows_written} rows written to {log_name}",
                    file=sys.stderr,
                )

    return rows_written


# ── CLI ──────────────────────────────────────────────────────────────

def parse_args():
    """
    Parses command-line arguments for input source selection.

    returns : argparse.Namespace with attributes: port, baud
    """
    parser = argparse.ArgumentParser(
        description="Log validated Pico sensor stream to a timestamped CSV file."
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
    args    = parse_args()
    ser     = None
    log_path = make_log_path()

    print(f"[logger] writing to {log_path}", file=sys.stderr)

    try:
        if args.port:
            ser, source = _open_serial(args.port, args.baud)
        else:
            source = sys.stdin

        total = log_stream(source, log_path)

    except KeyboardInterrupt:
        total = 0
        # Count rows already written by reading the file we created.
        try:
            with open(log_path, "r") as f:
                total = sum(1 for _ in f) - 1   # subtract header
        except OSError:
            pass

    finally:
        if ser is not None:
            ser.close()
        print(
            f"[logger] done — {total} rows written to {log_path}",
            file=sys.stderr,
        )
