"""Play the KCSM live stream from the terminal, no browser needed.

Usage:
    uv run --with-requirements requirements.txt play.py          # HD1 (Jazz 91)
    uv run --with-requirements requirements.txt play.py hd2      # HD2

Ctrl+C to stop.
"""

import argparse
import json
import sys
import threading
import time
import urllib.request

import miniaudio

STREAMS = {
    "hd1": ("KCSM HD1 (Jazz 91)", "https://ice7.securenetsystems.net/KCSM2"),
    "hd2": ("KCSM HD2", "https://ice26.securenetsystems.net/KCSMHD2"),
}

# NPR Cadence schedule feed (same one the kcsm.org player uses) -> current show
SCHEDULE_URL = (
    "https://cadence.nprstations.org/api/cadence/widget/"
    "2c8042c8-5fb1-4ff9-a7d0-f609990bd085?show_song=true"
)


def current_show():
    try:
        with urllib.request.urlopen(SCHEDULE_URL, timeout=10) as r:
            on = json.load(r).get("onNow") or {}
        if on.get("programName"):
            return f"{on['programName']} ({on.get('startTime')} - {on.get('endTime')})"
    except Exception:
        pass
    return None


def show_loop(stop: threading.Event, interval: int = 300):
    last = None
    while not stop.is_set():
        show = current_show()
        if show and show != last:
            print(f"On air: {show}", flush=True)
            last = show
        stop.wait(interval)


def print_title(client, title):
    # Song titles from the stream's ICY metadata, if the server sends them
    if title:
        print(f"\u266a {title}", flush=True)


def main():
    p = argparse.ArgumentParser(description="Play KCSM without the website")
    p.add_argument("station", nargs="?", default="hd1", choices=STREAMS)
    p.add_argument("--no-meta", action="store_true", help="don't print show/song info")
    args = p.parse_args()

    name, url = STREAMS[args.station]
    print(f"Connecting to {name}: {url}", flush=True)

    source = miniaudio.IceCastClient(url, update_stream_title=None if args.no_meta else print_title)
    stream = miniaudio.stream_any(source, source.audio_format)

    stop = threading.Event()
    if not args.no_meta and args.station == "hd1":
        threading.Thread(target=show_loop, args=(stop,), daemon=True).start()

    with miniaudio.PlaybackDevice() as device:
        device.start(stream)
        print("Playing. Ctrl+C to stop.", flush=True)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping.")
        finally:
            stop.set()
            source.close()


if __name__ == "__main__":
    sys.exit(main())
