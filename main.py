"""
Enhanced FireRedTTS2 main script with modular video generation pipeline.

This script generates conversational speech using FireRedTTS2, creates synchronized
video animations with Manim, and combines everything into a final video output.
"""

import sys
import time
import argparse
import os
from typing import Optional, List, Dict, Any
from pathlib import Path

from fireredtts2.fireredtts2 import FireRedTTS2
from ai_video_driver import (
    generate_video_from_srt,
    combine_audio_video,
    create_output_structure,
    save_files,
    setup_pipeline_logging,
    PipelineTimer,
    log_file_info,
    config,
)
from ai_video_driver.content_fetcher import GitHubContentFetcher
from ai_video_driver.podcast_converter import PodcastConverter

# Global voice prompt configuration
PROMPT_WAV_LIST = [
    "audio/S1.flac",
    "audio/S2.wav",
]

# "audio/S1.wav", ourself
# "[S1]然后，额外再讲一下，就是他有一个，这个，他这个插件有一个可以自定义它的一个json",

# "audio/mid-man.wav"
# "[S1]那我这里主要是focus的是英文podcast，那很多观众听到这里可能会觉得自己英文水平不好，不敢收听纯英文节目,那这里我想告诉你",


PROMPT_TEXT_LIST = [
    "[S1]啊，可能说更适合美国市场应该是什么样子。那这这个可能说，当然如果说有有机会能亲身的去考察去了解一下，那当然是有更好的帮助。",
    "[S2]从剧场转影视之后有什么差别，然后你的适应呀等等，你觉得你做了什么样的调试。",
]


def get_default_dialogue():
    """Default dialogue content about FireRedTTS2"""
    return [
        "[S1]嗯，最近发现了一个很厉害的TTS系统叫FireRedTTS2。它最大的特点就是可以generate long conversational speech，支持multi-speaker dialogue generation。",
        "[S2]真的吗？那它跟其他的TTS有什么不同呢？",
        "[S1]这个system很特别，它可以支持3分钟的dialogue with 4 speakers，而且还有ultra-low latency。在L20 GPU上，first-packet latency只要140ms。最重要的是它支持multi lingual，包括English、Chinese、Japanese、Korean、French、German还有Russian。",
        "[S2]听起来很powerful啊。那它还有什么其他features吗？",
        "[S1]对，它还有zero-shot voice cloning功能，可以做cross-lingual和code-switching scenarios。而且还有random timbre generation，这个对creating ASR data很有用。最关键是stability很强，在monologue和dialogue tests里都有high similarity和low WER/CER。",
        "[S2]那这个是open source的吗？",
        "[S1]是的，它基于Apache 2.0 license。你可以在GitHub上找到FireRedTeam/FireRedTTS2，还有pre-trained checkpoints在Hugging Face上。不过要注意，voice cloning功能只能用于academic research purposes。",
    ]


def generate_content_from_repo(
    repo_url: str, style: str, length: str, github_token: Optional[str] = None
) -> list:
    """Generate dialogue content from a GitHub repository"""
    logger = setup_pipeline_logging()

    try:
        # Initialize content fetcher
        fetcher = GitHubContentFetcher(github_token=github_token)

        # Fetch repository content
        logger.info(f"Fetching content from repository: {repo_url}")
        repo_content = fetcher.fetch_repository_content(repo_url)

        if not repo_content:
            logger.error("Failed to fetch repository content")
            return get_default_dialogue()

        # Convert to podcast format
        converter = PodcastConverter()
        dialogue = converter.convert_to_podcast(
            repo_content, style=style, length=length
        )

        if dialogue and converter.validate_dialogue_format(dialogue):
            logger.info(f"Successfully generated {len(dialogue)} dialogue segments")
            return dialogue
        else:
            logger.warning("Generated dialogue failed validation, using fallback")
            return create_fallback_dialogue(
                {
                    "name": repo_content.get("name", ""),
                    "description": repo_content.get("description", ""),
                    "language": repo_content.get("language", ""),
                    "stargazers_count": repo_content.get("stars", 0),
                }
            )

    except Exception as e:
        logger.error(f"Failed to generate content from repository: {e}")
        return get_default_dialogue()


