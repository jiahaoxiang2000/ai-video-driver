# AI Video Driver

A modular video generation pipeline for FireRedTTS2 that creates synchronized video content from conversational speech.

## Package Structure

```
ai_video_driver/
├── __init__.py          # Package exports and main interface
├── video_generator.py   # Manim-based video generation
├── file_utils.py        # File management and I/O operations
├── logger.py           # Centralized logging and timing utilities
├── config.py           # Configuration settings and constants
└── README.md           # This file
```

## Core Components

### 🎬 Video Generator (`video_generator.py`)
- **SRT Parsing**: Converts subtitle timing to Manim animations
- **DialogueScene**: Multi-speaker video scenes with color-coded text
- **Fallback Recovery**: Handles Manim failures with ffmpeg partial file recovery
- **Audio/Video Combination**: Uses ffmpeg to merge silent video with audio

### 📁 File Utils (`file_utils.py`)
- **Output Structure**: Creates organized timestamp-based directories
- **File Operations**: Handles audio/SRT saving with proper error handling
- **Cleanup**: Optional temp file management
- **File Info**: Logging helpers for file sizes and metadata

### 📝 Logger (`logger.py`)
- **Pipeline Logging**: Comprehensive logging with file and console output
- **Timing Context**: `PipelineTimer` for measuring step durations
- **Standardized Formats**: Consistent log formatting with emojis
- **Module Control**: Separate log levels for different components

### ⚙️ Config (`config.py`)
- **Video Settings**: Quality, resolution, animation parameters
- **Audio Settings**: Sample rates, TTS parameters
- **File Settings**: Directory structure, naming conventions
- **Log Settings**: Format, levels, output configuration

## Usage

### Basic Import
```python
from ai_video_driver import (
    generate_video_from_srt,
    combine_audio_video,
    create_output_structure,
    setup_pipeline_logging
)
```

### With Enhanced Logging
```python
from ai_video_driver import PipelineTimer, config

logger = setup_pipeline_logging()

with PipelineTimer("Generate Video", logger):
    video_file = generate_video_from_srt(srt_content, audio_file, output_dir, temp_dir)
```

### Configuration Access
```python
from ai_video_driver import config

# Access video settings
quality = config['video'].QUALITY
sample_rate = config['audio'].SAMPLE_RATE
log_level = config['logging'].LEVEL
```

## Pipeline Flow

1. **Initialize** → Setup logging and configuration
2. **Create Structure** → Organized output directories
3. **Generate TTS** → FireRedTTS2 audio and SRT
4. **Save Files** → Audio and subtitles with metadata
5. **Generate Video** → Manim animation from SRT timing
6. **Combine Media** → Final video with synchronized audio

## Output Structure

```
output/chat_clone_YYYYMMDD_HHMMSS/
├── final_video_with_audio.mp4  # Main deliverable
├── video_silent.mp4            # Silent video component
├── audio.wav                   # TTS-generated audio
├── subtitles.srt              # Timed subtitles
└── temp/                      # Temporary Manim files
    ├── videos/
    ├── filelist.txt
    └── dialogue_video.mp4
```

## Features

- ✅ **Modular Design**: Clean separation of concerns
- ✅ **Error Recovery**: Graceful fallbacks for video generation
- ✅ **Comprehensive Logging**: File and console with timing
- ✅ **Configurable**: Easy customization via config classes
- ✅ **Professional Output**: Standardized file organization
- ✅ **Multi-speaker Support**: Color-coded dialogue animations