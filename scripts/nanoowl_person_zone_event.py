#!/usr/bin/env python3
"""Log a NanoOWL person-in-zone event and save an evidence image.

This is the reference solution for Lab 003 task 2.  It opens a CSI camera, USB
camera, or RTSP stream, then applies this strict situation rule:

    A detection for the prompt "a person" has its box center inside a chosen
    image zone continuously for at least three seconds.

When the rule is met, the program appends one JSON Lines event and saves one
annotated JPEG evidence image.  A frame without a matching person in the zone
resets the timer.  RTSP credentials are read only from an environment variable
and are never written to the log or printed by this script.
"""

# argparse reads command-line options and provides automatic --help text.
import argparse
# json writes one structured event per line to the event log.
import json
# os reads the RTSP environment variable without putting it on the command line.
import os
# time.monotonic measures elapsed time safely even if the system clock changes.
import time
# datetime provides human-readable timestamps for the saved evidence and log.
from datetime import datetime
# Path creates result folders and works consistently with file paths.
from pathlib import Path

# OpenCV opens the selected camera and draws the zone and detection on evidence.
import cv2
# NanoOWL receives Pillow RGB images, while OpenCV frames are BGR arrays.
import PIL.Image
from nanoowl.owl_predictor import OwlPredictor


def parse_resolution(value: str) -> tuple[int, int]:
    """Convert a value such as 640x480 into separate width and height numbers."""
    try:
        width_text, height_text = value.lower().split("x", maxsplit=1)
        width, height = int(width_text), int(height_text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "--resolution must be WIDTHxHEIGHT, for example 640x480"
        ) from error

    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("resolution values must be positive")
    return width, height


def parse_zone(value: str) -> tuple[float, float, float, float]:
    """Parse LEFT,TOP,RIGHT,BOTTOM relative coordinates for the monitored zone."""
    try:
        left, top, right, bottom = [float(part.strip()) for part in value.split(",")]
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "--zone must be LEFT,TOP,RIGHT,BOTTOM, for example 0.66,0,1,1"
        ) from error

    # Relative coordinates make one rule work across resolutions.  0 means the
    # left or top image edge, while 1 means the right or bottom image edge.
    if not all(0.0 <= coordinate <= 1.0 for coordinate in (left, top, right, bottom)):
        raise argparse.ArgumentTypeError("--zone values must be between 0 and 1")
    if left >= right or top >= bottom:
        raise argparse.ArgumentTypeError(
            "--zone must have left < right and top < bottom"
        )
    return left, top, right, bottom


def csi_workflow(sensor_id: int, width: int, height: int, framerate: int) -> str:
    """Build the Argus GStreamer workflow used to open a CSI camera."""
    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        f"video/x-raw(memory:NVMM),width=(int){width},height=(int){height},"
        f"format=(string)NV12,framerate=(fraction){framerate}/1 ! "
        f"nvvidconv ! video/x-raw,width=(int){width},height=(int){height},"
        "format=(string)BGRx ! "
        "videoconvert ! video/x-raw,format=(string)BGR ! "
        "appsink drop=true max-buffers=1 sync=false"
    )


def rtsp_workflow(url: str, width: int, height: int, latency: int) -> str:
    """Build an H.264 RTSP workflow without logging the secret URL."""
    return (
        f"rtspsrc location={url} protocols=tcp latency={latency} ! "
        "rtph264depay ! h264parse ! nvv4l2decoder ! "
        f"nvvidconv ! video/x-raw,format=(string)BGRx,width=(int){width},"
        f"height=(int){height} ! videoconvert ! video/x-raw,format=(string)BGR ! "
        "appsink drop=true max-buffers=1 sync=false"
    )


def open_camera(args: argparse.Namespace, width: int, height: int) -> cv2.VideoCapture:
    """Open the selected source and report errors without exposing RTSP details."""
    if args.source == "v4l2":
        # A USB camera is opened by its current V4L2 index, for example 1 for
        # /dev/video1.  The index can change after reconnecting USB devices.
        camera = cv2.VideoCapture(args.camera)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        source_description = f"USB camera index {args.camera}"
    elif args.source == "csi":
        # A CSI camera uses Argus sensor-id, which is not the same thing as the
        # Linux /dev/video0 file that may contain raw Bayer data.
        camera = cv2.VideoCapture(
            csi_workflow(args.sensor_id, width, height, args.framerate),
            cv2.CAP_GSTREAMER,
        )
        source_description = f"CSI camera sensor-id {args.sensor_id}"
    else:
        # The environment variable was created interactively in the terminal.
        # Do not include its value in an error message, status text, or JSON log.
        rtsp_url = os.environ.get(args.rtsp_env)
        if not rtsp_url:
            raise RuntimeError(
                f"The {args.rtsp_env} environment variable is empty. "
                "Set it in the host terminal before starting the container."
            )
        camera = cv2.VideoCapture(
            rtsp_workflow(rtsp_url, width, height, args.latency),
            cv2.CAP_GSTREAMER,
        )
        source_description = "RTSP stream from an environment variable"

    if not camera.isOpened():
        camera.release()
        raise RuntimeError(
            f"Could not open {source_description}. Check the selected source, "
            "camera connection, and that no other program is using it."
        )

    print(f"Opened {source_description}.")
    return camera


