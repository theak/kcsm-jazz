# kcsm-jazz

Play [KCSM Jazz 91](https://www.kcsm.org/) from the terminal, no browser needed.

## Usage

```sh
./play.sh            # KCSM Jazz 91, AAC+ 64k (sounds best)
./play.sh mp3        # Jazz 91 as MP3 96k (same station, older encode)
./play.sh hd2        # KCSM HD2
./play.sh --no-meta  # don't print show info
```

Ctrl+C to stop. The only requirement is [uv](https://docs.astral.sh/uv/), which installs the
Python dependencies ([PyAV](https://pyav.basswood-io.com/), numpy, sounddevice) on first run.

## How it works

The play button on kcsm.org just points at a plain Icecast stream (the MP3 one), no API or auth. The AAC+ stream
isn't linked from the site but sounds noticeably better despite the lower bitrate:

| Station | Stream URL | Format |
| --- | --- | --- |
| Jazz 91 (default) | `https://ice5.securenetsystems.net/KCSM` | HE-AAC, 64 kbps |
| Jazz 91 MP3 | `https://ice7.securenetsystems.net/KCSM2` | MP3, 96 kbps, 32 kHz |
| HD2 | `https://ice26.securenetsystems.net/KCSMHD2` | HE-AAC |

`play.py` decodes the stream with PyAV (FFmpeg), resamples to 48 kHz and plays it through
sounddevice, keeping a couple seconds of buffer and reconnecting automatically if the stream
drops. It also prints the current show from NPR's Cadence schedule feed (the same one the
website uses).

## Raspberry Pi

Works on a Pi 3B or Zero 2 W running Raspberry Pi OS (64-bit). sounddevice needs PortAudio:
`sudo apt install libportaudio2`. If audio stutters over WiFi, turn off WiFi power saving:
`sudo iw wlan0 set power_save off`.
