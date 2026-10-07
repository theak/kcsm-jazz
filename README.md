# kcsm-jazz

Play [KCSM Jazz 91](https://www.kcsm.org/) from the terminal, no browser needed.

## Usage

```sh
./play.sh            # KCSM Jazz 91, AAC+ 64k (sounds best)
```

Ctrl+C to stop. The only requirement is [uv](https://docs.astral.sh/uv/), which installs the
Python dependencies ([PyAV](https://pyav.basswood-io.com/), numpy, sounddevice) on first run.

## Other commands

```sh
./play.sh mp3        # Jazz 91 as MP3 96k, 32 kHz
./play.sh hd2        # KCSM HD2
```
