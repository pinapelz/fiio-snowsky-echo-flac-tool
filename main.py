import argparse
from pathlib import Path
from typing import Iterator
from tqdm import tqdm
import syncedlyrics
from mutagen.flac import FLAC

def iter_files(base: Path) -> Iterator[Path]:
    iterator = base.rglob("*")
    for p in iterator:
        if p.is_file():
            yield p.resolve()

def rename_file(filepath: Path, new_name: str) -> None:
    target = filepath.with_name(new_name)
    filepath.rename(target)


def get_track_info(path: Path) -> tuple:
    audio = FLAC(str(path))
    title = audio.get("TITLE", [""])
    artist = audio.get("ARTIST", [""])
    return (title[0], artist[0])

def resize_album_art(path: Path) -> None:
    audio = FLAC(str(path))
    if not audio.pictures:
        return
    from io import BytesIO
    from PIL import Image
    for pic in audio.pictures:
        with Image.open(BytesIO(pic.data)) as img:
            resized = img.resize((500, 500), Image.Resampling.LANCZOS)
            out = BytesIO()
            fmt = img.format if img.format else "PNG"
            resized.save(out, format=fmt)
            pic.data = out.getvalue()
    audio.save()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_dir", type=Path)
    parser.add_argument("--nolrc", "-n", action="store_true", dest="flag")
    args = parser.parse_args()

    base = args.base_dir
    files = [p for p in iter_files(base) if p.suffix == ".flac"]

    for fp in tqdm(files, desc="Processing FLAC files", unit="file"):
        print("Fetching track info and renaming file")
        title, artist = get_track_info(fp)

        new_file_name = title + ".flac"
        rename_file(fp, new_file_name)
        fp = fp.with_name(new_file_name)

        print("Resizing album art to 500x500")
        resize_album_art(fp)

        if args.nolrc:
            continue

        lrc_path = fp.with_suffix(".lrc")
        if lrc_path.exists():
            print("Skipping", lrc_path, "as LRC already exists")
            continue

        print(f"Fetching LRC file for {title} {artist}")
        lrc = syncedlyrics.search(f"{title} {artist}", providers=["Lrclib", "Megalobiz", "NetEase"])

        with open(lrc_path, "w", encoding="utf-8") as f:
            f.write(lrc if lrc else "")

if __name__ == "__main__":
    main()
