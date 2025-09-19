"""
Centralized logging configuration for the AI Video Driver pipeline.
"""

import logging
import sys
import time
from pathlib import Path
from .config import config


def setup_pipeline_logging(log_level=None):
    """Setup comprehensive logging configuration for the pipeline"""

    log_config = config['logging']
    files_config = config['files']

    if log_level is None:
        log_level = log_config.LEVEL

    # Create logs directory if it doesn't exist
    log_dir = Path(files_config.LOGS_DIR)
    log_dir.mkdir(exist_ok=True)

    # Create timestamp for log file
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"video_generation_{timestamp}.log"

    # Setup file and console handlers
    logging.basicConfig(
        level=log_level,
        format=log_config.FORMAT,
        datefmt=log_config.DATE_FORMAT,
        handlers=[
            logging.FileHandler(log_file, encoding=log_config.ENCODING),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set specific module log levels
    logging.getLogger("manim").setLevel(log_config.MANIM_LOG_LEVEL)
    logging.getLogger("ffmpeg").setLevel(log_config.FFMPEG_LOG_LEVEL)

    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info("🚀 AI Video Driver Pipeline Starting")
    logger.info(f"📝 Log file: {log_file}")
    logger.info("="*60)

    return logger


def get_logger(name):
    """Get a logger for a specific module"""
    return logging.getLogger(name)


class PipelineTimer:
    """Context manager for timing pipeline steps"""

    def __init__(self, step_name, logger=None):
        self.step_name = step_name
        self.logger = logger or get_logger(__name__)
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"🔄 Starting: {self.step_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if exc_type is None:
            self.logger.info(f"✅ Completed: {self.step_name} ({duration:.2f}s)")
        else:
            self.logger.error(f"❌ Failed: {self.step_name} ({duration:.2f}s) - {exc_val}")


def log_file_info(file_path, logger=None, prefix="📄"):
    """Log file information in a standardized format"""
    if logger is None:
        logger = get_logger(__name__)

    try:
        path = Path(file_path)
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            logger.info(f"{prefix} {path.name} ({size_mb:.2f} MB)")
        else:
            logger.warning(f"{prefix} {path.name} (not found)")
    except Exception as e:
        logger.error(f"{prefix} {file_path} (error: {e})")


def log_step_summary(step_num, total_steps, description, logger=None):
    """Log a standardized step header"""
    if logger is None:
        logger = get_logger(__name__)

    logger.info(f"📋 Step {step_num}/{total_steps}: {description}")


def log_pipeline_summary(output_dir, final_file, total_time, logger=None):
    """Log final pipeline summary"""
    if logger is None:
        logger = get_logger(__name__)

    logger.info("="*60)
    logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    logger.info(f"📁 Output directory: {output_dir}")
    logger.info(f"🎬 Final video: {Path(final_file).name}")
    logger.info(f"⏱️  Total processing time: {total_time:.2f} seconds")
    logger.info("="*60)

    # Log all output files
    logger.info("📋 Generated files:")
    for file_path in Path(output_dir).glob("*"):
        if file_path.is_file():
            log_file_info(file_path, logger, "   •")