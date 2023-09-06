# -*- coding: utf-8 -*-

from flask import Flask, request, send_file
import os
import cherrypy
import argparse
import logging
import whisper_timestamped as whisper
from whisper.utils import get_writer

app = Flask(__name__)

upload_folder = "uploads"
os.makedirs(upload_folder, exist_ok=True)
output_directory = "output"
os.makedirs(output_directory, exist_ok=True)


def remove_keys(list_of_dicts, key):
    for d in list_of_dicts:
        yield {k: d[k] for k in d.keys() - {key}}


accurate_args = {
    "beam_size": 5,
    "best_of": 5,
    "temperature": (0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
}

device = "cpu"
model_name = "large"
accurate = False
vad = True
detect_disfluencies = True


@app.route("/transcribe", methods=["POST"])
def transcribe(task="transcribe"):
    if "file" not in request.files:
        return "Missing file", 400
    up_file = request.files["file"]

    settings = {}
    for key in request.form.keys():
        settings[key] = request.form[key]

    # save the file
    filename = up_file.filename
    file_path = os.path.join(upload_folder, filename)
    up_file.save(file_path)
    logging.info(f"Saved file to {file_path}")
    file_path = os.path.abspath(file_path).replace("\\", "/")
    video_prefix = os.path.splitext(os.path.basename(file_path))[0]

    out_format = settings.get("format", "srt")

    logging.info(f"Transcribing {file_path} to format {out_format}")
    audio = whisper.load_audio(file_path)
    
    args = {}
    args["task"] = task
    args["vad"] = vad
    args["detect_disfluencies"] = detect_disfluencies
    if accurate:
        args.update(accurate_args)
    logging.info(f"Transcribing with args {args}")
    result = whisper.transcribe(app.model, audio, **args)

    writer = get_writer(out_format, str(output_directory))
    processed = list(remove_keys(result["segments"], "words"))
    out_path = os.path.join(output_directory, video_prefix + "." + out_format)
    logging.info(f"Writing file to {out_path}")

    with open(out_path, "w") as f:
        writer.write_result({"segments": processed}, f)

    logging.info(f"Returning file {out_path}")
    return send_file(out_path), 200


@app.route("/translate", methods=["POST"])
def translate():
    return transcribe(task="translate")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", help="select the model to use", default="large")
    parser.add_argument("--device", help="select the device to use", default="cpu")
    parser.add_argument("--port", help="select the port to use", default=5000)
    parser.add_argument(
        "--max-size", help="select the max size to use", default=1024 * 1024 * 1024
    )
    parser.add_argument("--vad", help="use vad", action="store_true")
    parser.add_argument(
        "--detect_disfluencies", help="detect disfluencies", action="store_true"
    )
    parser.add_argument("--accurate", help="use accurate mode", action="store_true")
    args = parser.parse_args()
    if args.port:
        port = int(args.port)
    if args.max_size:
        max_size = int(args.max_size)
    if args.model:
        model_name = str(args.model)
    if args.device:
        device = str(args.device)
    if args.vad:
        vad = True
    else:
        vad = False
    if args.detect_disfluencies:
        detect_disfluencies = True
    else:
        detect_disfluencies = False
    if args.accurate:
        accurate = True
    else:
        accurate = False
    logging.info(f"Loading model {model_name} on device {device}")
    app.model = whisper.load_model(model_name, device=device)
    cherrypy.tree.graft(app, "/")
    cherrypy.config.update(
        {
            "server.socket_host": "0.0.0.0",
            "server.socket_port": port,
            "engine.autoreload.on": True,
            "server.max_request_body_size": max_size,
        }
    )
    logging.info(
        f"Starting server on port {port}, max size {max_size}, model {model_name}, device {device}, vad {vad}, detect_disfluencies {detect_disfluencies}, accurate {accurate}"
    )
    cherrypy.engine.start()
    cherrypy.engine.block()
