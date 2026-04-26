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
    temp_cover="$(mktemp --suffix=.jpg)"
    ffmpeg -y -i "$image" \
        -vf "scale=500:500:force_original_aspect_ratio=decrease,pad=500:500:(ow-iw)/2:(oh-ih)/2" \
        "$temp_cover" >/dev/null 2>&1
    find "$dir" -maxdepth 1 -type f -iname "*.flac" | while read -r flac; do
        echo "Tagging: $flac"

        metaflac \
            --remove-tag=METADATA_BLOCK_PICTURE \
            --import-picture-from="$temp_cover" \
            "$flac"
    done

    rm -f "$temp_cover"
done
