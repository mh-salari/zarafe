"""Export Meta Aria Gen1 VRS file to MP4 videos, gaze data, and sensor data.

This script exports data from Meta Aria VRS recordings including:
- RGB camera video (world/scene view)
- Eye tracking camera video
- IMU sensor data
- Gaze data with camera calibration
- Recording metadata
"""

import argparse
import datetime
import itertools
import json
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import pycolmap
from projectaria_tools.core import calibration, data_provider, mps, sophus
from projectaria_tools.core.mps import MpsDataPathsProvider
from projectaria_tools.core.sensor_data import TimeDomain
from projectaria_tools.core.stream_id import StreamId
from projectaria_tools.tools.vrs_to_mp4.vrs_to_mp4_utils import convert_vrs_to_mp4

from .vrs_to_video_lossless import convert_vrs_to_video_lossless

# Stream IDs for Aria cameras
RGB_CAMERA_STREAM_ID = "214-1"
EYE_TRACKING_CAMERA_STREAM_ID = "211-1"
IMU_RIGHT_STREAM_ID = "1202-1"
IMU_LEFT_STREAM_ID = "1202-2"


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Export Meta Aria Gen1 VRS file to MP4 videos and gaze data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("vrs_file_path", type=str, help="Path to the VRS file to process")
    parser.add_argument(
        "--mps-folder-path",
        type=str,
        default=None,
        help="Path to MPS folder (auto-detected if not provided)",
    )
    parser.add_argument(
        "--output-folder-path",
        type=str,
        default=None,
        help="Path to output folder (defaults to export_<vrs_filename>)",
    )
    parser.add_argument("--skip-rgb-camera", action="store_true", help="Skip extracting RGB camera video")
    parser.add_argument("--skip-eye-camera", action="store_true", help="Skip extracting eye tracking camera video")
    parser.add_argument("--skip-gaze-data", action="store_true", help="Skip extracting gaze data and calibration")
    parser.add_argument("--skip-imu-data", action="store_true", help="Skip extracting IMU sensor data")
    parser.add_argument(
        "--export-raw-gaze", action="store_true", help="Export raw gaze data (yaw, pitch, depth, confidence intervals)"
    )
    parser.add_argument("--list-streams-only", action="store_true", help="Only list available streams and exit")
    return parser.parse_args()


def display_stream_information(vrs_data_provider: object) -> None:
    """Display information about all available streams in the VRS file."""
    print("\n" + "=" * 80)
    print("VRS FILE STREAM INFORMATION")
    print("=" * 80)

    all_streams = vrs_data_provider.get_all_streams()
    for stream_id in all_streams:
        stream_label = vrs_data_provider.get_label_from_stream_id(stream_id)
        print(f"\nStream ID: {stream_id} | Label: {stream_label.upper()}")

        if "camera" in stream_label:
            camera_config = vrs_data_provider.get_image_configuration(stream_id)
            start_time_ns = vrs_data_provider.get_first_time_ns(stream_id, TimeDomain.DEVICE_TIME)
            end_time_ns = vrs_data_provider.get_last_time_ns(stream_id, TimeDomain.DEVICE_TIME)
            duration_seconds = (end_time_ns - start_time_ns) / 1e9
            expected_frame_count = int(duration_seconds * camera_config.nominal_rate_hz)

            print("  Type: Video Stream")
            print(f"  Resolution: {camera_config.image_width} x {camera_config.image_height} pixels")
            print(f"  Frame Rate: {camera_config.nominal_rate_hz} fps")
            print(f"  Duration: {duration_seconds:.2f} seconds ({expected_frame_count} frames)")
            print(f"  Sensor Serial: {camera_config.sensor_serial}")

            if stream_label == "camera-et":
                print("  Purpose: Eye tracking camera for gaze estimation")
            elif stream_label == "camera-rgb":
                print("  Purpose: Scene/world camera capturing user's view")

        elif "imu" in stream_label:
            imu_config = vrs_data_provider.get_imu_configuration(stream_id)
            start_time_ns = vrs_data_provider.get_first_time_ns(stream_id, TimeDomain.DEVICE_TIME)
            end_time_ns = vrs_data_provider.get_last_time_ns(stream_id, TimeDomain.DEVICE_TIME)
            duration_seconds = (end_time_ns - start_time_ns) / 1e9

            print("  Type: IMU (Inertial Measurement Unit)")
            print(f"  Sample Rate: {imu_config.nominal_rate_hz} Hz")
            print(f"  Duration: {duration_seconds:.2f} seconds")
            print("  Purpose: Head movement and orientation tracking")

    print("\n" + "=" * 80 + "\n")


