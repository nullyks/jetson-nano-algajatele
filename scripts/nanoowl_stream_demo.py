#!/usr/bin/env python3
"""NanoOWL browser demo with CSI, RTSP, or V4L2 camera input.

The original NanoOWL tree demo opens only a numeric V4L2 camera index.
This companion keeps its prompt protocol and browser page, but lets OpenCV
open an NVIDIA Argus or RTSP GStreamer workflow as well.
"""

import argparse
import asyncio
import contextlib
import logging
import os
import time
import weakref

import cv2
import PIL.Image
from aiohttp import WSCloseCode, web
from nanoowl.owl_predictor import OwlPredictor
from nanoowl.tree import Tree
from nanoowl.tree_drawing import draw_tree_output
from nanoowl.tree_predictor import TreePredictor


def parse_resolution(value: str) -> tuple[int, int]:
    """Convert a command-line value such as 640x480 to two integers."""
    try:
        width_text, height_text = value.lower().split("x", maxsplit=1)
        width, height = int(width_text), int(height_text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "resolution must be WIDTHxHEIGHT, for example 640x480"
        ) from error

    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("resolution values must be positive")

    return width, height


def csi_workflow(
    sensor_id: int, width: int, height: int, framerate: int
) -> str:
    """Build an Argus workflow for an NVIDIA CSI camera such as IMX219."""
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
    """Build a low-latency H.264 RTSP workflow without printing its URL."""
    return (
        f"rtspsrc location={url} protocols=tcp latency={latency} ! "
        "rtph264depay ! h264parse ! nvv4l2decoder ! "
        f"nvvidconv ! video/x-raw,format=(string)BGRx,width=(int){width},"
        f"height=(int){height} ! videoconvert ! video/x-raw,format=(string)BGR ! "
        "appsink drop=true max-buffers=1 sync=false"
    )


def open_camera(args: argparse.Namespace, width: int, height: int) -> cv2.VideoCapture:
    """Open the selected source and fail with a useful, non-secret error."""
    if args.source == "v4l2":
        camera = cv2.VideoCapture(args.camera)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        source_description = f"V4L2 camera index {args.camera}"
    elif args.source == "csi":
        camera = cv2.VideoCapture(
            csi_workflow(args.sensor_id, width, height, args.framerate),
            cv2.CAP_GSTREAMER,
        )
        source_description = f"CSI camera sensor-id {args.sensor_id}"
    else:
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

    logging.info("Opened %s.", source_description)
    return camera


def bgr_to_pil(image):
    """NanoOWL expects a Pillow image in RGB order; OpenCV uses BGR."""
    return PIL.Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NanoOWL browser demo with CSI, RTSP, or V4L2 input."
    )
    parser.add_argument("image_encode_engine", help="Path to the TensorRT engine")
    parser.add_argument(
        "--source", choices=("csi", "rtsp", "v4l2"), default="v4l2"
    )
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--sensor-id", type=int, default=0)
    parser.add_argument("--resolution", type=parse_resolution, default=(640, 480))
    parser.add_argument("--framerate", type=int, default=30)
    parser.add_argument("--latency", type=int, default=200)
    parser.add_argument("--rtsp-env", default="RTSP_URL")
    parser.add_argument("--image-quality", type=int, default=50)
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    if args.framerate <= 0:
        parser.error("--framerate must be positive")
    if args.latency < 0:
        parser.error("--latency cannot be negative")
    if not 0 <= args.image_quality <= 100:
        parser.error("--image-quality must be between 0 and 100")

    width, height = args.resolution
    predictor = TreePredictor(
        owl_predictor=OwlPredictor(image_encoder_engine=args.image_encode_engine)
    )
    state = {"prompt": None}

    async def handle_index_get(request: web.Request) -> web.FileResponse:
        # The official NanoOWL tree-demo page is in the current work directory.
        return web.FileResponse("./index.html")

    async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
        websocket = web.WebSocketResponse()
        await websocket.prepare(request)
        request.app["websockets"].add(websocket)

        try:
            async for message in websocket:
                if not isinstance(message.data, str) or not message.data.startswith(
                    "prompt:"
                ):
                    continue

                prompt = message.data.removeprefix("prompt:")
                try:
                    tree = Tree.from_prompt(prompt)
                    state["prompt"] = {
                        "tree": tree,
                        "clip": predictor.encode_clip_text(tree),
                        "owl": predictor.encode_owl_text(tree),
                    }
                    logging.info("Set a new object prompt.")
                except Exception as error:  # Keep the browser demo usable after bad input.
                    logging.warning("Could not use the received prompt: %s", error)
        finally:
            request.app["websockets"].discard(websocket)

        return websocket

    async def on_shutdown(app: web.Application) -> None:
        for websocket in set(app["websockets"]):
            await websocket.close(
                code=WSCloseCode.GOING_AWAY, message=b"Server shutdown"
            )

    async def detection_loop(app: web.Application) -> None:
        camera = open_camera(args, width, height)
        event_loop = asyncio.get_running_loop()

        def read_and_encode_frame():
            ok, image = camera.read()
            if not ok:
                return False, None

            prompt = state["prompt"]
            if prompt is not None:
                start = time.perf_counter()
                detections = predictor.predict(
                    bgr_to_pil(image),
                    tree=prompt["tree"],
                    clip_text_encodings=prompt["clip"],
                    owl_text_encodings=prompt["owl"],
                )
                image = draw_tree_output(image, detections, prompt["tree"])
                logging.debug("Inference took %.3f seconds.", time.perf_counter() - start)

            encoded, jpeg = cv2.imencode(
                ".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, args.image_quality]
            )
            return encoded, bytes(jpeg) if encoded else None

        try:
            while True:
                ok, jpeg = await event_loop.run_in_executor(None, read_and_encode_frame)
                if not ok:
                    logging.error("Camera frame read failed; stopping the demo.")
                    break

                for websocket in set(app["websockets"]):
                    await websocket.send_bytes(jpeg)
        finally:
            camera.release()

    async def detection_context(app: web.Application):
        task = asyncio.create_task(detection_loop(app))
        yield
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    logging.basicConfig(level=logging.INFO)
    app = web.Application()
    app["websockets"] = weakref.WeakSet()
    app.router.add_get("/", handle_index_get)
    app.router.add_get("/ws", websocket_handler)
    app.on_shutdown.append(on_shutdown)
    app.cleanup_ctx.append(detection_context)
    web.run_app(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
