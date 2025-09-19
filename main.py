"""
Enhanced FireRedTTS2 main script with modular video generation pipeline.

This script generates conversational speech using FireRedTTS2, creates synchronized
video animations with Manim, and combines everything into a final video output.
"""

import sys
import time
import argparse
import os
from typing import Optional
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


def generate_content_from_repo(repo_url: str, style: str, length: str, github_token: Optional[str] = None) -> list:
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
        dialogue = converter.convert_to_podcast(repo_content, style=style, length=length)

        if dialogue and converter.validate_dialogue_format(dialogue):
            logger.info(f"Successfully generated {len(dialogue)} dialogue segments")
            return dialogue
        else:
            logger.warning("Generated dialogue failed validation, using fallback")
            return converter.get_fallback_dialogue(repo_content)

    except Exception as e:
        logger.error(f"Failed to generate content from repository: {e}")
        return get_default_dialogue()


def generate_trending_content(language: str, style: str, length: str, github_token: Optional[str] = None) -> list:
    """Generate dialogue content from trending repositories"""
    logger = setup_pipeline_logging()

    try:
        # Initialize content fetcher
        fetcher = GitHubContentFetcher(github_token=github_token)

        # Get trending repositories
        logger.info(f"Fetching trending {language} repositories")
        trending_repos = fetcher.get_trending_repos(language=language, limit=1)

        if not trending_repos:
            logger.error("No trending repositories found")
            return get_default_dialogue()

        # Use the first trending repo
        repo = trending_repos[0]
        repo_url = repo.get("html_url")

        if not repo_url:
            logger.error("No valid repository URL found")
            return get_default_dialogue()

        logger.info(f"Selected trending repo: {repo.get('full_name', 'Unknown')}")
        return generate_content_from_repo(repo_url, style, length, github_token)

    except Exception as e:
        logger.error(f"Failed to generate content from trending repos: {e}")
        return get_default_dialogue()


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="AI Video Driver - Generate podcast-style videos from GitHub repositories"
    )

    parser.add_argument(
        "--repo-url",
        type=str,
        help="GitHub repository URL to generate content from"
    )

    parser.add_argument(
        "--trending",
        action="store_true",
        help="Use trending repositories instead of specific URL"
    )

    parser.add_argument(
        "--language",
        type=str,
        default="python",
        help="Programming language for trending repos (default: python)"
    )

    parser.add_argument(
        "--style",
        type=str,
        choices=["educational", "casual", "technical", "marketing"],
        default="educational",
        help="Podcast style (default: educational)"
    )

    parser.add_argument(
        "--length",
        type=str,
        choices=["short", "medium", "long"],
        default="medium",
        help="Dialogue length (default: medium)"
    )

    parser.add_argument(
        "--github-token",
        type=str,
        help="GitHub API token (can also use GITHUB_TOKEN env var)"
    )

    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        help="Device for TTS model (default: cuda)"
    )

    parser.add_argument(
        "--output-name",
        type=str,
        default="auto_generated",
        help="Output directory name (default: auto_generated)"
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

    # Generate dialogue content based on arguments
    if args.repo_url:
        logger.info(f"🔗 Generating content from repository: {args.repo_url}")
        text_list = generate_content_from_repo(
            args.repo_url, args.style, args.length, github_token
        )
    elif args.trending:
        logger.info(f"📈 Generating content from trending {args.language} repositories")
        text_list = generate_trending_content(
            args.language, args.style, args.length, github_token
        )
    else:
        logger.info("📝 Using default FireRedTTS2 content")
        text_list = get_default_dialogue()

    prompt_wav_list = [
        "examples/chat_prompt/zh/S1.flac",
        "examples/chat_prompt/zh/S2.flac",
    ]

    prompt_text_list = [
        "[S1]啊，可能说更适合美国市场应该是什么样子。那这这个可能说当然如果说有有机会能亲身的去考察去了解一下，那当然是有更好的帮助。",
        "[S2]比如具体一点的，他觉得最大的一个跟他预想的不一样的是在什么地方。",
    ]

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
