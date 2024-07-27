#!/bin/sh
set -eu -o pipefail
set -x

# WORKED:
# https://trac.ffmpeg.org/wiki/EncodingForStreamingSites#Withoutscalingtheoutput

VIDEO_BITRATE="6000k"
PRESET=ultrafast
FPS=30

# -f s16le -ac 1 -ar 24000 -i fifo_audio

# TODO: remove in docker
rm -f audio.socket video.socket

./script.py &
PYTHON_PID=$!

killpython() {
    kill $PYTHON_PID
}

trap 'killpython' SIGINT

until [ -e ./audio.socket ]; do sleep 0.1; done

ls -la


ffmpeg \
    -f s16le -ac 1 -ar 24000 -i "unix://$PWD/audio.socket" \
    -f rawvideo -pix_fmt rgb24 -framerate $FPS -video_size 1920x1080 -i "unix://$PWD/video.socket" \
    -c:v libx264 \
    -preset veryfast \
    -b:v $VIDEO_BITRATE \
    -maxrate $VIDEO_BITRATE \
    -bufsize 10M \
    -vf "format=yuv420p" \
    -g $(($FPS * 2)) \
    -c:a aac \
    -b:a 128k \
    -ac 2 \
    -ar 24000 \
    -crf 20 \
    -f flv \
    "$RTMP_STREAM_URL"
