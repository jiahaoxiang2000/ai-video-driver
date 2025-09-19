"""
File management utilities for organizing output and temp files.
"""

import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def create_output_structure(base_name="dialogue"):
    """Create organized output folder structure"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/{base_name}_{timestamp}")
    temp_dir = output_dir / "temp"

    logger.info(f"Creating output structure: {output_dir}")

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Successfully created directories: {output_dir}, {temp_dir}")
    except Exception as e:
        logger.error(f"Failed to create output directories: {e}")
        raise

    return output_dir, temp_dir


def save_files(output_dir, audio_data, srt_content, sample_rate=24000):
    """Save audio and SRT files to output directory"""
    import torchaudio

    audio_file = output_dir / "audio.wav"
    srt_file = output_dir / "subtitles.srt"

    logger.info(f"Saving audio to: {audio_file}")
    try:
        torchaudio.save(str(audio_file), audio_data, sample_rate)
        logger.info(f"Successfully saved audio: {audio_file}")
    except Exception as e:
        logger.error(f"Failed to save audio: {e}")
        raise

    logger.info(f"Saving SRT to: {srt_file}")
    try:
        with open(srt_file, "w", encoding="utf-8") as f:
            f.write(srt_content)
        logger.info(f"Successfully saved SRT: {srt_file}")
    except Exception as e:
        logger.error(f"Failed to save SRT: {e}")
        raise

    return audio_file, srt_file


def cleanup_temp_files(temp_dir, keep_important=True):
    """Clean up temporary files, optionally keeping important ones"""
    import shutil

    if not temp_dir.exists():
        logger.warning(f"Temp directory does not exist: {temp_dir}")
        return

    logger.info(f"Cleaning up temp files in: {temp_dir}")

    try:
        if keep_important:
            # Keep certain files for debugging
            important_patterns = ["*.mp4", "filelist.txt"]
            for pattern in important_patterns:
                files = list(temp_dir.glob(f"**/{pattern}"))
                logger.debug(f"Keeping {len(files)} files matching {pattern}")
        else:
            # Remove everything
            shutil.rmtree(temp_dir)
            logger.info(f"Removed temp directory: {temp_dir}")

    except Exception as e:
        logger.error(f"Failed to cleanup temp files: {e}")


def get_file_info(file_path):
    """Get basic file information for logging"""
    try:
        path = Path(file_path)
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            return f"{path.name} ({size_mb:.2f} MB)"
        else:
            return f"{path.name} (not found)"
    except Exception as e:
        logger.error(f"Failed to get file info: {e}")
        return f"{file_path} (error)"