def check_required_streams(
    vrs_data_provider: object, skip_rgb: bool, skip_eye: bool
) -> tuple[bool, bool, object, object]:
    """Check if required camera streams are present in the VRS file."""
    rgb_stream_id = StreamId(RGB_CAMERA_STREAM_ID)
    eye_tracking_stream_id = StreamId(EYE_TRACKING_CAMERA_STREAM_ID)

    has_rgb_camera = False
    has_eye_tracking_camera = False

    all_streams = vrs_data_provider.get_all_streams()
    for stream_id in all_streams:
        if stream_id == rgb_stream_id:
            has_rgb_camera = True
        elif stream_id == eye_tracking_stream_id:
            has_eye_tracking_camera = True

    if not has_rgb_camera and not skip_rgb:
        raise RuntimeError("RGB camera stream not found in recording")
    if not has_eye_tracking_camera and not skip_eye:
        raise RuntimeError("Eye tracking camera stream not found in recording")

    return has_rgb_camera, has_eye_tracking_camera, rgb_stream_id, eye_tracking_stream_id


def print_camera_timing_info(
    vrs_data_provider: object, rgb_stream_id: object, eye_tracking_stream_id: object
) -> tuple[int, int, int, int]:
    """Print timing information for RGB and eye tracking cameras."""
    rgb_start_time_ns = vrs_data_provider.get_first_time_ns(rgb_stream_id, TimeDomain.DEVICE_TIME)
    rgb_end_time_ns = vrs_data_provider.get_last_time_ns(rgb_stream_id, TimeDomain.DEVICE_TIME)
    rgb_duration_seconds = (rgb_end_time_ns - rgb_start_time_ns) / 1e9

    eye_tracking_start_time_ns = vrs_data_provider.get_first_time_ns(eye_tracking_stream_id, TimeDomain.DEVICE_TIME)
    eye_tracking_end_time_ns = vrs_data_provider.get_last_time_ns(eye_tracking_stream_id, TimeDomain.DEVICE_TIME)
    eye_tracking_duration_seconds = (eye_tracking_end_time_ns - eye_tracking_start_time_ns) / 1e9

    onset_offset_ms = (rgb_start_time_ns - eye_tracking_start_time_ns) / 1e6
    offset_offset_ms = (rgb_end_time_ns - eye_tracking_end_time_ns) / 1e6

    print(f"RGB camera: {rgb_duration_seconds:.3f}s ({rgb_start_time_ns}--{rgb_end_time_ns} ns)")
    print(
        f"Eye tracking camera: {eye_tracking_duration_seconds:.3f}s ({eye_tracking_start_time_ns}--{eye_tracking_end_time_ns} ns)"
    )
    print(f"Timing offset (onset, offset): {onset_offset_ms:.3f}ms, {offset_offset_ms:.3f}ms")

    return rgb_start_time_ns, rgb_end_time_ns, eye_tracking_start_time_ns, eye_tracking_end_time_ns


def export_camera_video(
    vrs_file_path: Path,
    output_folder_path: Path,
    stream_id: object,
    output_filename: str,
    use_lossless: bool = False,
    vrs_data_provider: object = None,
) -> None:
    """Export camera stream to video file.

    Args:
        vrs_file_path: Path to the VRS file
        output_folder_path: Directory to save the output video
        stream_id: Stream ID to export
        output_filename: Name of the output video file
        use_lossless: Whether to use lossless encoding (for eye camera)
        vrs_data_provider: Optional VRS data provider (to check audio config)

    """
    output_video_path = output_folder_path / output_filename

    if use_lossless:
        # Use lossless extractor for eye camera (preserves exact pixel values)
        convert_vrs_to_video_lossless(str(vrs_file_path), str(output_video_path), stream_id=str(stream_id))
    else:
        # Determine correct audio channels to use
        audio_channels = None  # Default: try to extract audio with auto-detection

        if vrs_data_provider is not None:
            # Check if mic stream exists and get its configuration
            try:
                mic_stream_id = StreamId("231-1")  # Standard mic stream ID for Aria
                audio_config = vrs_data_provider.get_audio_configuration(mic_stream_id)
                # Use all available channels explicitly
                audio_channels = list(range(audio_config.num_channels))
                print(f"  Audio: detected {audio_config.num_channels} channels")
            except Exception:
                # No audio stream or failed to get config - skip audio
                audio_channels = []
                print("  Note: No audio stream detected, extracting video without audio")

        convert_vrs_to_mp4(
            str(vrs_file_path), str(output_video_path), stream_id=str(stream_id), audio_channels=audio_channels
        )

    print(f"  Saved to: {output_video_path}")


