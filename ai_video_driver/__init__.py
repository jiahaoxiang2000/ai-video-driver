"""
AI Video Driver - Video generation pipeline for FireRedTTS2.

This package provides modular components for generating synchronized video
content from conversational speech using FireRedTTS2 and Manim.
"""

__version__ = "0.1.0"
__author__ = "FireRedTTS2 Video Pipeline"

from .video_generator import generate_video_from_srt, combine_audio_video
from .file_utils import create_output_structure, save_files, get_file_info
from .logger import setup_pipeline_logging, PipelineTimer, log_file_info
from .config import config

__all__ = [
    "generate_video_from_srt",
    "combine_audio_video",
    "create_output_structure",
    "save_files",
    "get_file_info",
    "setup_pipeline_logging",
    "PipelineTimer",
    "log_file_info",
    "config"
]