def get_top5_trending_repos(github_token: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get top 5 unrecorded trending repositories"""
    logger = setup_pipeline_logging()

    try:
        # Initialize content fetcher
        fetcher = GitHubContentFetcher(github_token=github_token)

        # Get top 5 trending repositories
        logger.info("Fetching top 5 unrecorded trending repositories")
        trending_repos = fetcher.get_top5_unrecorded_trending_repos()

        if not trending_repos:
            logger.error("No trending repositories found")
            return []

        logger.info(f"Found {len(trending_repos)} trending repositories")
        for i, repo in enumerate(trending_repos, 1):
            logger.info(
                f"{i}. {repo.get('full_name', 'Unknown')} - {repo.get('stargazers_count', 0)} stars"
            )

        return trending_repos

    except Exception as e:
        logger.error(f"Failed to get trending repositories: {e}")
        return []


def generate_multi_repo_content(
    style: str,
    length: str,
    device: str,
    output_name: str,
    github_token: Optional[str] = None,
) -> bool:
    """Generate content from top 5 trending repos and create combined video"""
    logger = setup_pipeline_logging()

    try:
        # Get top 5 trending repositories
        trending_repos = get_top5_trending_repos(github_token)

        if not trending_repos:
            logger.error("No trending repositories found")
            return False

        logger.info(f"Processing {len(trending_repos)} trending repositories")

        # Create main output directory
        main_output_dir = Path(f"outputs/{output_name}_multi_repo")
        main_output_dir.mkdir(parents=True, exist_ok=True)

        generated_videos = []
        video_titles = []
        repo_dialogues = []

        # Process each repository and collect dialogues
        for i, repo in enumerate(trending_repos, 1):
            repo_name = repo.get("full_name", f"repo_{i}")
            logger.info(f"Processing repository {i}/5: {repo_name}")

            # Convert repo to podcast
            podcast_dialogue = convert_repo_to_podcast(
                repo, style, length, github_token
            )

            if not podcast_dialogue:
                logger.warning(f"Failed to generate podcast for {repo_name}, skipping")
                continue

            # Store dialogue for summary generation
            repo_dialogues.append((repo_name, podcast_dialogue))

            # Generate video for this podcast
            video_file = generate_video_for_podcast(
                podcast_dialogue, repo_name, device, main_output_dir
            )

            if video_file:
                generated_videos.append(video_file)
                video_titles.append(repo_name)
                logger.info(f"Successfully generated video {i}/5 for {repo_name}")
            else:
                logger.warning(f"Failed to generate video for {repo_name}")

        # Generate summary video from collected dialogues
        if repo_dialogues:
            logger.info("Generating summary video from top 5 repositories")
            summary_dialogue = create_summary_dialogue(repo_dialogues)

            summary_video = generate_video_for_podcast(
                summary_dialogue, "summary_introduction", device, main_output_dir
            )

            if summary_video:
                # Insert summary video at the beginning
                generated_videos.insert(0, summary_video)
                video_titles.insert(0, "intro")
                logger.info("Successfully generated summary introduction video")
            else:
                logger.warning("Failed to generate summary video")

        # Combine all videos
        if generated_videos:
            final_combined_video = main_output_dir / "combined_final.mp4"
            success = combine_videos(generated_videos, final_combined_video, video_titles)

            if success:
                logger.info("🎉 MULTI-REPO PIPELINE COMPLETED SUCCESSFULLY!")
                logger.info(f"📁 Output directory: {main_output_dir}")
                logger.info(f"🎬 Combined video: {final_combined_video}")
                logger.info(
                    f"📊 Generated {len(generated_videos)} total videos (including summary)"
                )
                print(f"\n🎬 Final combined video: {final_combined_video}")
                print(f"📁 All files: {main_output_dir}")
                return True
            else:
                logger.error("Failed to combine videos")
                print(f"\n⚠️  Video combination failed")
                print(f"📁 Individual videos: {main_output_dir}")
                return False
        else:
            logger.error("No videos were generated")
            return False

    except Exception as e:
        logger.error(f"Failed to generate multi-repo content: {e}")
        return False


def convert_repo_to_podcast(
    repo_info: Dict[str, Any],
    style: str,
    length: str,
    github_token: Optional[str] = None,
) -> List[str]:
    """Convert a single repository to podcast dialogue"""
    logger = setup_pipeline_logging()

    try:
        # Get repository URL
        repo_url = repo_info.get("html_url")
        if not repo_url:
            logger.error("No repository URL found")
            return get_default_dialogue()

        # Fetch detailed repository content
        fetcher = GitHubContentFetcher(github_token=github_token)
        repo_content = fetcher.fetch_repository_content(repo_url)

        if not repo_content:
            logger.error(
                f"Failed to fetch content for {repo_info.get('full_name', 'Unknown')}"
            )
            return get_default_dialogue()

        # Convert to podcast format
        converter = PodcastConverter()
        dialogue = converter.convert_to_podcast(
            repo_content, style=style, length=length
        )

        if dialogue and converter.validate_dialogue_format(dialogue):
            logger.info(
                f"Successfully converted {repo_info.get('full_name', 'Unknown')} to {len(dialogue)} dialogue segments"
            )

            # Mark repo as recorded
            fetcher.mark_repo_as_recorded(repo_info.get("full_name", ""))

            return dialogue
        else:
            logger.warning(
                f"Generated dialogue failed validation for {repo_info.get('full_name', 'Unknown')}, using fallback"
            )
            # Create a simple fallback dialogue based on repo info
            return create_fallback_dialogue(repo_info)

    except Exception as e:
        logger.error(f"Failed to convert repository to podcast: {e}")
        return get_default_dialogue()


def create_summary_dialogue(repo_dialogues: List[tuple]) -> List[str]:
    """Create a summary dialogue from multiple repository dialogues using AI"""
    logger = setup_pipeline_logging()

    try:
        # Initialize PodcastConverter for AI generation
        converter = PodcastConverter()

        if not converter.check_api_availability():
            logger.warning("AI API not available, using fallback summary")
            return _create_fallback_summary(repo_dialogues)

        # Prepare summary content from all repo dialogues
        summary_content = _prepare_summary_content(repo_dialogues)

        # Generate AI summary dialogue
        summary_dialogue = converter._generate_summary_dialogue(summary_content)

        if summary_dialogue and converter.validate_dialogue_format(summary_dialogue):
            logger.info(
                f"Successfully generated AI summary with {len(summary_dialogue)} segments"
            )
            return summary_dialogue
        else:
            logger.warning("AI summary generation failed, using fallback")
            return _create_fallback_summary(repo_dialogues)

    except Exception as e:
        logger.error(f"Failed to create AI summary dialogue: {e}")
        return _create_fallback_summary(repo_dialogues)


def _prepare_summary_content(repo_dialogues: List[tuple]) -> Dict[str, str]:
    """Prepare content for summary generation"""
    repo_names = [repo_name for repo_name, _ in repo_dialogues]

    # Extract key points from each dialogue
    repo_summaries = []
    for repo_name, dialogue in repo_dialogues:
        # Take first few dialogue segments as key points
        key_points = dialogue[:3] if len(dialogue) >= 3 else dialogue
        repo_summaries.append(
            f"Repository: {repo_name}\nKey discussion points: {' '.join(key_points)}"
        )

    summary_content = {
        "name": "GitHub Top 5 Trending Repositories Summary",
        "description": f"Summary of top 5 trending repositories: {', '.join(repo_names)}",
        "readme": "\n\n".join(repo_summaries),
    }

    return summary_content


def _create_fallback_summary(repo_dialogues: List[tuple]) -> List[str]:
    """Fallback summary when AI generation fails"""
    repo_names = [repo_name for repo_name, _ in repo_dialogues]

    summary_dialogue = [
        "[S1]欢迎收听今天的GitHub热门项目podcast！今天我们将为大家介绍5个最受关注的开源项目。",
        "[S2]听起来很exciting啊！都有哪些有趣的项目呢？",
        f"[S1]今天我们会深入了解{', '.join(repo_names[:3])}等项目，它们各有特色，涵盖了不同的技术领域。",
        "[S2]太好了！让我们一起来探索这些amazing的开源项目吧！",
        "[S1]没错，接下来我们就逐一介绍这些项目，相信你们会有很多收获。Let's get started!",
    ]

    return summary_dialogue


def create_fallback_dialogue(repo_info: Dict[str, Any]) -> List[str]:
    """Create fallback dialogue based on repository information"""
    name = repo_info.get("name", "Unknown Repository")
    description = repo_info.get("description", "")
    language = repo_info.get("language", "")
    stars = repo_info.get("stargazers_count", 0)

    dialogue = [
        f"[S1]今天我们来聊聊GitHub上一个有趣的项目叫{name}。",
        f"[S2]听起来很有意思，这个project是做什么的呢？",
    ]

    if description:
        dialogue.append(f"[S1]{description}")
        dialogue.append(f"[S2]那这个项目有什么特别的功能吗？")

    if language:
        dialogue.append(f"[S1]这个project主要是用{language}开发的。")

    if stars > 0:
        dialogue.append(f"[S2]看起来很受欢迎啊，有{stars}个stars了。")
        dialogue.append(f"[S1]是的，说明这个项目确实有价值，值得大家关注。")

    return dialogue


def generate_video_for_podcast(
    podcast_dialogue: List[str], repo_name: str, device: str, output_base_dir: Path
) -> Optional[Path]:
    """Generate a single video from podcast dialogue"""
    logger = setup_pipeline_logging()

    try:
        # Create unique output directory for this repo
        repo_output_dir = output_base_dir / f"repo_{repo_name.replace('/', '_')}"
        repo_output_dir.mkdir(parents=True, exist_ok=True)
        temp_dir = repo_output_dir / "temp"
        temp_dir.mkdir(exist_ok=True)

        logger.info(
            f"Generating video for {repo_name} with {len(podcast_dialogue)} dialogue segments"
        )

        # Initialize FireRedTTS2
        fireredtts2 = FireRedTTS2(
            pretrained_dir="./pretrained_models/FireRedTTS2",
            gen_type="dialogue",
            device=device,
        )

        prompt_wav_list = PROMPT_WAV_LIST

        prompt_text_list = PROMPT_TEXT_LIST

        # Generate TTS audio and SRT
        all_audio, srt_text = fireredtts2.generate_dialogue(
            text_list=podcast_dialogue,
            prompt_wav_list=prompt_wav_list,
            prompt_text_list=prompt_text_list,
            temperature=config["audio"].DEFAULT_TEMPERATURE,
            topk=config["audio"].DEFAULT_TOPK,
        )

        # Save audio and SRT files
        audio_file, _ = save_files(
            repo_output_dir, all_audio, srt_text, config["audio"].SAMPLE_RATE
        )

        # Generate video from SRT
        video_file = generate_video_from_srt(
            srt_text, audio_file, repo_output_dir, temp_dir
        )

        if video_file and video_file.exists():
            # Combine audio with video
            final_video = repo_output_dir / f"{repo_name.replace('/', '_')}_final.mp4"
            success = combine_audio_video(audio_file, video_file, final_video)

            if success and final_video.exists():
                logger.info(
                    f"Successfully generated video for {repo_name}: {final_video}"
                )
                return final_video
            else:
                logger.warning(
                    f"Audio/video combination failed for {repo_name}, returning silent video"
                )
                return video_file
        else:
            logger.error(f"Video generation failed for {repo_name}")
            return None

    except Exception as e:
        logger.error(f"Failed to generate video for {repo_name}: {e}")
        return None


def combine_videos(video_files: List[Path], output_file: Path, video_titles: Optional[List[str]] = None) -> bool:
    """Combine multiple videos into one final video and generate timestamp descriptions"""
    logger = setup_pipeline_logging()

    try:
        import subprocess

        # Filter out None values and ensure all files exist
        valid_videos = [v for v in video_files if v and v.exists()]

        if not valid_videos:
            logger.error("No valid video files to combine")
            return False

        if len(valid_videos) == 1:
            # If only one video, just copy it
            import shutil

            shutil.copy2(valid_videos[0], output_file)
            logger.info(f"Single video copied to {output_file}")

            # Generate simple timestamp for single video
            _generate_single_video_timestamps(output_file, valid_videos[0], video_titles)
            return True

        # Get video durations for timestamp generation
        video_durations = []
        for video in valid_videos:
            duration = _get_video_duration(video)
            video_durations.append(duration)

        # Create a text file listing all videos for ffmpeg
        concat_file = output_file.parent / "concat_list.txt"
        with open(concat_file, "w") as f:
            for video in valid_videos:
                f.write(f"file '{video.absolute()}'\n")

        # Use ffmpeg to concatenate videos
        cmd = [
            "ffmpeg",
            "-y",  # -y to overwrite output file
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",  # Copy streams without re-encoding
            str(output_file),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Clean up concat file
        concat_file.unlink(missing_ok=True)

        if result.returncode == 0:
            logger.info(
                f"Successfully combined {len(valid_videos)} videos into {output_file}"
            )

            # Generate timestamp descriptions
            _generate_video_timestamps(output_file, valid_videos, video_durations, video_titles)

            return True
        else:
            logger.error(f"FFmpeg failed to combine videos: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Failed to combine videos: {e}")
        return False


def _get_video_duration(video_path: Path) -> float:
    """Get video duration in seconds using ffprobe"""
    try:
        import subprocess

        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(video_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            duration = float(data["format"]["duration"])
            return duration
        else:
            return 0.0

    except Exception:
        return 0.0


def _format_timestamp(seconds: float) -> str:
    """Format seconds to MM:SS timestamp"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"


def _generate_video_timestamps(output_file: Path, video_files: List[Path], durations: List[float], titles: Optional[List[str]] = None) -> None:
    """Generate timestamp descriptions for combined video"""
    logger = setup_pipeline_logging()

    try:
        timestamp_file = output_file.parent / "timestamps.txt"

        current_time = 0.0
        timestamps = []

        for i, (video_file, duration) in enumerate(zip(video_files, durations)):
            # Extract title from video filename or use provided titles
            if titles and i < len(titles):
                title = titles[i]
            else:
                # Extract meaningful title from filename
                title = _extract_title_from_filename(video_file)

            timestamp_str = _format_timestamp(current_time)
            timestamps.append(f"{timestamp_str} {title}")

            current_time += duration

        # Write timestamps to file
        with open(timestamp_file, "w", encoding="utf-8") as f:
            f.write("视频时间轴:\n\n")
            for timestamp in timestamps:
                f.write(f"{timestamp}\n")

        logger.info(f"Generated video timestamps: {timestamp_file}")

        # Also print to console for immediate visibility
        print(f"\n📝 视频时间轴:")
        for timestamp in timestamps:
            print(f"   {timestamp}")
        print(f"📄 完整时间轴文件: {timestamp_file}")

    except Exception as e:
        logger.error(f"Failed to generate video timestamps: {e}")


def _generate_single_video_timestamps(output_file: Path, video_file: Path, titles: Optional[List[str]] = None) -> None:
    """Generate timestamp for single video"""
    logger = setup_pipeline_logging()

    try:
        timestamp_file = output_file.parent / "timestamps.txt"

        # Extract title from video filename or use provided title
        if titles and len(titles) > 0:
            title = titles[0]
        else:
            title = _extract_title_from_filename(video_file)

        with open(timestamp_file, "w", encoding="utf-8") as f:
            f.write("视频时间轴:\n\n")
            f.write(f"00:00 {title}\n")

        logger.info(f"Generated single video timestamp: {timestamp_file}")

        print(f"\n📝 视频时间轴:")
        print(f"   00:00 {title}")
        print(f"📄 时间轴文件: {timestamp_file}")

    except Exception as e:
        logger.error(f"Failed to generate single video timestamp: {e}")


def _extract_title_from_filename(video_file: Path) -> str:
    """Extract meaningful title from video filename"""
    filename = video_file.stem

    # Handle different naming patterns
    if "summary" in filename.lower():
        return "intro"
    elif "repo_" in filename:
        # Extract repo name from filename like "repo_user_project_final"
        parts = filename.split("_")
        if len(parts) >= 3:
            repo_name = "_".join(parts[1:-1])  # Remove 'repo_' prefix and '_final' suffix
            return repo_name.replace("_", "/")
        else:
            return filename.replace("repo_", "").replace("_", " ")
    else:
        # Clean up filename
        return filename.replace("_", " ").title()


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="AI Video Driver - Generate podcast-style videos from GitHub repositories"
    )

    parser.add_argument(
        "--repo-url", type=str, help="GitHub repository URL to generate content from"
    )

    parser.add_argument(
        "--style",
        type=str,
        choices=["educational", "casual", "technical", "marketing"],
        default="technical",
        help="Podcast style (default: technical)",
    )

    parser.add_argument(
        "--length",
        type=str,
        choices=["short", "medium", "long"],
        default="medium",
        help="Dialogue length (default: medium)",
    )

    parser.add_argument(
        "--github-token",
        type=str,
        help="GitHub API token (can also use GITHUB_TOKEN env var)",
    )

    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        help="Device for TTS model (default: cuda)",
    )

    parser.add_argument(
        "--output-name",
        type=str,
        default="auto_generated",
        help="Output directory name (default: auto_generated)",
    )

    parser.add_argument(
        "--multi-repo",
        action="store_true",
        help="Generate videos from top 5 trending repos and combine them",
    )

    parser.add_argument(
        "--video-only",
        action="store_true",
        help="Generate videos only without combining them",
    )

    return parser.parse_args()