def export_imu_data(vrs_data_provider: object, output_folder_path: Path) -> None:
    """Export IMU sensor data to CSV files."""
    print("\nExtracting IMU sensor data...")

    imu_right_stream_id = StreamId(IMU_RIGHT_STREAM_ID)
    imu_left_stream_id = StreamId(IMU_LEFT_STREAM_ID)

    # Check if IMU streams exist
    all_streams = vrs_data_provider.get_all_streams()
    has_imu_right = imu_right_stream_id in all_streams
    has_imu_left = imu_left_stream_id in all_streams

    if has_imu_right:
        imu_right_data_list = []
        imu_right_iterator = vrs_data_provider.deliver_queued_sensor_data()
        for sensor_data in imu_right_iterator:
            if sensor_data.stream_id() == imu_right_stream_id:
                imu_data = sensor_data.imu_data()
                timestamp_ns = sensor_data.get_time_ns(TimeDomain.DEVICE_TIME)
                imu_right_data_list.append({
                    "timestamp_ns": timestamp_ns,
                    "accel_x": imu_data.accel_msec2[0],
                    "accel_y": imu_data.accel_msec2[1],
                    "accel_z": imu_data.accel_msec2[2],
                    "gyro_x": imu_data.gyro_radsec[0],
                    "gyro_y": imu_data.gyro_radsec[1],
                    "gyro_z": imu_data.gyro_radsec[2],
                })

        if imu_right_data_list:
            imu_right_df = pd.DataFrame(imu_right_data_list)
            imu_right_output_path = output_folder_path / "imu_right.csv"
            imu_right_df.to_csv(imu_right_output_path, index=False, float_format="%.8f")
            print(f"  IMU Right saved to: {imu_right_output_path}")

    if has_imu_left:
        imu_left_data_list = []
        imu_left_iterator = vrs_data_provider.deliver_queued_sensor_data()
        for sensor_data in imu_left_iterator:
            if sensor_data.stream_id() == imu_left_stream_id:
                imu_data = sensor_data.imu_data()
                timestamp_ns = sensor_data.get_time_ns(TimeDomain.DEVICE_TIME)
                imu_left_data_list.append({
                    "timestamp_ns": timestamp_ns,
                    "accel_x": imu_data.accel_msec2[0],
                    "accel_y": imu_data.accel_msec2[1],
                    "accel_z": imu_data.accel_msec2[2],
                    "gyro_x": imu_data.gyro_radsec[0],
                    "gyro_y": imu_data.gyro_radsec[1],
                    "gyro_z": imu_data.gyro_radsec[2],
                })

        if imu_left_data_list:
            imu_left_df = pd.DataFrame(imu_left_data_list)
            imu_left_output_path = output_folder_path / "imu_left.csv"
            imu_left_df.to_csv(imu_left_output_path, index=False, float_format="%.8f")
            print(f"  IMU Left saved to: {imu_left_output_path}")


