#!/usr/bin/env python3
"""Compare several NanoOWL text prompts on one still image.

This is the reference solution for Lab 003 task 1.  It sends one image to the
same NanoOWL model with the default prompts ``a person``, ``a face``, and
``a hand``.  The program writes two outputs:

* a JSON file that another program can read later;
* an annotated image that a person can inspect visually.

Run this script inside the NanoOWL container.  The TensorRT engine path and
the output paths normally point to folders mounted from the Jetson host.
"""

# argparse turns command-line options into Python values and creates --help.
import argparse
# json writes dictionaries and lists as a portable JSON text file.
import json
# datetime supplies a UTC timestamp for the result metadata.
from datetime import datetime, timezone
# Path creates output folders and extracts a file name from an input path.
from pathlib import Path

# Pillow opens the input JPEG and represents it as a Python image object.
import PIL.Image
# The official drawing helper adds NanoOWL boxes, labels, and scores to an image.
from nanoowl.owl_drawing import draw_owl_output
# OwlPredictor loads OWL-ViT and uses the previously built TensorRT engine.
from nanoowl.owl_predictor import OwlPredictor


# The exercise deliberately starts with three prompts that can produce very
# different results on the same image.  These are prompt descriptions, not
# biometric identification and not a guarantee that a face or hand is found.
DEFAULT_PROMPTS = ["a person", "a face", "a hand"]


def detection_as_dict(label_tensor, score_tensor, box_tensor, prompts):
    """Convert one NanoOWL tensor result into ordinary JSON values.

    NanoOWL returns PyTorch tensors, which may live in GPU memory.  JSON cannot
    store tensors directly, so this function copies each value to normal Python
    numbers and records which text prompt produced the detection.
    """
    # labels contains the index of the winning prompt.  For example, index 0
    # means the first text in ``prompts``, which is ``a person`` by default.
    prompt_index = int(label_tensor.item())
    # detach() disconnects the value from PyTorch's calculation graph and cpu()
    # makes the four box coordinates available as ordinary Python data.
    left, top, right, bottom = [
        float(value) for value in box_tensor.detach().cpu().tolist()
    ]

    return {
        "prompt_index": prompt_index,
        "prompt": prompts[prompt_index],
        # NanoOWL returns a prompt-dependent model score from 0 to 1.  It is a
        # useful comparison aid, but it is not proof that the object is present.
        "score": round(float(score_tensor.item()), 4),
        "bounding_box": {
            # Coordinates are measured in pixels from the image top-left corner.
            "left": round(left, 1),
            "top": round(top, 1),
            "right": round(right, 1),
            "bottom": round(bottom, 1),
            "width": round(right - left, 1),
            "height": round(bottom - top, 1),
        },
    }


def main() -> None:
    # Define the command-line interface before loading the large NanoOWL model.
    parser = argparse.ArgumentParser(
        description="Compare NanoOWL text prompts on one still image."
    )
    parser.add_argument("--input", required=True, help="Input JPEG file path")
    parser.add_argument(
        "--engine",
        required=True,
        help="Path to the previously built NanoOWL TensorRT engine",
    )
    parser.add_argument(
        "--output-json", required=True, help="Path for the JSON result file"
    )
    parser.add_argument(
        "--output-image", required=True, help="Path for the annotated JPEG"
    )
    # nargs="+" accepts one or more values after --prompts.  Quotes are needed
    # around prompts with spaces, for example "a person".
    parser.add_argument(
        "--prompts",
        nargs="+",
        default=DEFAULT_PROMPTS,
        help="One or more quoted English prompts; default: a person, a face, a hand",
    )
    parser.add_argument("--threshold", type=float, default=0.10)
    parser.add_argument("--model", default="google/owlvit-base-patch32")
    args = parser.parse_args()

    # Reject impossible scores before loading the model or creating output files.
    if not 0.0 <= args.threshold <= 1.0:
        parser.error("--threshold must be between 0.0 and 1.0")

    # Remove accidental leading/trailing spaces.  An empty prompt would make the
    # result difficult to interpret, so stop with a clear argument error.
    prompts = [prompt.strip() for prompt in args.prompts if prompt.strip()]
    if not prompts:
        parser.error("--prompts must contain at least one non-empty prompt")

    # The output folders are normally mounted from the Jetson host.  Creating
    # them makes the script safe to run even if mkdir -p was skipped beforehand.
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_image).parent.mkdir(parents=True, exist_ok=True)

    # Convert to RGB once.  JPEG images can contain other modes, but NanoOWL and
    # the drawing helper expect a normal three-channel RGB Pillow image.
    with PIL.Image.open(args.input) as input_image:
        image = input_image.convert("RGB")

    # Loading the predictor connects the model to the TensorRT image encoder.
    # The engine must match the model architecture used when it was built.
    predictor = OwlPredictor(args.model, image_encoder_engine=args.engine)
    # Text encodings depend only on the prompts, not on the image.  Encoding
    # them once is faster and demonstrates how later video code avoids repeat
    # work on every frame.
    text_encodings = predictor.encode_text(prompts)
    # pad_square=False keeps the output boxes in the original image proportions.
    output = predictor.predict(
        image=image,
        text=prompts,
        text_encodings=text_encodings,
        threshold=args.threshold,
        pad_square=False,
    )

    # zip() walks through matching label, score, and box tensors together.  The
    # list can be empty when no prompt produces a score above the chosen limit.
    detections = [
        detection_as_dict(label, score, box, prompts)
        for label, score, box in zip(output.labels, output.scores, output.boxes)
    ]

    # draw_owl_output is NanoOWL's official annotation helper.  It returns a
    # new Pillow image, leaving ``image`` available as the unmodified input.
    annotated_image = draw_owl_output(image.copy(), output, text=prompts, draw_text=True)
    annotated_image.save(args.output_image)

    # This dictionary becomes the complete JSON document.  The prompt list is
    # saved too, so a later reader knows exactly what NanoOWL was asked to find.
    result = {
        "image_name": Path(args.input).name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "engine_name": Path(args.engine).name,
        "threshold": args.threshold,
        "prompts": prompts,
        "detections": detections,
    }

    # ``with open`` closes the file automatically, including if JSON writing
    # fails.  indent=2 keeps the file readable in a terminal or text editor.
    with open(args.output_json, "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, indent=2, ensure_ascii=False)
        json_file.write("\n")

    print(f"Saved {len(detections)} NanoOWL detections to {args.output_json}")
    print(f"Saved annotated image to {args.output_image}")


if __name__ == "__main__":
    # Do not run main() automatically if another Python file imports this one.
    main()