def main():
    """Main pipeline execution with enhanced logging and error handling"""

    # Parse command line arguments
    args = parse_arguments()

    # Setup logging
    logger = setup_pipeline_logging()

    # Get GitHub token from args or environment
    github_token = args.github_token or os.getenv("GITHUB_TOKEN")

    # Configuration
    device = args.device
    logger.info(f"🖥️  Using device: {device}")

    # Handle multi-repo workflow
    if args.multi_repo:
        logger.info("🔄 Starting multi-repository video generation workflow")
        success = generate_multi_repo_content(
            args.style, args.length, device, args.output_name, github_token
        )
        if success:
            logger.info("✅ Multi-repo workflow completed successfully")
        else:
            logger.error("❌ Multi-repo workflow failed")
            sys.exit(1)
        return

    # Generate dialogue content based on arguments
    if args.repo_url:
        logger.info(f"🔗 Generating content from repository: {args.repo_url}")
        text_list = generate_content_from_repo(
            args.repo_url, args.style, args.length, github_token
        )
    else:
        logger.info("📝 Using default FireRedTTS2 content")
        text_list = get_default_dialogue()

    prompt_wav_list = PROMPT_WAV_LIST
    prompt_text_list = PROMPT_TEXT_LIST

    logger.info(f"📝 Dialogue contains {len(text_list)} text segments")
    logger.info(f"🎤 Using {len(prompt_wav_list)} voice prompts")

    try:
        pipeline_start = time.time()

        # Step 1: Initialize FireRedTTS2
        with PipelineTimer("Initialize FireRedTTS2 model", logger):
            fireredtts2 = FireRedTTS2(
                pretrained_dir="./pretrained_models/FireRedTTS2",
                gen_type="dialogue",
                device=device,
            )

        # Step 2: Create output structure
        with PipelineTimer("Create output directory structure", logger):
            output_dir, temp_dir = create_output_structure(args.output_name)

        # Step 3: Generate TTS audio and SRT
        with PipelineTimer("Generate dialogue audio and subtitles", logger):
            all_audio, srt_text = fireredtts2.generate_dialogue(
                text_list=text_list,
                prompt_wav_list=prompt_wav_list,
                prompt_text_list=prompt_text_list,
                temperature=config["audio"].DEFAULT_TEMPERATURE,
                topk=config["audio"].DEFAULT_TOPK,
            )

        # Step 4: Save audio and SRT files
        with PipelineTimer("Save audio and subtitle files", logger):
            audio_file, srt_file = save_files(
                output_dir, all_audio, srt_text, config["audio"].SAMPLE_RATE
            )

        log_file_info(audio_file, logger, "🎵")
        log_file_info(srt_file, logger, "📄")

        # Step 5: Generate video from SRT
        with PipelineTimer("Generate video animation from subtitles", logger):
            video_file = generate_video_from_srt(
                srt_text, audio_file, output_dir, temp_dir
            )

        if video_file and video_file.exists():
            log_file_info(video_file, logger, "🎬")

            # Step 6: Combine audio with video
            with PipelineTimer("Combine audio and video", logger):
                final_video = output_dir / config["files"].FINAL_VIDEO_FILENAME
                success = combine_audio_video(audio_file, video_file, final_video)

            if success and final_video.exists():
                # Pipeline completed successfully
                total_time = time.time() - pipeline_start

                logger.info("=" * 60)
                logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
                logger.info(f"📁 Output directory: {output_dir}")
                log_file_info(final_video, logger, "🎬")
                logger.info(f"⏱️  Total processing time: {total_time:.2f} seconds")
                logger.info("=" * 60)

                # Log all output files
                logger.info("📋 Generated files:")
                for file_path in output_dir.glob("*"):
                    if file_path.is_file():
                        log_file_info(file_path, logger, "   •")

                print(f"\n🎬 Final video: {final_video}")
                print(f"📁 All files: {output_dir}")

            else:
                logger.error("❌ Failed to create final video with audio")
                logger.info(f"🎬 Silent video available: {video_file}")
                print(f"\n⚠️  Audio/video combination failed")
                print(f"🎬 Silent video: {video_file}")
                print(f"📁 Files: {output_dir}")

        else:
            logger.error("❌ Video generation failed completely")
            print(f"\n❌ Video generation failed")
            print(f"📁 Audio and SRT files: {output_dir}")

    except Exception as e:
        logger.error(f"💥 Pipeline failed with error: {e}", exc_info=True)
        print(f"\n💥 Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
