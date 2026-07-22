#!/usr/bin/env python3
"""Save detections from one still image as JSON and an annotated JPEG.

This is the reference solution for Lab 002 task 1.  Run it inside the
jetson-inference container.  The program has one input image and two outputs:

* a JSON file for another program to read later;
* a JPEG image with bounding boxes, labels, and confidence values drawn on it.

It intentionally uses the same SSD Mobilenet v2 model and overlay settings as
the earlier detectnet examples in Lab 002.
"""

# argparse reads options such as --input and --threshold from the command line.
# It also creates the automatic --help text shown to the learner.
import argparse
# json converts Python dictionaries and lists into a JSON text file.
import json
# sys.argv contains the exact command-line words used to start this script.
import sys
# datetime supplies the UTC timestamp stored in the result file.
from datetime import datetime, timezone
# Path makes file and folder paths easier to handle than plain text strings.
from pathlib import Path

# detectNet loads the neural network and returns its object detections.
from jetson_inference import detectNet
# videoSource reads a file or a camera URI.  saveImage writes the CUDA image.
from jetson_utils import saveImage, videoSource


def detection_as_dict(detection, network):
    """Convert one detectNet Detection object into ordinary JSON data.

    ``detection`` is an object supplied by jetson-inference.  JSON cannot save
    that Python/CUDA object directly, so this function picks out the useful
    values and puts them in a dictionary made only of numbers and text.
    """
    # The four coordinates describe the bounding box in image pixels.  The
    # origin (0, 0) is at the top-left corner of the input image.
    left = float(detection.Left)
    top = float(detection.Top)
    right = float(detection.Right)
    bottom = float(detection.Bottom)

    # A Python dictionary uses a name (the key) for each value.  json.dump()
    # later turns this nested dictionary into the JSON object in the result.
    return {
        # ClassID is a numeric model-internal identifier.  GetClassDesc()
        # translates it to a human-readable COCO class name such as "person".
        "class_id": int(detection.ClassID),
        "class_name": network.GetClassDesc(detection.ClassID),
        # Confidence is a number from 0 to 1.  Four decimal places retain
        # useful precision while keeping the JSON file easy to read.
        "confidence": round(float(detection.Confidence), 4),
        "bounding_box": {
            "left": round(left, 1),
            "top": round(top, 1),
            "right": round(right, 1),
            "bottom": round(bottom, 1),
            # Width and height are derived values.  Saving them avoids making
            # a later program repeat the right-left and bottom-top calculation.
            "width": round(right - left, 1),
            "height": round(bottom - top, 1),
        },
    }


def main():
    # ArgumentParser describes the command-line interface before any camera or
    # model work starts.  ``args`` below will hold the values chosen by the user.
    parser = argparse.ArgumentParser(
        description="Write detectNet image detections to JSON and an annotated image."
    )
    # required=True means that Python stops with a clear help message if the
    # learner forgets one of these essential output or input paths.
    parser.add_argument("--input", required=True, help="Input image path or URI")
    parser.add_argument(
        "--output-json", required=True, help="Path for the JSON result file"
    )
    parser.add_argument(
        "--output-image", required=True, help="Path for the annotated image file"
    )
    # These options have defaults, so the short Lab 002 command can omit them.
    # type=float converts text such as "0.50" into the Python number 0.5.
    parser.add_argument("--network", default="ssd-mobilenet-v2")
    parser.add_argument("--threshold", type=float, default=0.50)
    # overlay is passed to detectNet.  It selects what is drawn on the JPEG.
    parser.add_argument("--overlay", default="box,labels,conf")
    args = parser.parse_args()

    # A confidence threshold is a probability-like value.  Rejecting impossible
    # values here gives a helpful error before the model has been loaded.
    if not 0.0 <= args.threshold <= 1.0:
        parser.error("--threshold must be between 0.0 and 1.0")

    # Path(...).parent is the folder containing a file path.  mkdir(...,
    # exist_ok=True) creates that folder if needed and succeeds harmlessly if
    # it already exists.  In Lab 002 these folders are mounted from the Jetson
    # host, so the results survive after the container is closed.
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_image).parent.mkdir(parents=True, exist_ok=True)

    # videoSource has one interface for files, cameras, and RTSP streams.  This
    # task deliberately gives it a JPEG file, so Capture() is called only once.
    # The returned image is stored in CUDA-accessible memory for detectNet.
    source = videoSource(args.input, argv=sys.argv)
    image = source.Capture()
    if image is None:
        # A clear exception is better than trying to run the model on a missing
        # image and receiving a later, less understandable CUDA error.
        raise RuntimeError("The input image could not be read.")

    # detectNet also parses command-line-like options.  Do not pass the whole
    # sys.argv list to it: that list contains this script's --input and output
    # options, which detectNet does not understand.  Instead create its small,
    # separate argument list.  The first item conventionally acts as a program
    # name.  detectNet expects --network=VALUE, while argparse accepts both
    # --network VALUE and --network=VALUE.
    detectnet_argv = [
        sys.argv[0],
        f"--network={args.network}",
        f"--confidence={args.threshold}",
    ]
    # The first argument selects the model.  The final threshold argument is
    # supplied as well because this is the detectNet Python API signature.
    network = detectNet(args.network, detectnet_argv, args.threshold)
    # Detect returns a Python list of Detection objects.  With an overlay,
    # detectNet also draws directly on ``image``; it does not create a second
    # image variable for the marked-up result.
    detections = network.Detect(image, overlay=args.overlay)

    # Save only after Detect(), because Detect() has now added boxes and labels
    # to this same CUDA image.  The original input file is never overwritten.
    saveImage(args.output_image, image)

    # This top-level dictionary becomes the complete JSON document.  UTC makes
    # the generation time comparable even when results come from other timezones.
    result = {
        "image_name": Path(args.input).name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "network": args.network,
        "threshold": args.threshold,
        # A list comprehension calls detection_as_dict once for every object
        # that passed the threshold.  An empty detection list is valid JSON and
        # simply means that the model found no sufficiently confident objects.
        "detections": [
            detection_as_dict(detection, network) for detection in detections
        ],
    }

    # ``with open`` closes the file automatically, even if writing fails.  UTF-8
    # and ensure_ascii=False allow future class labels or notes to contain
    # ordinary non-ASCII text without turning it into escape sequences.
    with open(args.output_json, "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, indent=2, ensure_ascii=False)
        # json.dump does not add a final newline by itself.  Adding one makes
        # the file pleasant to inspect with terminal tools and version control.
        json_file.write("\n")

    # These messages are for the human running the command.  They are not part
    # of the JSON result and make it easy to see where the two files were saved.
    print(f"Saved {len(detections)} detections to {args.output_json}")
    print(f"Saved annotated image to {args.output_image}")


if __name__ == "__main__":
    # Python sets __name__ to "__main__" only when this file is started directly.
    # This keeps main() from running automatically if another script imports it.
    main()
