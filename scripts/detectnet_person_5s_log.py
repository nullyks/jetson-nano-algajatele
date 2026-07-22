#!/usr/bin/env python3
"""Log an event when detectNet sees a class continuously for five seconds.

This is the reference solution for Lab 002 task 2.  Run it inside the
jetson-inference container.  By default the target is the SSD Mobilenet v2
COCO class "person".  Every processed frame must contain that class until the
chosen duration has passed.  One missing frame resets the timer, so this first
version of the situation rule is deliberately strict and easy to reason about.
"""

# argparse turns command-line options into Python values and creates --help.
import argparse
# sys.argv is used when passing a separate option list to detectNet.
import sys
# time.monotonic measures elapsed time without being affected by clock changes.
import time
# datetime supplies the human-readable local timestamp in the event log.
from datetime import datetime
# Path creates the log folder when it does not exist yet.
from pathlib import Path

# detectNet performs the object detection for every received frame.
from jetson_inference import detectNet
# videoSource opens cameras, files, and RTSP URIs.  videoOutput is optional.
from jetson_utils import videoOutput, videoSource


def current_timestamp():
    """Return local time with its UTC offset for the human-readable event log."""
    # astimezone() adds the local UTC offset, for example +03:00.  The offset
    # prevents ambiguity if log files are later compared across timezones.
    return datetime.now().astimezone().isoformat(timespec="seconds")


def append_event(log_path, started_at):
    """Append one event line without removing earlier events from the log."""
    # The output folder is host-mounted in Lab 002.  Creating it here allows
    # the script to be run directly even if the learner skipped mkdir -p first.
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    # Mode "a" means append: Python creates the file if it is missing and adds
    # the new line after earlier events if the file already exists.
    with open(log_path, "a", encoding="utf-8") as log_file:
        # Keep this exact Estonian text because it is the required task output.
        log_file.write(f"{started_at} Inimene tuvastatud!\n")


