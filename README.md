# whisper-timestamped-WebAPI

Build whisper-timestamped docker image that supports WebAPI.

Designed to be used with [AV2Sub](https://github.com/HAL9000COM/AV2Sub).

Tested on Windows WSL2 with cpu.

Original project:
[whisper-timestamped](https://github.com/linto-ai/whisper-timestamped)

## Usage

Change settings in docker-compose.yml

start container with

    docker compose --profile web-cpu up --build

or

    docker compose --profile web-gpu up --build

## API

API is available at <http://localhost:5000/transcribe> and <http://localhost:5000/translate>.

Only support subtitle transcribe now. Translate seems to be broken.

### Example

    curl -X POST      -H "Content-Type: multipart/form-data"      -F "file=@test.mkv"      -F "format=srt"      <http://localhost:5000/translate>

return string

    1
    00:00:00,000 --> 00:00:01,000
    Hello world
