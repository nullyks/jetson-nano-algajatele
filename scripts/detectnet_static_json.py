#!/usr/bin/env python3
"""Save detectNet detections from one image as JSON and an annotated JPEG.

Run this script inside the jetson-inference container.  It intentionally uses
the same SSD Mobilenet v2 model and overlay settings as Lab 002.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from jetson_inference import detectNet
from jetson_utils import saveImage, videoSource


def detection_as_dict(detection, network):
    """Convert one jetson-inference Detection object to JSON-safe values."""
    left = float(detection.Left)
    top = float(detection.Top)
    right = float(detection.Right)
    bottom = float(detection.Bottom)

    return {
        "class_id": int(detection.ClassID),
        "class_name": network.GetClassDesc(detection.ClassID),
        "confidence": round(float(detection.Confidence), 4),
        "bounding_box": {
            "left": round(left, 1),
            "top": round(top, 1),
            "right": round(right, 1),
            "bottom": round(bottom, 1),
            "width": round(right - left, 1),
            "height": round(bottom - top, 1),
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Write detectNet image detections to JSON and an annotated image."
    )
    parser.add_argument("--input", required=True, help="Input image path or URI")
    parser.add_argument(
        "--output-json", required=True, help="Path for the JSON result file"
    )
    parser.add_argument(
        "--output-image", required=True, help="Path for the annotated image file"
    )
    parser.add_argument("--network", default="ssd-mobilenet-v2")
    parser.add_argument("--threshold", type=float, default=0.50)
    parser.add_argument("--overlay", default="box,labels,conf")
    args = parser.parse_args()

    if not 0.0 <= args.threshold <= 1.0:
        parser.error("--threshold must be between 0.0 and 1.0")

    # The output folders are host-mounted paths in the Lab 002 command.
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_image).parent.mkdir(parents=True, exist_ok=True)

    # videoSource can load a JPEG just like it opens a camera URI. Capture once.
    source = videoSource(args.input, argv=sys.argv)
    image = source.Capture()
    if image is None:
        raise RuntimeError("The input image could not be read.")

    # Detect modifies the CUDA image in place when an overlay is requested.
    # Do not pass this script's --input/--output arguments to detectNet.
    # Its parser expects --network=VALUE, while argparse also accepts a space.
    detectnet_argv = [
        sys.argv[0],
        f"--network={args.network}",
        f"--confidence={args.threshold}",
    ]
    network = detectNet(args.network, detectnet_argv, args.threshold)
    detections = network.Detect(image, overlay=args.overlay)

    # Save the modified CUDA image after detectNet has drawn boxes and labels.
    saveImage(args.output_image, image)

    result = {
        "image_name": Path(args.input).name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "network": args.network,
        "threshold": args.threshold,
        "detections": [
            detection_as_dict(detection, network) for detection in detections
        ],
    }

    with open(args.output_json, "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, indent=2, ensure_ascii=False)
        json_file.write("\n")

    print(f"Saved {len(detections)} detections to {args.output_json}")
    print(f"Saved annotated image to {args.output_image}")


if __name__ == "__main__":
    main()