def bgr_to_pil(frame):
    """Convert an OpenCV BGR frame to the RGB Pillow image NanoOWL expects."""
    return PIL.Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))


def zone_pixels(zone, frame_width: int, frame_height: int) -> tuple[int, int, int, int]:
    """Convert relative zone values from 0..1 to drawable pixel coordinates."""
    left, top, right, bottom = zone
    return (
        round(left * frame_width),
        round(top * frame_height),
        round(right * frame_width),
        round(bottom * frame_height),
    )


def detection_as_dict(label_tensor, score_tensor, box_tensor, prompt, frame_width, frame_height):
    """Convert one NanoOWL result to JSON-friendly values plus a relative center."""
    # This task uses exactly one prompt.  Keep the label index in the result so
    # a learner can still see that NanoOWL associated the box with that prompt.
    prompt_index = int(label_tensor.item())
    left, top, right, bottom = [
        float(value) for value in box_tensor.detach().cpu().tolist()
    ]
    center_x = (left + right) / 2
    center_y = (top + bottom) / 2

    return {
        "prompt_index": prompt_index,
        "prompt": prompt,
        "score": round(float(score_tensor.item()), 4),
        "bounding_box": {
            "left": round(left, 1),
            "top": round(top, 1),
            "right": round(right, 1),
            "bottom": round(bottom, 1),
            "width": round(right - left, 1),
            "height": round(bottom - top, 1),
        },
        # Relative values make it possible to compare the same zone rule across
        # camera resolutions.  0,0 is top-left and 1,1 is bottom-right.
        "center_relative": {
            "x": round(center_x / frame_width, 4),
            "y": round(center_y / frame_height, 4),
        },
    }


def detection_is_in_zone(detection, zone) -> bool:
    """Return True when the detection box center is inside the chosen zone."""
    left, top, right, bottom = zone
    center = detection["center_relative"]
    return left <= center["x"] <= right and top <= center["y"] <= bottom


def best_detection_in_zone(output, prompt, zone, frame_width, frame_height):
    """Return the highest-scoring person box whose center is inside the zone."""
    candidates = []
    # zip() walks through matching label, score, and box values for every
    # NanoOWL result above the threshold.  With one prompt, label index 0 is
    # expected, but keeping the check makes the function explicit and robust.
    for label, score, box in zip(output.labels, output.scores, output.boxes):
        if int(label.item()) != 0:
            continue
        detection = detection_as_dict(
            label, score, box, prompt, frame_width, frame_height
        )
        if detection_is_in_zone(detection, zone):
            candidates.append(detection)

    # max(..., default=None) returns None when no person center is in the zone.
    return max(candidates, key=lambda detection: detection["score"], default=None)


