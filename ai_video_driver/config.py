"""
Configuration settings for the AI Video Driver pipeline.
"""

import logging
from pathlib import Path


class VideoConfig:
    """Configuration for video generation settings"""

    # Video quality settings
    QUALITY = "medium_quality"
    FORMAT = "mp4"
    RESOLUTION = "720p30"

    # Manim settings
    DISABLE_CACHING = True
    FRAME_RATE = 30

    # Text animation settings
    MAX_VISIBLE_TEXTS = 4
    WRITE_ANIMATION_SPEED = 0.3
    FADEOUT_DURATION = 0.3

    # Speaker colors
    SPEAKER_COLORS = {
        "S1": "#3498db",  # Blue
        "S2": "#2ecc71",  # Green
        "S3": "#f1c40f",  # Yellow
        "S4": "#9b59b6"   # Purple
    }

    # Font settings
    SPEAKER_FONT_SIZE = 24
    TEXT_FONT_SIZE = 20


class AudioConfig:
    """Configuration for audio processing"""

    SAMPLE_RATE = 24000
    AUDIO_FORMAT = "wav"

    # TTS settings
    DEFAULT_TEMPERATURE = 0.9
    DEFAULT_TOPK = 30


class FileConfig:
    """Configuration for file management"""

    # Directory structure
    OUTPUT_BASE = "output"
    TEMP_SUBDIR = "temp"
    LOGS_DIR = "logs"

    # File naming
    AUDIO_FILENAME = "audio.wav"
    SRT_FILENAME = "subtitles.srt"
    SILENT_VIDEO_FILENAME = "video_silent.mp4"
    FINAL_VIDEO_FILENAME = "final_video_with_audio.mp4"

    # Cleanup settings
    KEEP_TEMP_FILES = True


class LogConfig:
    """Configuration for logging"""

    LEVEL = logging.INFO
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    # Module-specific log levels
    MANIM_LOG_LEVEL = logging.WARNING
    FFMPEG_LOG_LEVEL = logging.WARNING

    # File settings
    ENCODING = "utf-8"


class ContentConfig:
    """Configuration for content generation"""

    # GitHub API settings
    GITHUB_API_BASE = "https://api.github.com"
    DEFAULT_CACHE_HOURS = 1
    MAX_README_LENGTH = 5000

    # Trending repositories
    DEFAULT_LANGUAGE = "python"
    TRENDING_LIMIT = 10

    # Podcast conversion settings
    DEFAULT_STYLE = "educational"
    DEFAULT_LENGTH = "medium"

    # Claude CLI settings
    CLAUDE_TIMEOUT = 120  # seconds
    MAX_DIALOGUE_SEGMENTS = 24


# Global configuration instance
config = {
    'video': VideoConfig(),
    'audio': AudioConfig(),
    'files': FileConfig(),
    'logging': LogConfig(),
    'content': ContentConfig()
}