from datetime import datetime
import sys

def log(msg, *args, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted = msg % args if args else msg
    print(f"[{timestamp}] {level}: {formatted}", file=sys.stderr)

def debug(msg, *args): log(msg, *args, level="DEBUG")
def error(msg, *args): log(msg, *args, level="ERROR")
