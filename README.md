# FIIO Snowsky Echo FLAC Media Tool
This is a small script to help owners who already maintain a FLAC library make their music work/show up nicer on the Snowsky Echo/Echo Mini

The script does the following:
- Recursively searches through the provided directory
- Re-samples audio higher than 192Khz 24bit via ffmpeg
- Re-encodes files with block size higher than 4096 via `flac` CLI
- Rename FLAC file to `TRACK_NAME - ARTIST.flac`
- Resize album art to 500x500px
- Normalize all audio to -14 LUFS
- Download LRC file
  - A delay of 0.3 sec is hardcoded to avoid rate limit, this is a hard limit across all threads (if running multithreaded)

# External Dependencies
You need the FLAC command line tool to be accessible globally, meaning it must be able to run anywhere on your machine. Using the official tool was the most consistent way of fixing the block-size issue cross-platform.

https://xiph.org/flac/download.html

- Windows: `winget install -e --id Xiph.FLAC`
- Linux: `sudo pacman -S flac` (follow your package manager)
- macOS: `brew install flac` (idk tho i don't own a mac)

```bash
uv sync
uv run main.py <base_dir> [--nolrc] [-n num_threads]
```

Example: `uv run main.py <DIR_WITH_MUSIC>`

# Other Tools
`apply_album_art.sh` - Recursively traverse all folders, automatically apply album art and resize to all FLACs that have a JPG/PNG in the same directory
