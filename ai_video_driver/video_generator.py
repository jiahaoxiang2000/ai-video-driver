"""
Video generation module using Manim for synchronized subtitle animations.
"""

import os
import re
import logging
from pathlib import Path
import torchaudio
from manim import (
    Scene,
    Text,
    VGroup,
    Write,
    FadeOut,
    config,
    BLUE,
    GREEN,
    YELLOW,
    PURPLE,
    WHITE,
    LEFT,
    RIGHT,
    DOWN,
    UP,
)

logger = logging.getLogger(__name__)


def parse_srt_for_manim(srt_content):
    """Parse SRT content to extract timing and text for Manim animation"""
    logger.info("Parsing SRT content for Manim animation")
    pattern = r"(\d+)\n([\d:,]+) --> ([\d:,]+)\n(.+?)(?=\n\n|\n\d+\n|$)"
    matches = re.findall(pattern, srt_content, re.DOTALL)
    logger.debug(f"Found {len(matches)} subtitle entries")

    subtitles = []
    for match in matches:
        _, start_time, end_time, text = match

        # Convert time format to seconds
        def time_to_seconds(time_str):
            time_str = time_str.replace(",", ".")
            parts = time_str.split(":")
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])

        start_sec = time_to_seconds(start_time)
        end_sec = time_to_seconds(end_time)

        # Extract speaker if present
        speaker = "S1"  # default
        clean_text = text.strip()
        if clean_text.startswith("[S"):
            speaker_match = re.match(r"\[([^\]]+)\](.+)", clean_text)
            if speaker_match:
                speaker = speaker_match.group(1)
                clean_text = speaker_match.group(2).strip()

        subtitle_data = {
            "start": start_sec,
            "end": end_sec,
            "duration": end_sec - start_sec,
            "text": clean_text,
            "speaker": speaker,
        }
        subtitles.append(subtitle_data)
        logger.debug(f"Parsed subtitle: {speaker} at {start_sec:.2f}s: {clean_text[:50]}...")

    logger.info(f"Successfully parsed {len(subtitles)} subtitles")
    return subtitles


class DialogueScene(Scene):
    """Manim scene for rendering dialogue with speaker-colored text"""

    def __init__(self, subtitles, audio_duration, **kwargs):
        super().__init__(**kwargs)
        self.subtitles = subtitles
        self.audio_duration = audio_duration
        logger.debug(f"Initialized DialogueScene with {len(subtitles)} subtitles, duration: {audio_duration:.2f}s")

    def construct(self):
        logger.info("Starting Manim scene construction")

        # Speaker colors
        speaker_colors = {"S1": BLUE, "S2": GREEN, "S3": YELLOW, "S4": PURPLE}
        current_texts = []

        for i, subtitle in enumerate(self.subtitles):
            logger.debug(f"Processing subtitle {i+1}/{len(self.subtitles)}: {subtitle['speaker']}")

            # Create text object
            speaker_color = speaker_colors.get(subtitle["speaker"], WHITE)

            # Speaker label
            speaker_label = Text(
                f"{subtitle['speaker']}:", font_size=24, color=speaker_color
            ).to_edge(LEFT, buff=0.5)

            # Main text
            main_text = Text(
                subtitle["text"], font_size=20, color=WHITE, line_spacing=0.5
            ).next_to(speaker_label, RIGHT, buff=0.3)

            # Group speaker and text
            full_text = VGroup(speaker_label, main_text)

            # Position based on existing texts
            if current_texts:
                full_text.next_to(current_texts[-1], DOWN, buff=0.3, aligned_edge=LEFT)
            else:
                full_text.to_edge(UP, buff=1)

            # Animate text appearance
            write_duration = min(0.5, subtitle["duration"] * 0.3)
            self.play(Write(full_text), run_time=write_duration)

            # Hold text for remaining duration
            hold_time = subtitle["duration"] - write_duration
            if hold_time > 0:
                self.wait(hold_time)

            current_texts.append(full_text)

            # Fade older texts if screen gets crowded
            if len(current_texts) > 4:
                old_text = current_texts.pop(0)
                self.play(FadeOut(old_text), run_time=0.3)

        # Wait for any remaining audio
        final_wait = max(
            0, self.audio_duration - sum(sub["duration"] for sub in self.subtitles)
        )
        if final_wait > 0:
            logger.debug(f"Adding final wait of {final_wait:.2f}s")
            self.wait(final_wait)

        logger.info("Completed Manim scene construction")


