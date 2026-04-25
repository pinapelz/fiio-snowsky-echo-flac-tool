import argparse
import subprocess
from pathlib import Path
from typing import Iterator
from tqdm import tqdm
import syncedlyrics
from mutagen.flac import FLAC
import ffmpeg


def iter_files(base: Path) -> Iterator[Path]:
    iterator = base.rglob("*")
    for p in iterator:
        if p.is_file():
            yield p.resolve()


def rename_file(filepath: Path, new_name: str) -> None:
    target = filepath.with_name(new_name)
    filepath.rename(target)


def get_audio_issues(path: Path) -> dict:
    audio = FLAC(str(path))
    info = audio.info
    sample_rate = getattr(info, "sample_rate", 0)
    bits_per_sample = getattr(info, "bits_per_sample", 24)
    max_blocksize = getattr(info, "max_blocksize", 4096)

    return {
        "needs_sample_rate_fix": sample_rate > 192000,
        "needs_bitdepth_fix": bits_per_sample > 24,
        "needs_blocksize_fix": max_blocksize != 4096,
        "sample_rate": sample_rate,
        "bits_per_sample": bits_per_sample,
        "max_blocksize": max_blocksize,
    }


def fix_with_ffmpeg(path: Path, fix_sample_rate: bool, fix_bitdepth: bool) -> Path:
    output_kwargs = {
        "acodec": "flac",
        "map": "0:a",
    }
    if fix_bitdepth:
        output_kwargs["sample_fmt"] = "s24"
    if fix_sample_rate:
        output_kwargs["ar"] = "192000"

    temp_path = path.with_suffix(".tmp.flac")
    (
        ffmpeg
        .input(str(path))
        .output(str(temp_path), **output_kwargs)
        .overwrite_output()
        .run(quiet=True)
    )
    path.unlink()
    temp_path.rename(path)
    return path


def fix_blocksize(path: Path, blocksize: int = 4096) -> Path:
    temp_path = path.with_suffix(".tmp.flac")
    command = ["flac", "--force", f"--blocksize={blocksize}", str(path), "-o", str(temp_path)]
    try:
        subprocess.run(command, capture_output=True, text=True, check=True)
        path.unlink()
        temp_path.rename(path)
    except subprocess.CalledProcessError as e:
        temp_path.unlink(missing_ok=True)
        print(f"  Error fixing blocksize for {path.name}:")
        print(e.stderr)
    return path


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
    parser.add_argument("--nolrc", "-n", action="store_true", dest="nolrc")
    args = parser.parse_args()

    base = args.base_dir
    files = [p for p in iter_files(base) if p.suffix == ".flac"]

    for fp in tqdm(files, desc="Processing FLAC files", unit="file"):
        print(f"\nProcessing: {fp.name}")
        title, artist = get_track_info(fp)

        new_file_name = title + ".flac"
        rename_file(fp, new_file_name)
        fp = fp.with_name(new_file_name)

        issues = get_audio_issues(fp)
        print(f"  Stats: {issues['sample_rate']}Hz, {issues['bits_per_sample']}-bit, blocksize={issues['max_blocksize']}")

        if issues["needs_sample_rate_fix"] or issues["needs_bitdepth_fix"]:
            reasons = []
            if issues["needs_sample_rate_fix"]:
                reasons.append(f"sample rate {issues['sample_rate']}Hz -> 192000Hz")
            if issues["needs_bitdepth_fix"]:
                reasons.append(f"bit depth {issues['bits_per_sample']}-bit -> 24-bit")
            print(f"  Fixing via ffmpeg: {', '.join(reasons)}")
            fp = fix_with_ffmpeg(fp, issues["needs_sample_rate_fix"], issues["needs_bitdepth_fix"])

            post_info = FLAC(str(fp)).info
            if getattr(post_info, "max_blocksize", 4096) != 4096:
                issues["needs_blocksize_fix"] = True

        if issues["needs_blocksize_fix"]:
            print(f"  Fixing blocksize -> 4096 via flac CLI")
            fp = fix_blocksize(fp)

        print("  Resizing album art to 500x500")
        resize_album_art(fp)

        if args.nolrc:
            continue

        lrc_path = fp.with_suffix(".lrc")
        if lrc_path.exists():
            print(f"  Skipping LRC for {fp.name} (already exists)")
            continue

        print(f"  Fetching LRC for: {title} - {artist}")
        lrc = syncedlyrics.search(f"{title} {artist}", providers=["Lrclib", "Megalobiz", "NetEase"])

        with open(lrc_path, "w", encoding="utf-8") as f:
            f.write(lrc if lrc else "")


if __name__ == "__main__":
    main()
