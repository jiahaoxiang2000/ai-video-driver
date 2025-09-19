<div align="center">
    <h1>
    AI Video Driver
    </h1>
    <p>
    AI-powered automatic video driver creation tool <br>
    <b><em>Leveraging FireRedTTS-2 for intelligent video content generation</em></b>
    </p>
    <p>
    </p>
    <a href="https://github.com/jiahaoxiang2000/ai-video-driver"><img src="https://img.shields.io/badge/GitHub-Repository-blue" alt="GitHub repo"></a>
    <a href="https://github.com/jiahaoxiang2000/ai-video-driver"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="Apache-2.0"></a>
</div>

## Overview

AI Video Driver is an intelligent tool that leverages the power of FireRedTTS-2 for **automatic video content generation**. This system combines advanced text-to-speech capabilities with AI-driven video creation workflows to produce engaging multimedia content automatically.

## Architecture

### Core Components

The system is built with a modular architecture consisting of three main layers:

#### 1. **FireRedTTS2 Engine** (`fireredtts2/`)
- **TTS Core** (`fireredtts2.py`) - Main text-to-speech synthesis engine
- **Audio Codec** (`codec/`) - Audio encoding/decoding, neural vocoding (RVQ), Whisper integration
- **Language Models** (`llm/`) - Neural language processing and dialogue understanding
- **Utilities** (`utils/`) - Text processing and splitting utilities

#### 2. **AI Video Driver** (`ai_video_driver/`)
- **Video Generator** (`video_generator.py`) - Manim-based video scene generation and audio-video synchronization
- **File Management** (`file_utils.py`) - Output structure management and file operations
- **Configuration** (`config.py`) - Pipeline settings and parameters
- **Logging** (`logger.py`) - Enhanced logging and performance monitoring

#### 3. **Main Pipeline** (`main.py`)
- Orchestrates the complete video generation workflow
- Handles multi-speaker dialogue processing
- Manages timing synchronization between audio and video
- Provides comprehensive error handling and logging

### Data Flow

```
Text Input → FireRedTTS2 → Audio Generation → SRT Generation → Video Creation → Final Output
    ↓             ↓              ↓               ↓              ↓
Dialogue     Multi-speaker   Synchronized    Manim Scene   Combined A/V
Processing   Voice Cloning   Subtitles       Animation     with Subtitles
```

