import time

def log(source: str, msg: str) -> None:
    """Print a log message in the required format: [source epoch_seconds] message"""
    print(f"[{source} {int(time.time())}] {msg}")