"""Lossless VRS to video converter that preserves exact pixel values."""

from pathlib import Path

import cv2
from projectaria_tools.core import data_provider
from projectaria_tools.core.sensor_data import SensorDataType
from projectaria_tools.core.stream_id import StreamId
from tqdm import tqdm


def convert_vrs_to_video_lossless(
    vrs_path: str,
    output_path: str,
    stream_id: str = "211-1",
    codec: str = "FFV1",
    container: str = "avi",
) -> None:
    """Convert VRS stream to lossless video that preserves exact pixel values.

    Args:
        vrs_path: Path to VRS file
        output_path: Path to output video file
        stream_id: Stream ID to extract (default: "211-1" for eye camera)
        codec: Codec fourcc code (default: "FFV1" - lossless)
        container: Video container format (default: "avi")

    """
    # Ensure output has correct extension
    output_path = Path(output_path)
    if output_path.suffix != f".{container}":
        output_path = output_path.with_suffix(f".{container}")

    # Load VRS provider
    provider = data_provider.create_vrs_data_provider(vrs_path)
    if not provider:
        raise ValueError(f"Cannot open VRS file: {vrs_path}")

    stream = StreamId(stream_id)
    if not provider.check_stream_is_active(stream):
        raise ValueError(f"Stream {stream_id} not found in VRS file")

    # Get stream configuration
    image_config = provider.get_image_configuration(stream)
    width = image_config.image_width
    height = image_config.image_height
    fps = image_config.nominal_rate_hz
    frame_count = provider.get_num_data(stream)

    # Setup video writer with lossless codec
    fourcc = cv2.VideoWriter_fourcc(*codec)
    writer = cv2.VideoWriter(
        str(output_path),
        fourcc,
        fps,
        (width, height),
        isColor=False,  # Grayscale
    )

    if not writer.isOpened():
        raise RuntimeError(f"Failed to open video writer for {output_path}")

    # Configure stream delivery
    deliver_option = provider.get_default_deliver_queued_options()
    deliver_option.deactivate_stream_all()
    deliver_option.activate_stream(stream)

    # Extract frames
    frames_written = 0
    with tqdm(total=frame_count, desc="Extracting frames") as pbar:
        for data in provider.deliver_queued_sensor_data(deliver_option):
            if data.sensor_data_type() == SensorDataType.IMAGE and data.stream_id() == stream:
                # Get raw frame without any processing
                frame = data.image_data_and_record()[0].to_numpy_array()

                # Write frame directly (no rotation, no conversion)
                writer.write(frame)
                frames_written += 1
                pbar.update(1)

    writer.release()
    print(f"Extracted {frames_written} frames to {output_path}")
