#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

input_dir="$1"

find "$input_dir" -type d | while read -r dir; do
    image=""
    for ext in jpg JPG jpeg JPEG png PNG; do
        found=$(find "$dir" -maxdepth 1 -type f -name "*.${ext}" | head -n 1)
        if [[ -n "${found:-}" ]]; then
            image="$found"
            break
        fi
    done
    [[ -z "$image" ]] && continue
    echo "Processing folder: $dir"
    echo "Using image: $image"

    ext_lower="${image##*.}"
    ext_lower="${ext_lower,,}"
    if [[ "$ext_lower" == "png" ]]; then
        mimetype="image/png"
        suffix=".png"
    else
        mimetype="image/jpeg"
        suffix=".jpg"
    fi

    temp_cover="$(mktemp --suffix=${suffix})"
    ffmpeg -y -i "$image" \
        -vf "scale=500:500:force_original_aspect_ratio=decrease,pad=500:500:(ow-iw)/2:(oh-ih)/2" \
        "$temp_cover" >/dev/null 2>&1
    find "$dir" -maxdepth 1 -type f -iname "*.flac" | while read -r flac; do
        echo "Tagging: $flac"

        metaflac --remove --block-type=PICTURE "$flac"
        metaflac --import-picture-from="3|${mimetype}|||$temp_cover" "$flac"
    done

    rm -f "$temp_cover"
done