def generate_video_from_srt(srt_content, audio_file, output_dir, temp_dir):
    """Generate video using Manim based on SRT timing"""
    logger.info(f"Starting video generation from SRT, audio: {audio_file}")

    subtitles = parse_srt_for_manim(srt_content)

    # Get audio duration
    audio_info = torchaudio.info(str(audio_file))
    audio_duration = audio_info.num_frames / audio_info.sample_rate
    logger.info(f"Audio duration: {audio_duration:.2f} seconds")

    # Configure Manim to generate video without audio first
    config.media_dir = str(temp_dir)
    config.output_file = str(temp_dir / "dialogue_video")
    config.format = "mp4"
    config.quality = "medium_quality"
    config.disable_caching = True
    logger.debug("Configured Manim settings")

    try:
        logger.info("Attempting to render scene with Manim")
        # Create and render scene (without audio)
        scene = DialogueScene(subtitles, audio_duration)
        scene.render()

        # Find the generated video file in temp directory
        generated_videos = list(temp_dir.glob("**/*.mp4"))
        if generated_videos:
            video_file = output_dir / "video_silent.mp4"
            os.system(f"cp '{generated_videos[0]}' '{video_file}'")
            logger.info(f"Successfully generated video: {video_file}")
            return video_file
        else:
            logger.warning("No video file generated by Manim")
            return None

    except Exception as e:
        logger.error(f"Manim rendering failed: {e}")
        logger.info("Attempting to recover using partial video files")

        # Try to combine partial video files manually using ffmpeg
        partial_dir = temp_dir / "videos" / "720p30" / "partial_movie_files" / "DialogueScene"
        if partial_dir.exists():
            partial_files = sorted(list(partial_dir.glob("*.mp4")))
            if partial_files:
                logger.info(f"Found {len(partial_files)} partial video files, combining manually...")

                # Create file list for ffmpeg concat
                filelist_path = temp_dir / "filelist.txt"
                with open(filelist_path, "w") as f:
                    for partial_file in partial_files:
                        f.write(f"file '{partial_file.absolute()}'\n")

                # Combine using ffmpeg
                video_file = output_dir / "video_silent.mp4"
                concat_cmd = f"ffmpeg -f concat -safe 0 -i '{filelist_path}' -c copy '{video_file}' -y -loglevel warning"
                logger.debug(f"Running ffmpeg command: {concat_cmd}")
                result = os.system(concat_cmd)

                if result == 0 and video_file.exists():
                    logger.info(f"Successfully combined partial files into: {video_file}")
                    return video_file
                else:
                    logger.error("Failed to combine partial video files")
                    return None
            else:
                logger.error("No partial video files found")
                return None
        else:
            logger.error("Partial video directory not found")
            return None


def combine_audio_video(audio_file, video_file, output_file):
    """Combine audio and video using ffmpeg"""
    logger.info(f"Combining audio {audio_file} with video {video_file}")

    cmd = f"ffmpeg -i '{video_file}' -i '{audio_file}' -c:v copy -c:a aac -strict experimental '{output_file}' -y -loglevel warning"
    logger.debug(f"Running ffmpeg command: {cmd}")

    result = os.system(cmd)

    if result == 0 and Path(output_file).exists():
        logger.info(f"Successfully created final video: {output_file}")
        return True
    else:
        logger.error(f"Failed to combine audio and video")
        return False