def export_raw_gaze_data(
    mps_folder_path: Path,
    output_folder_path: Path,
) -> None:
    """Export raw gaze data with yaw, pitch, depth, and confidence intervals."""
    print("\nExtracting raw gaze data...")

    # Load MPS gaze data
    mps_data_paths_provider = MpsDataPathsProvider(str(mps_folder_path))
    general_eyegaze_path = mps_data_paths_provider.get_data_paths().eyegaze.general_eyegaze
    general_gaze_data = []

    personalized_eyegaze_path = mps_data_paths_provider.get_data_paths().eyegaze.personalized_eyegaze
    if not personalized_eyegaze_path:
        eyegaze_path = general_eyegaze_path
    else:
        general_gaze_data = mps.read_eyegaze(general_eyegaze_path)
        eyegaze_path = personalized_eyegaze_path

    gaze_data = mps.read_eyegaze(eyegaze_path)

    # Extract raw gaze data
    raw_gaze_samples = []
    for gaze_sample, general_gaze_sample in itertools.zip_longest(gaze_data, general_gaze_data):
        # Use general gaze if personalized gaze is NaN
        current_gaze_sample = gaze_sample
        if np.isnan(gaze_sample.yaw) and general_gaze_sample is not None:
            current_gaze_sample = general_gaze_sample

        # Get timestamp in microseconds
        timestamp_microseconds = current_gaze_sample.tracking_timestamp / datetime.timedelta(microseconds=1)

        raw_gaze_samples.append({
            "tracking_timestamp_us": timestamp_microseconds,
            "yaw_rads_cpf": current_gaze_sample.yaw,
            "pitch_rads_cpf": current_gaze_sample.pitch,
            "depth_m": current_gaze_sample.depth if current_gaze_sample.depth is not None else np.nan,
            "yaw_low_rads_cpf": current_gaze_sample.yaw_low,
            "pitch_low_rads_cpf": current_gaze_sample.pitch_low,
            "yaw_high_rads_cpf": current_gaze_sample.yaw_high,
            "pitch_high_rads_cpf": current_gaze_sample.pitch_high,
        })

    # Save raw gaze data to CSV
    raw_gaze_df = pd.DataFrame(raw_gaze_samples)
    raw_gaze_output_path = output_folder_path / "raw_gaze.csv"
    raw_gaze_df.to_csv(raw_gaze_output_path, index=False, float_format="%.8f", na_rep="")

    print(f"  Raw gaze data saved to: {raw_gaze_output_path}")


