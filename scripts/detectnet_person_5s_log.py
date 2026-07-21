#!/usr/bin/env python3
"""Log an event when detectNet sees a person continuously for five seconds.

Run this script inside the jetson-inference container.  The default target is
the SSD Mobilenet v2 COCO class "person".  A missing detection resets the
timer, so the first version of the rule is intentionally strict and easy to
reason about.
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

from jetson_inference import detectNet
from jetson_utils import videoOutput, videoSource


def current_timestamp():
    """Return local time with a UTC offset for a log that can be compared later."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def append_event(log_path, started_at):
    """Append exactly the requested event line and keep earlier events intact."""
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"{started_at} Inimene tuvastatud!\n")


def main():
    parser = argparse.ArgumentParser(
        description="Log when a detectNet class remains visible for a duration."
    )
    parser.add_argument("--input", required=True, help="Camera, RTSP, or video URI")
    parser.add_argument("--log", required=True, help="Host-mounted event log path")
    parser.add_argument(
        "--output",
        default="",
        help="Optional video output URI, for example /detectnet-results/person.mp4",
    )
    parser.add_argument("--network", default="ssd-mobilenet-v2")
    parser.add_argument("--threshold", type=float, default=0.50)
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--target-class", default="person")
    parser.add_argument("--overlay", default="box,labels,conf")
    args = parser.parse_args()

    if not 0.0 <= args.threshold <= 1.0:
        parser.error("--threshold must be between 0.0 and 1.0")
    if args.duration <= 0:
        parser.error("--duration must be greater than zero")

    # Use the same URI interface as the detectnet console program.
    source = videoSource(args.input, argv=sys.argv)
    output = videoOutput(args.output, argv=sys.argv) if args.output else None
    # Keep this script's event-rule arguments separate from detectNet options.
    detectnet_argv = [
        sys.argv[0],
        f"--network={args.network}",
        f"--confidence={args.threshold}",
    ]
    network = detectNet(args.network, detectnet_argv, args.threshold)

    target_class = args.target_class.casefold()
    sequence_started_monotonic = None
    sequence_started_timestamp = None
    event_written = False

    try:
        while True:
            image = source.Capture()
            if image is None:
                # A capture timeout is not proof that the person disappeared.
                # A finite video file also reports end-of-stream this way.
                if not source.IsStreaming():
                    break
                continue

            detections = network.Detect(image, overlay=args.overlay)
            target_visible = any(
                network.GetClassDesc(detection.ClassID).casefold() == target_class
                for detection in detections
            )
            now_monotonic = time.monotonic()

            if target_visible:
                if sequence_started_monotonic is None:
                    # Keep both clocks: monotonic measures elapsed time reliably,
                    # while the wall-clock timestamp is useful in the event log.
                    sequence_started_monotonic = now_monotonic
                    sequence_started_timestamp = current_timestamp()
                    event_written = False
                    print("Person detection sequence started.")

                elapsed = now_monotonic - sequence_started_monotonic
                if elapsed >= args.duration and not event_written:
                    append_event(args.log, sequence_started_timestamp)
                    event_written = True
                    print(
                        f"Logged person event after {elapsed:.1f} seconds: "
                        f"{sequence_started_timestamp} Inimene tuvastatud!"
                    )
            else:
                if sequence_started_monotonic is not None:
                    print("Person detection sequence reset.")
                sequence_started_monotonic = None
                sequence_started_timestamp = None
                event_written = False

            if output is not None:
                output.Render(image)
                output.SetStatus(
                    f"{args.network} | {network.GetNetworkFPS():.0f} FPS"
                )

            if output is not None and not output.IsStreaming():
                break

            # Check end-of-stream after processing the final available frame.
            if not source.IsStreaming():
                break
    except KeyboardInterrupt:
        print("Stopped by user.")


if __name__ == "__main__":
    main()
