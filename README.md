# FIIO Snowsky Echo FLAC Media Tool
This is a small script to help owners who already maintain a FLAC library make their music show up nicer on the Snowsky Echo/Echo Mini

The script does the following:
- Recursively searches through the provided directory
- Rename FLAC file to `TRACK_NAME.flac`
- Resize album art to 500x500px
- Download LRC file

```bash
uv sync
uv run main.py <base_dir> [--nolrc]
```