def export_local_gaze_data(
    vrs_data_provider: object,
    rgb_stream_id: object,
    local_gaze_csv_path: Path,
    output_folder_path: Path,
    rgb_start_time_ns: int,
    apply_upright_rotation: bool = True,
) -> None:
    """Export gaze data from local CSV file."""
    print("\nProcessing local gaze data...")

    # Read local gaze CSV
    local_gaze_df = pd.read_csv(local_gaze_csv_path)

    # Get device calibration
    device_calibration = vrs_data_provider.get_device_calibration()
    rgb_camera_calibration = device_calibration.get_camera_calib(
        vrs_data_provider.get_label_from_stream_id(rgb_stream_id)
    )

    # Get coordinate transformations
    transform_device_to_cpf = device_calibration.get_transform_device_cpf()
    transform_device_to_rgb_camera = device_calibration.get_transform_device_sensor(
        vrs_data_provider.get_label_from_stream_id(rgb_stream_id), True
    )

    # Apply upright rotation if needed
    if apply_upright_rotation:
        rotation_matrix = np.array([[0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        transform_device_to_rgb_camera @= sophus.SE3.from_matrix(rotation_matrix)

    transform_rgb_camera_to_cpf = transform_device_to_rgb_camera.inverse() @ transform_device_to_cpf

    # Validate camera calibration model
    if rgb_camera_calibration.get_model_name() != calibration.CameraModelType.FISHEYE624:
        raise ValueError(
            f"RGB camera must use Fisheye624 calibration model, got {rgb_camera_calibration.get_model_name()}"
        )

    # Rotate camera calibration if upright
    if apply_upright_rotation:
        rgb_camera_calibration = calibration.rotate_camera_calib_cw90deg(rgb_camera_calibration)

    # Create colmap camera calibration
    colmap_camera = pycolmap.Camera.create(
        0,
        pycolmap.CameraModelId.RAD_TAN_THIN_PRISM_FISHEYE,
        rgb_camera_calibration.get_focal_lengths()[0],
        *rgb_camera_calibration.get_image_size(),
    )

    calibration_parameters = np.zeros((colmap_camera.extra_params_idxs()[-1] + 1,))
    calibration_parameters[colmap_camera.focal_length_idxs()] = rgb_camera_calibration.get_focal_lengths()
    calibration_parameters[colmap_camera.principal_point_idxs()] = rgb_camera_calibration.get_principal_point()
    calibration_parameters[colmap_camera.extra_params_idxs()] = rgb_camera_calibration.get_projection_params()[
        -len(colmap_camera.extra_params_idxs()) :
    ]
    colmap_camera.params = calibration_parameters

    # Process gaze data from CSV
    gaze_samples = []
    for _, row in local_gaze_df.iterrows():
        # Skip rows with NaN yaw or pitch
        if pd.isna(row["yaw_rads_cpf"]) or pd.isna(row["pitch_rads_cpf"]):
            continue

        yaw = row["yaw_rads_cpf"]
        pitch = row["pitch_rads_cpf"]
        depth_meters = row["depth_m"] if not pd.isna(row["depth_m"]) else 1.0

        # Calculate 3D binocular gaze point
        binocular_gaze_point_cpf = mps.get_eyegaze_point_at_depth(yaw, pitch, depth_meters)

        # Project gaze point onto camera image
        binocular_gaze_point_rgb_camera = transform_rgb_camera_to_cpf @ binocular_gaze_point_cpf
        gaze_position_on_image = colmap_camera.img_from_cam(np.reshape(binocular_gaze_point_rgb_camera, (1, 3)))

        # Calculate timestamp in relative video time (microseconds)
        timestamp_microseconds = row["tracking_timestamp_us"] - int(rgb_start_time_ns / 1000)

        # Store sample (convert gaze point from m to mm)
        # Note: We don't have full gaze vectors/origins from local CSV, so we fill with NaN
        gaze_samples.append(
            np.concatenate((
                [timestamp_microseconds],
                gaze_position_on_image.flatten(),
                binocular_gaze_point_cpf * 1000.0,
                [np.nan] * 12,  # Placeholder for gaze vectors and origins
            ))
        )

    # Save gaze data to TSV
    gaze_dataframe = pd.DataFrame(
        gaze_samples,
        columns=[
            "timestamp",
            "gaze_pos_vid_x",
            "gaze_pos_vid_y",
            "gaze_pos_3d_x",
            "gaze_pos_3d_y",
            "gaze_pos_3d_z",
            "gaze_dir_left_x",
            "gaze_dir_left_y",
            "gaze_dir_left_z",
            "gaze_dir_right_x",
            "gaze_dir_right_y",
            "gaze_dir_right_z",
            "gaze_ori_left_x",
            "gaze_ori_left_y",
            "gaze_ori_left_z",
            "gaze_ori_right_x",
            "gaze_ori_right_y",
            "gaze_ori_right_z",
        ],
    )

    gaze_output_path = output_folder_path / "gaze_local.tsv"
    gaze_dataframe.to_csv(gaze_output_path, sep="\t", float_format="%.8f", index=False, na_rep="nan")

    print(f"  Local gaze data saved to: {gaze_output_path}")


def export_gaze_data_and_calibration(
    vrs_data_provider: object,
    rgb_stream_id: object,
    mps_folder_path: Path,
    output_folder_path: Path,
    rgb_start_time_ns: int,
    apply_upright_rotation: bool = True,
) -> None:
    """Export gaze data and camera calibration."""
    print("\nProcessing gaze data and camera calibration...")

    # Load MPS gaze data
    mps_data_paths_provider = MpsDataPathsProvider(str(mps_folder_path))
    general_eyegaze_path = mps_data_paths_provider.get_data_paths().eyegaze.general_eyegaze
    general_gaze_data = []

    personalized_eyegaze_path = mps_data_paths_provider.get_data_paths().eyegaze.personalized_eyegaze
    if not personalized_eyegaze_path:
        eyegaze_path = general_eyegaze_path
    else:
        general_gaze_data = mps.read_eyegaze(general_eyegaze_path)
        eyegaze_path = personalized_eyegaze_path

    gaze_data = mps.read_eyegaze(eyegaze_path)

    # Get device calibration
    device_calibration = vrs_data_provider.get_device_calibration()
    rgb_camera_calibration = device_calibration.get_camera_calib(
        vrs_data_provider.get_label_from_stream_id(rgb_stream_id)
    )

    # Get coordinate transformations
    transform_device_to_cpf = device_calibration.get_transform_device_cpf()
    transform_device_to_rgb_camera = device_calibration.get_transform_device_sensor(
        vrs_data_provider.get_label_from_stream_id(rgb_stream_id), True
    )

    # Apply upright rotation if needed (convert_vrs_to_mp4 rotates video upright)
    if apply_upright_rotation:
        rotation_matrix = np.array([[0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        transform_device_to_rgb_camera @= sophus.SE3.from_matrix(rotation_matrix)

    transform_rgb_camera_to_cpf = transform_device_to_rgb_camera.inverse() @ transform_device_to_cpf

    # Validate camera calibration model
    if rgb_camera_calibration.get_model_name() != calibration.CameraModelType.FISHEYE624:
        raise ValueError(
            f"RGB camera must use Fisheye624 calibration model, got {rgb_camera_calibration.get_model_name()}"
        )

    # Rotate camera calibration if upright
    if apply_upright_rotation:
        rgb_camera_calibration = calibration.rotate_camera_calib_cw90deg(rgb_camera_calibration)

    # Create colmap camera calibration
    colmap_camera = pycolmap.Camera.create(
        0,
        pycolmap.CameraModelId.RAD_TAN_THIN_PRISM_FISHEYE,
        rgb_camera_calibration.get_focal_lengths()[0],
        *rgb_camera_calibration.get_image_size(),
    )

    calibration_parameters = np.zeros((colmap_camera.extra_params_idxs()[-1] + 1,))
    calibration_parameters[colmap_camera.focal_length_idxs()] = rgb_camera_calibration.get_focal_lengths()
    calibration_parameters[colmap_camera.principal_point_idxs()] = rgb_camera_calibration.get_principal_point()
    calibration_parameters[colmap_camera.extra_params_idxs()] = rgb_camera_calibration.get_projection_params()[
        -len(colmap_camera.extra_params_idxs()) :
    ]
    colmap_camera.params = calibration_parameters

    # Save camera calibration to XML
    camera_calibration_info = {
        "resolution": rgb_camera_calibration.get_image_size(),
        "position": transform_rgb_camera_to_cpf.to_quat_and_translation()[0][4:] * 1000.0,  # m to mm
        "rotation": transform_rgb_camera_to_cpf.to_matrix()[:3, :3],
        "colmap_camera": colmap_camera.todict(),
    }

    # Fix values that cv2.FileStorage cannot handle
    camera_calibration_info["colmap_camera"]["model"] = camera_calibration_info["colmap_camera"]["model"].name
    camera_calibration_info["colmap_camera"]["has_prior_focal_length"] = int(
        camera_calibration_info["colmap_camera"]["has_prior_focal_length"]
    )

    calibration_output_path = output_folder_path / "calibration.xml"
    file_storage = cv2.FileStorage(str(calibration_output_path), cv2.FILE_STORAGE_WRITE)
    for key, value in camera_calibration_info.items():
        if isinstance(value, dict):
            file_storage.startWriteStruct("colmap_camera", cv2.FileNode_MAP)
            for dict_key, dict_value in value.items():
                file_storage.write(name=dict_key, val=dict_value)
            file_storage.endWriteStruct()
        else:
            file_storage.write(name=key, val=value)
    file_storage.release()

    # Process gaze data
    gaze_samples = []
    for gaze_sample, general_gaze_sample in itertools.zip_longest(gaze_data, general_gaze_data):
        # Use general gaze if personalized gaze is NaN
        current_gaze_sample = gaze_sample
        if np.isnan(gaze_sample.yaw) and general_gaze_sample is not None:
            current_gaze_sample = general_gaze_sample

        # Calculate 3D binocular gaze point
        depth_meters = current_gaze_sample.depth or 1.0
        binocular_gaze_point_cpf = mps.get_eyegaze_point_at_depth(
            current_gaze_sample.yaw, current_gaze_sample.pitch, depth_meters
        )

        # Project gaze point onto camera image
        binocular_gaze_point_rgb_camera = transform_rgb_camera_to_cpf @ binocular_gaze_point_cpf
        gaze_position_on_image = colmap_camera.img_from_cam(np.reshape(binocular_gaze_point_rgb_camera, (1, 3)))

        # Get gaze vectors
        gaze_vectors = mps.get_gaze_vectors(
            current_gaze_sample.vergence.left_yaw, current_gaze_sample.vergence.right_yaw, current_gaze_sample.pitch
        )

        # Get gaze origins (m to mm)
        gaze_origins_mm = (
            np.array([
                current_gaze_sample.vergence.tx_left_eye,
                current_gaze_sample.vergence.ty_left_eye,
                current_gaze_sample.vergence.tz_left_eye,
                current_gaze_sample.vergence.tx_right_eye,
                current_gaze_sample.vergence.ty_right_eye,
                current_gaze_sample.vergence.tz_right_eye,
            ])
            * 1000.0
        )

        # Calculate timestamp in relative video time (microseconds)
        timestamp_microseconds = current_gaze_sample.tracking_timestamp / datetime.timedelta(microseconds=1) - int(
            rgb_start_time_ns / 1000
        )

        # Store sample (convert gaze point from m to mm)
        gaze_samples.append(
            np.concatenate((
                [timestamp_microseconds],
                gaze_position_on_image.flatten(),
                binocular_gaze_point_cpf * 1000.0,
                *gaze_vectors,
                gaze_origins_mm,
            ))
        )

    # Save gaze data to TSV
    gaze_dataframe = pd.DataFrame(
        gaze_samples,
        columns=[
            "timestamp",
            "gaze_pos_vid_x",
            "gaze_pos_vid_y",
            "gaze_pos_3d_x",
            "gaze_pos_3d_y",
            "gaze_pos_3d_z",
            "gaze_dir_left_x",
            "gaze_dir_left_y",
            "gaze_dir_left_z",
            "gaze_dir_right_x",
            "gaze_dir_right_y",
            "gaze_dir_right_z",
            "gaze_ori_left_x",
            "gaze_ori_left_y",
            "gaze_ori_left_z",
            "gaze_ori_right_x",
            "gaze_ori_right_y",
            "gaze_ori_right_z",
        ],
    )

    gaze_output_path = output_folder_path / "gaze.tsv"
    gaze_dataframe.to_csv(gaze_output_path, sep="\t", float_format="%.8f", index=False, na_rep="nan")

    print(f"  Gaze data saved to: {gaze_output_path}")
    print(f"  Calibration saved to: {calibration_output_path}")


def export_metadata(
    vrs_data_provider: object,
    vrs_file_path: Path,
    output_folder_path: Path,
    rgb_camera_config: object,
    eye_tracking_camera_config: object,
    rgb_start_time_ns: int,
    rgb_end_time_ns: int,
    eye_tracking_start_time_ns: int,
    eye_tracking_end_time_ns: int,
) -> None:
    """Export recording metadata to JSON file."""
    print("\nExporting metadata...")

    recording_metadata = vrs_data_provider.get_metadata()

    metadata_dict = {
        "start_time": recording_metadata.start_time_epoch_sec,
        "glasses_serial": recording_metadata.device_serial,
        "duration": int(
            (max(eye_tracking_start_time_ns, eye_tracking_end_time_ns) - min(rgb_start_time_ns, rgb_end_time_ns))
            / 1000.0
        ),
        "name": vrs_file_path.stem,
        "rgb_camera": {
            "sensor_serial": rgb_camera_config.sensor_serial,
            "resolution": [rgb_camera_config.image_width, rgb_camera_config.image_height],
            "frame_rate_hz": rgb_camera_config.nominal_rate_hz,
            "pixel_format": int(rgb_camera_config.pixel_format),
        },
        "eye_tracking_camera": {
            "sensor_serial": eye_tracking_camera_config.sensor_serial,
            "resolution": [eye_tracking_camera_config.image_width, eye_tracking_camera_config.image_height],
            "frame_rate_hz": eye_tracking_camera_config.nominal_rate_hz,
            "pixel_format": int(eye_tracking_camera_config.pixel_format),
        },
    }

    # Load additional metadata from JSON file if present
    vrs_json_file_path = vrs_file_path.with_suffix(".vrs.json")
    if vrs_json_file_path.is_file():
        with vrs_json_file_path.open(encoding="utf-8") as json_file:
            additional_metadata = json.load(json_file)

        if "firmware_version" in additional_metadata:
            metadata_dict["firmware_version"] = additional_metadata["firmware_version"]
        if additional_metadata.get("companion_version"):
            metadata_dict["recording_software_version"] = additional_metadata["companion_version"]

    metadata_output_path = output_folder_path / "metadata.json"
    with metadata_output_path.open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata_dict, metadata_file, indent=2)

    print(f"  Metadata saved to: {metadata_output_path}")


def main() -> None:
    """Main execution function."""
    args = parse_arguments()

    # Setup paths
    vrs_file_path = Path(args.vrs_file_path)
    if not vrs_file_path.exists():
        raise FileNotFoundError(f"VRS file not found: {vrs_file_path}")

    # Create output folder
    if args.output_folder_path:
        output_folder_path = Path(args.output_folder_path)
    else:
        output_folder_path = vrs_file_path.parent / f"export_{vrs_file_path.stem}"
    output_folder_path.mkdir(exist_ok=True, parents=True)

    # Determine MPS folder path
    if args.mps_folder_path:
        mps_folder_path = Path(args.mps_folder_path)
    else:
        mps_folder_path = vrs_file_path.parent / f"mps_{vrs_file_path.stem}_vrs"

    # Create VRS data provider
    print(f"Loading VRS file: {vrs_file_path}")
    vrs_data_provider = data_provider.create_vrs_data_provider(str(vrs_file_path))
    if not vrs_data_provider:
        raise RuntimeError("Failed to create VRS data provider")

    # Display stream information
    display_stream_information(vrs_data_provider)

    # Exit if list-only mode
    if args.list_streams_only:
        print("List-only mode enabled. Exiting without extraction.")
        return

    # Check for required streams
    has_rgb_camera, has_eye_tracking_camera, rgb_stream_id, eye_tracking_stream_id = check_required_streams(
        vrs_data_provider, args.skip_rgb_camera, args.skip_eye_camera
    )

    # Print camera timing information
    print("\nCamera Timing Information:")
    rgb_start_time_ns, rgb_end_time_ns, eye_tracking_start_time_ns, eye_tracking_end_time_ns = (
        print_camera_timing_info(vrs_data_provider, rgb_stream_id, eye_tracking_stream_id)
    )

    # Get camera configurations for later use
    rgb_camera_config = vrs_data_provider.get_image_configuration(rgb_stream_id)
    eye_tracking_camera_config = vrs_data_provider.get_image_configuration(eye_tracking_stream_id)

    # Export RGB camera video
    if not args.skip_rgb_camera and has_rgb_camera:
        print("\n" + "=" * 80)
        print("Extracting RGB camera video...")
        print("=" * 80)
        export_camera_video(
            vrs_file_path, output_folder_path, rgb_stream_id, "worldCamera.mp4", vrs_data_provider=vrs_data_provider
        )
    else:
        print("\nSkipping RGB camera extraction")

    # Export eye tracking camera video (lossless, preserves exact pixel values)
    if not args.skip_eye_camera and has_eye_tracking_camera:
        print("\n" + "=" * 80)
        print("Extracting eye tracking camera video (lossless)...")
        print("=" * 80)
        export_camera_video(
            vrs_file_path,
            output_folder_path,
            eye_tracking_stream_id,
            "eyeCamera.avi",
            use_lossless=True,
            vrs_data_provider=vrs_data_provider,
        )
    else:
        print("\nSkipping eye tracking camera extraction")

    # Export gaze data and calibration
    if not args.skip_gaze_data:
        print("\n" + "=" * 80)
        export_gaze_data_and_calibration(
            vrs_data_provider,
            rgb_stream_id,
            mps_folder_path,
            output_folder_path,
            rgb_start_time_ns,
            apply_upright_rotation=True,
        )
        print("=" * 80)
    else:
        print("\nSkipping gaze data extraction")

    # Export IMU data
    if not args.skip_imu_data:
        print("\n" + "=" * 80)
        export_imu_data(vrs_data_provider, output_folder_path)
        print("=" * 80)
    else:
        print("\nSkipping IMU data extraction")

    # Export raw gaze data
    if args.export_raw_gaze:
        print("\n" + "=" * 80)
        export_raw_gaze_data(mps_folder_path, output_folder_path)
        print("=" * 80)

    # Export metadata
    print("\n" + "=" * 80)
    export_metadata(
        vrs_data_provider,
        vrs_file_path,
        output_folder_path,
        rgb_camera_config,
        eye_tracking_camera_config,
        rgb_start_time_ns,
        rgb_end_time_ns,
        eye_tracking_start_time_ns,
        eye_tracking_end_time_ns,
    )
    print("=" * 80)

    print("\n\nExport completed successfully!")
    print(f"Output directory: {output_folder_path}")


if __name__ == "__main__":
    main()
