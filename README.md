# kcsm-jazz

Play [KCSM Jazz 91](https://www.kcsm.org/) from the terminal, no browser needed.

## Usage

```sh
./play.sh          # KCSM HD1 (Jazz 91)
```

Ctrl+C to stop. The only requirement is [uv](https://docs.astral.sh/uv/), which installs the
Python dependencies (just [`miniaudio`](https://github.com/irmen/pyminiaudio)) on first run.

## How it works

The play button on kcsm.org just points at a plain Icecast MP3 stream, no API or auth:

| Station | Stream URL |
| --- | --- |
| HD1 (Jazz 91) | `https://ice7.securenetsystems.net/KCSM2` |

`play.py` connects to that stream, decodes it with miniaudio and plays it on the default
audio output. It also prints the current show from NPR's Cadence schedule feed (the same one
the website uses), plus song titles if the stream sends ICY metadata.
