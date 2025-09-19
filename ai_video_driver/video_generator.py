"""
Video generation module using Manim for synchronized subtitle animations.
"""

import os
import re
import logging
from pathlib import Path
import torchaudio
from .config import config as app_config
from manim import (
    Scene,
    Text,
    VGroup,
    Write,
    FadeOut,
    AnimationGroup,
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
        logger.debug(
            f"Parsed subtitle: {speaker} at {start_sec:.2f}s: {clean_text[:50]}..."
        )

    logger.info(f"Successfully parsed {len(subtitles)} subtitles")
    return subtitles


class DialogueScene(Scene):
    """Manim scene for rendering dialogue with speaker-colored text"""

    def __init__(self, subtitles, audio_duration, **kwargs):
        super().__init__(**kwargs)
        self.subtitles = subtitles
        self.audio_duration = audio_duration
        logger.debug(
            f"Initialized DialogueScene with {len(subtitles)} subtitles, duration: {audio_duration:.2f}s"
        )

    def construct(self):
        logger.info("Starting Manim scene construction")

        # Speaker colors from config
        speaker_colors = {
            "S1": app_config["video"].SPEAKER_COLORS.get("S1", "#3498db"),
            "S2": app_config["video"].SPEAKER_COLORS.get("S2", "#2ecc71"),
            "S3": app_config["video"].SPEAKER_COLORS.get("S3", "#f1c40f"),
            "S4": app_config["video"].SPEAKER_COLORS.get("S4", "#9b59b6"),
        }
        current_texts = []

        # Screen configuration
        screen_height = config.frame_height
        max_visible_height = screen_height * 0.8  # Use 80% of screen height
        line_height = 0.8  # Approximate height per line including spacing
        max_visible_lines = int(max_visible_height / line_height)

        for i, subtitle in enumerate(self.subtitles):
            logger.debug(
                f"Processing subtitle {i+1}/{len(self.subtitles)}: {subtitle['speaker']}"
            )

            # Create text object with wrapping
            speaker_color = speaker_colors.get(subtitle["speaker"], WHITE)

            # Speaker label
            speaker_label = Text(
                f"{subtitle['speaker']}:",
                font_size=app_config["video"].SPEAKER_FONT_SIZE,
                color=speaker_color,
            ).to_edge(LEFT, buff=0.5)

            # Calculate available width for main text
            available_width = (
                config.frame_width - speaker_label.width - 1.0
            )  # Leave some margin

            # Create main text with wrapping
            main_text = self._create_wrapped_text(
                subtitle["text"],
                max_width=available_width,
                font_size=app_config["video"].TEXT_FONT_SIZE,
                color=WHITE,
            )

            # Position main text next to speaker label
            main_text.next_to(speaker_label, RIGHT, buff=0.3)

            # Align the top of main text with speaker label
            main_text.align_to(speaker_label, UP)

            # Group speaker and text
            full_text = VGroup(speaker_label, main_text)

            # Position based on existing texts
            if current_texts:
                full_text.next_to(current_texts[-1], DOWN, buff=0.3, aligned_edge=LEFT)
            else:
                full_text.to_edge(UP, buff=1)

            current_texts.append(full_text)

            # Check if we need to scroll
            total_height = sum(text.height + 0.3 for text in current_texts)

            if total_height > max_visible_height and len(current_texts) > 1:
                # Calculate how much we need to scroll up to make room for new text
                excess_height = total_height - max_visible_height

                # First scroll existing texts (excluding the new one) up smoothly
                scroll_animations = []
                for text in current_texts[:-1]:  # Exclude the newly added text
                    scroll_animations.append(text.animate.shift(UP * excess_height))

                if scroll_animations:
                    self.play(AnimationGroup(*scroll_animations), run_time=0.5)

                # Position the new text at the scrolled position
                full_text.shift(UP * excess_height)

                # Then write the new text
                write_duration = min(0.5, subtitle["duration"] * 0.3)
                self.play(Write(full_text), run_time=write_duration)
            else:
                # Normal text appearance without scrolling
                write_duration = min(0.5, subtitle["duration"] * 0.3)
                self.play(Write(full_text), run_time=write_duration)

            # Hold text for remaining duration
            hold_time = subtitle["duration"] - write_duration
            if hold_time > 0:
                self.wait(hold_time)

            # Remove texts that have scrolled off screen
            texts_to_remove = []
            for text in current_texts:
                if text.get_bottom()[1] > screen_height / 2:  # Above visible area
                    texts_to_remove.append(text)

            for text in texts_to_remove:
                current_texts.remove(text)
                self.remove(text)

        # Wait for any remaining audio
        final_wait = max(
            0, self.audio_duration - sum(sub["duration"] for sub in self.subtitles)
        )
        if final_wait > 0:
            logger.debug(f"Adding final wait of {final_wait:.2f}s")
            self.wait(final_wait)

        logger.info("Completed Manim scene construction")

    def _split_mixed_text(self, text):
        """Split text handling both English words and Chinese characters with punctuation"""
        import re

        # Split on Chinese punctuation and whitespace while preserving them
        # This regex captures: whitespace, Chinese punctuation, and keeps them as separators
        chinese_punct = r'[，。！？；：、（）【】《》""''…—]'
        pattern = rf'(\s+|{chinese_punct})'

        # Split and filter out empty strings
        parts = [part.strip() for part in re.split(pattern, text) if part.strip()]

        # Further process to handle mixed content better
        words = []
        for part in parts:
            # If it's punctuation, add it as is
            if re.match(chinese_punct, part):
                words.append(part)
            # If it contains both English and Chinese, try to split more intelligently
            elif any('\u4e00' <= char <= '\u9fff' for char in part):
                # Contains Chinese characters
                # Split on word boundaries but keep Chinese chars together
                subparts = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+|\d+|[^\s\u4e00-\u9fff\w]', part)
                words.extend(subparts)
            else:
                # Pure English/numbers, split by space
                words.extend(part.split())

        return [word for word in words if word]

    def _create_wrapped_text(self, text, max_width, font_size=None, color=WHITE):
        """Create text with word wrapping to fit within max_width"""
        if font_size is None:
            font_size = app_config["video"].TEXT_FONT_SIZE
        words = self._split_mixed_text(text)
        lines = []
        current_line = []

        # Create a test text to measure width
        test_text = Text("", font_size=font_size)

        for word in words:
            test_line = " ".join(current_line + [word])
            test_text.become(Text(test_line, font_size=font_size))

            if test_text.width <= max_width:
                current_line.append(word)
            else:
                if current_line:  # If current line has words, start new line
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:  # If single word is too long, add it anyway
                    lines.append(word)
                    current_line = []

        # Add remaining words
        if current_line:
            lines.append(" ".join(current_line))

        # Create VGroup of text lines
        text_lines = []
        for line in lines:
            text_line = Text(line, font_size=font_size, color=color)
            text_lines.append(text_line)

        if text_lines:
            # Arrange lines vertically
            wrapped_text = VGroup(*text_lines)
            wrapped_text.arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            return wrapped_text
        else:
            # Return empty text if no content
            return Text("", font_size=font_size, color=color)


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
        partial_dir = (
            temp_dir / "videos" / "720p30" / "partial_movie_files" / "DialogueScene"
        )
        if partial_dir.exists():
            partial_files = sorted(list(partial_dir.glob("*.mp4")))
            if partial_files:
                logger.info(
                    f"Found {len(partial_files)} partial video files, combining manually..."
                )

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
                    logger.info(
                        f"Successfully combined partial files into: {video_file}"
                    )
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