def draw_evidence(frame, detection, zone):
    """Draw the monitored zone and the selected detection on a copied frame."""
    annotated = frame.copy()
    frame_height, frame_width = annotated.shape[:2]
    zone_left, zone_top, zone_right, zone_bottom = zone_pixels(
        zone, frame_width, frame_height
    )

    # Orange shows the configured zone.  The rectangle is visible in the saved
    # evidence image, so a later reviewer can see why the event was triggered.
    cv2.rectangle(
        annotated, (zone_left, zone_top), (zone_right, zone_bottom), (0, 165, 255), 2
    )
    cv2.putText(
        annotated,
        "monitoring zone",
        (zone_left + 6, max(zone_top + 24, 24)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 165, 255),
        2,
        cv2.LINE_AA,
    )

    box = detection["bounding_box"]
    left, top = round(box["left"]), round(box["top"])
    right, bottom = round(box["right"]), round(box["bottom"])
    # Green shows the person box that satisfied both the prompt and zone rule.
    cv2.rectangle(annotated, (left, top), (right, bottom), (0, 255, 0), 2)
    cv2.putText(
        annotated,
        f"{detection['prompt']} {detection['score']:.2f}",
        (left, max(top - 8, 20)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )
    return annotated


def save_event(log_path, event) -> None:
    """Append one JSON object followed by a newline, forming a JSON Lines log."""
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    # Append mode preserves previous events.  One object per line is convenient
    # because tail, grep, and later Python programs can process events one at a time.
    with open(log_path, "a", encoding="utf-8") as log_file:
        json.dump(event, log_file, ensure_ascii=False)
        log_file.write("\n")


def timestamp_with_offset() -> str:
    """Return local wall-clock time with a UTC offset for a human-readable log."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def evidence_filename() -> str:
    """Create a file-system-safe evidence name with microseconds to avoid clashes."""
    return "person-zone-" + datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%f%z.jpg")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Log a NanoOWL person-in-zone event and save evidence."
    )
    # The engine is positional to match the existing NanoOWL stream-demo command.
    parser.add_argument("image_encoder_engine", help="Path to the TensorRT engine")
    parser.add_argument("--source", choices=("csi", "rtsp", "v4l2"), default="v4l2")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--sensor-id", type=int, default=0)
    parser.add_argument("--resolution", type=parse_resolution, default=(640, 480))
    parser.add_argument("--framerate", type=int, default=30)
    parser.add_argument("--latency", type=int, default=200)
    parser.add_argument("--rtsp-env", default="RTSP_URL")
    parser.add_argument("--prompt", default="a person")
    parser.add_argument("--threshold", type=float, default=0.10)
    parser.add_argument("--duration", type=float, default=3.0)
    parser.add_argument("--zone", type=parse_zone, default=(0.66, 0.0, 1.0, 1.0))
    parser.add_argument("--log", required=True, help="Path to a JSON Lines event log")
    parser.add_argument(
        "--evidence-dir", required=True, help="Folder for annotated JPEG evidence images"
    )
    parser.add_argument("--model", default="google/owlvit-base-patch32")
    args = parser.parse_args()

    # Validate all numeric inputs before the program opens a camera or loads the model.
    if args.framerate <= 0:
        parser.error("--framerate must be positive")
    if args.latency < 0:
        parser.error("--latency cannot be negative")
    if not 0.0 <= args.threshold <= 1.0:
        parser.error("--threshold must be between 0.0 and 1.0")
    if args.duration <= 0:
        parser.error("--duration must be greater than zero")
    if not args.prompt.strip():
        parser.error("--prompt must not be empty")

    width, height = args.resolution
    prompt = args.prompt.strip()
    Path(args.evidence_dir).mkdir(parents=True, exist_ok=True)

    # Encode the one text prompt once.  Reusing it inside the loop avoids doing
    # text-model work for every camera frame and leaves only image inference.
    predictor = OwlPredictor(args.model, image_encoder_engine=args.image_encoder_engine)
    text_encodings = predictor.encode_text([prompt])
    camera = open_camera(args, width, height)

    # These variables store the state of the current uninterrupted person-in-zone
    # sequence.  None means the last usable frame did not satisfy the rule.
    sequence_started_monotonic = None
    sequence_started_timestamp = None
    event_written = False

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                # Unlike a missing detection, a failed camera read means there is
                # no reliable frame to evaluate.  Stop instead of inventing data.
                print("Camera frame read failed; stopping the event monitor.")
                break

            # NanoOWL expects a Pillow RGB image.  OpenCV provides BGR, so the
            # conversion happens for every newly captured frame.
            image = bgr_to_pil(frame)
            output = predictor.predict(
                image=image,
                text=[prompt],
                text_encodings=text_encodings,
                threshold=args.threshold,
                pad_square=False,
            )
            frame_height, frame_width = frame.shape[:2]
            detection = best_detection_in_zone(
                output, prompt, args.zone, frame_width, frame_height
            )
            # Read the monotonic clock once per frame for stable elapsed-time math.
            now_monotonic = time.monotonic()

            if detection is not None:
                if sequence_started_monotonic is None:
                    # A person has just entered the zone.  Keep a monotonic time
                    # for duration math and a wall-clock timestamp for the log.
                    sequence_started_monotonic = now_monotonic
                    sequence_started_timestamp = timestamp_with_offset()
                    event_written = False
                    print("Person-in-zone sequence started.")

                elapsed = now_monotonic - sequence_started_monotonic
                if elapsed >= args.duration and not event_written:
                    evidence_name = evidence_filename()
                    evidence_path = Path(args.evidence_dir) / evidence_name
                    annotated = draw_evidence(frame, detection, args.zone)
                    if not cv2.imwrite(str(evidence_path), annotated):
                        raise RuntimeError(f"Could not save evidence image {evidence_path}")

                    # The log deliberately stores source type, not an RTSP URL or
                    # camera address.  JSON Lines keeps every event self-contained.
                    event = {
                        "event": "person_in_zone",
                        "started_at": sequence_started_timestamp,
                        "confirmed_at": timestamp_with_offset(),
                        "source": args.source,
                        "prompt": prompt,
                        "threshold": args.threshold,
                        "duration_seconds": args.duration,
                        "zone": {
                            "left": args.zone[0],
                            "top": args.zone[1],
                            "right": args.zone[2],
                            "bottom": args.zone[3],
                        },
                        "detection": detection,
                        "evidence_image": evidence_name,
                    }
                    save_event(args.log, event)
                    event_written = True
                    print(
                        f"Logged person-in-zone event after {elapsed:.1f} seconds: "
                        f"{evidence_path}"
                    )
            else:
                if sequence_started_monotonic is not None:
                    # One frame without a matching center-in-zone detection resets
                    # this first strict version of the situation rule.
                    print("Person-in-zone sequence reset.")
                sequence_started_monotonic = None
                sequence_started_timestamp = None
                event_written = False
    except KeyboardInterrupt:
        # Ctrl+C is the normal way to stop a live camera experiment.
        print("Stopped by user.")
    finally:
        # Release the camera even after Ctrl+C or an exception, so another lab
        # command can open the same CSI or USB camera afterwards.
        camera.release()


if __name__ == "__main__":
    main()
