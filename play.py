"""Play the KCSM live stream from the terminal, no browser needed.

Usage:
    ./play.sh          # KCSM Jazz 91, AAC+ 64k (sounds best)
    ./play.sh mp3      # KCSM Jazz 91, MP3 96k (same station, older encode)
    ./play.sh hd2      # KCSM HD2, AAC+

Ctrl+C to stop. Decoding is done by PyAV (FFmpeg), so MP3 and AAC both work.
Reconnects automatically if the stream drops.
"""

import argparse
import json
import sys
import threading
import time
import urllib.request

import av
import sounddevice as sd

STREAMS = {
    "aac": ("KCSM Jazz 91 (AAC+)", "https://ice5.securenetsystems.net/KCSM"),
    "mp3": ("KCSM Jazz 91 (MP3)", "https://ice7.securenetsystems.net/KCSM2"),
    "hd2": ("KCSM HD2", "https://ice26.securenetsystems.net/KCSMHD2"),
}

# NPR Cadence schedule feed (same one the kcsm.org player uses) -> current show
SCHEDULE_URL = (
    "https://cadence.nprstations.org/api/cadence/widget/"
    "2c8042c8-5fb1-4ff9-a7d0-f609990bd085?show_song=true"
)

RATE = 48000          # everything gets resampled to this
CHANNELS = 2
BYTES_PER_SEC = RATE * CHANNELS * 2  # s16
PREBUFFER_SEC = 2.0   # audio to collect before (re)starting playback
MAX_BUFFER_SEC = 20.0  # drop old audio past this so we stay close to live


class AudioBuffer:
    """Thread-safe byte FIFO between the decoder thread and the audio callback."""

    def __init__(self):
        self._buf = bytearray()
        self._lock = threading.Lock()
        self.buffering = True  # True until PREBUFFER_SEC is available

    def push(self, data: bytes):
        with self._lock:
            self._buf += data
            excess = len(self._buf) - int(MAX_BUFFER_SEC * BYTES_PER_SEC)
            if excess > 0:
                del self._buf[: excess - excess % 4]
            if self.buffering and len(self._buf) >= PREBUFFER_SEC * BYTES_PER_SEC:
                self.buffering = False

    def pull(self, n: int) -> bytes:
        with self._lock:
            if self.buffering:
                return b""
            chunk = bytes(self._buf[:n])
            del self._buf[:n]
            if len(chunk) < n:
                self.buffering = True  # underrun: go silent until refilled
            return chunk


def decode_loop(url: str, buf: AudioBuffer, stop: threading.Event):
    """Connect, decode, resample to s16/stereo/RATE, push to buf. Reconnect forever."""
    backoff = 1
    first = True
    while not stop.is_set():
        try:
            with av.open(url, timeout=10) as container:
                stream = container.streams.audio[0]
                cc = stream.codec_context
                if first:
                    kbps = f"{stream.bit_rate // 1000} kbps, " if stream.bit_rate else ""
                    profile = f" {cc.profile}" if cc.profile else ""
                    print(f"Format: {cc.name}{profile}, {kbps}{cc.sample_rate} Hz", flush=True)
                    first = False
                else:
                    print("Reconnected.", flush=True)
                resampler = av.AudioResampler(format="s16", layout="stereo", rate=RATE)
                for frame in container.decode(stream):
                    if stop.is_set():
                        return
                    for out in resampler.resample(frame):
                        buf.push(out.to_ndarray().tobytes())
                    backoff = 1
        except Exception as e:
            if stop.is_set():
                return
            print(f"Stream error ({e.__class__.__name__}: {e}); retrying in {backoff}s", flush=True)
        else:
            if not stop.is_set():
                print(f"Stream ended; reconnecting in {backoff}s", flush=True)
        stop.wait(backoff)
        backoff = min(backoff * 2, 30)


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


def main():
    p = argparse.ArgumentParser(description="Play KCSM without the website")
    p.add_argument("station", nargs="?", default="aac", choices=STREAMS)
    p.add_argument("--no-meta", action="store_true", help="don't print show info")
    args = p.parse_args()

    name, url = STREAMS[args.station]
    print(f"Connecting to {name}: {url}", flush=True)

    buf = AudioBuffer()
    stop = threading.Event()
    threading.Thread(target=decode_loop, args=(url, buf, stop), daemon=True).start()
    if not args.no_meta and args.station != "hd2":  # schedule feed is for Jazz 91 only
        threading.Thread(target=show_loop, args=(stop,), daemon=True).start()

    def callback(outdata, frames, time_info, status):
        need = frames * CHANNELS * 2
        chunk = buf.pull(need)
        outdata[: len(chunk)] = chunk
        if len(chunk) < need:
            outdata[len(chunk):] = b"\x00" * (need - len(chunk))

    with sd.RawOutputStream(samplerate=RATE, channels=CHANNELS, dtype="int16",
                            latency="high", callback=callback):
        print("Playing. Ctrl+C to stop.", flush=True)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping.")
        finally:
            stop.set()


if __name__ == "__main__":
    sys.exit(main())