def main():
    # First describe all values that the learner may set on the command line.
    # parse_args() below stores the selected values in the ``args`` object.
    parser = argparse.ArgumentParser(
        description="Log when a detectNet class remains visible for a duration."
    )
    # A URI can be /dev/video1, csi://0, an RTSP variable, or a video file.
    parser.add_argument("--input", required=True, help="Camera, RTSP, or video URI")
    # The log path normally points to /detectnet-results, a host-mounted folder.
    parser.add_argument("--log", required=True, help="Host-mounted event log path")
    parser.add_argument(
        "--output",
        default="",
        help="Optional video output URI, for example /detectnet-results/person.mp4",
    )
    # --output is optional.  Without it, frames are analysed but not saved.
    # type=float converts the two numeric text options into Python numbers.
    parser.add_argument("--network", default="ssd-mobilenet-v2")
    parser.add_argument("--threshold", type=float, default=0.50)
    parser.add_argument("--duration", type=float, default=5.0)
    # This is a detectNet class name, not a free-form NanoOWL text prompt.
    parser.add_argument("--target-class", default="person")
    parser.add_argument("--overlay", default="box,labels,conf")
    args = parser.parse_args()

    # Validate user input before opening a camera or loading the neural network.
    if not 0.0 <= args.threshold <= 1.0:
        parser.error("--threshold must be between 0.0 and 1.0")
    if args.duration <= 0:
        parser.error("--duration must be greater than zero")

    # videoSource gives cameras, RTSP streams, videos, and image sequences one
    # common interface.  This is why changing only --input changes the source.
    source = videoSource(args.input, argv=sys.argv)
    # Create an output object only when --output was supplied.  ``None`` is the
    # Python value for "no object here", and later if-statements check for it.
    output = videoOutput(args.output, argv=sys.argv) if args.output else None
    # detectNet parses its own command-line-like options.  Keep the situation
    # rule options (--duration and --target-class) separate because detectNet
    # would not recognise them.  The first list item acts as a program name.
    detectnet_argv = [
        sys.argv[0],
        f"--network={args.network}",
        f"--confidence={args.threshold}",
    ]
    # The last argument is also part of the detectNet Python API signature.
    network = detectNet(args.network, detectnet_argv, args.threshold)

    # casefold() is a thorough case-insensitive comparison.  It lets a user
    # type PERSON or Person while still comparing against the model's "person".
    target_class = args.target_class.casefold()
    # These three variables describe the current uninterrupted detection run.
    # None means that the target class was not visible in the previous frame.
    sequence_started_monotonic = None
    sequence_started_timestamp = None
    # This flag prevents one long detection run from writing the same event on
    # every frame after the five-second limit has been reached.
    event_written = False

    try:
        while True:
            # Capture waits for the next frame and returns it in CUDA-accessible
            # memory.  ``image`` is then passed directly to detectNet.
            image = source.Capture()
            if image is None:
                # A capture timeout is not proof that the person disappeared.
                # A finite video file also reports end-of-stream this way.
                if not source.IsStreaming():
                    # For a file, there are no more frames left to process.
                    break
                # For a live camera, wait for another frame without resetting
                # the situation timer because no actual negative frame arrived.
                continue

            # Detect returns a list of all objects above the confidence threshold.
            # When an overlay was requested, it also draws on this same frame.
            detections = network.Detect(image, overlay=args.overlay)
            # any(...) is True when at least one detection has the requested
            # class name.  It stops checking as soon as it finds a match.
            target_visible = any(
                network.GetClassDesc(detection.ClassID).casefold() == target_class
                for detection in detections
            )
            # Read the monotonic clock once per frame so all decisions below use
            # the same reference time.
            now_monotonic = time.monotonic()

            if target_visible:
                if sequence_started_monotonic is None:
                    # This is the state change from "not visible" to "visible".
                    # Keep two clocks: monotonic measures elapsed time reliably,
                    # while the wall-clock timestamp tells a person when the run
                    # began.  A system time adjustment cannot affect monotonic.
                    sequence_started_monotonic = now_monotonic
                    sequence_started_timestamp = current_timestamp()
                    event_written = False
                    print("Person detection sequence started.")

                # Because the start time is no longer None, subtraction gives
                # the length of the uninterrupted visible sequence in seconds.
                elapsed = now_monotonic - sequence_started_monotonic
                if elapsed >= args.duration and not event_written:
                    # Write once at the requested duration.  On the next frame
                    # event_written is True, so no duplicate row is appended.
                    append_event(args.log, sequence_started_timestamp)
                    event_written = True
                    print(
                        f"Logged person event after {elapsed:.1f} seconds: "
                        f"{sequence_started_timestamp} Inimene tuvastatud!"
                    )
            else:
                if sequence_started_monotonic is not None:
                    # A real frame without the target breaks the strict rule.
                    # The next positive frame must therefore start a new run.
                    print("Person detection sequence reset.")
                sequence_started_monotonic = None
                sequence_started_timestamp = None
                event_written = False

            if output is not None:
                # Render writes the already annotated frame to the optional
                # video destination.  It does not change the event decision.
                output.Render(image)
                # SetStatus is metadata for a display/output window and helps
                # verify which network and approximate frame rate are in use.
                output.SetStatus(
                    f"{args.network} | {network.GetNetworkFPS():.0f} FPS"
                )

            if output is not None and not output.IsStreaming():
                # Stop if a video output file or display has been closed.
                break

            # Check end-of-stream after processing the final available frame so
            # a finite video file cannot lose its last detection.
            if not source.IsStreaming():
                break
    except KeyboardInterrupt:
        # Ctrl+C is normal for a live camera.  Catch it so the terminal prints a
        # friendly message instead of a long Python traceback.
        print("Stopped by user.")


if __name__ == "__main__":
    # Run main() only when this file is executed directly, not when imported.
    main()
