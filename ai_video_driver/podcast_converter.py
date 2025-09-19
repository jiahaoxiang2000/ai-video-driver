"""
Claude Code CLI integration for converting repository content to podcast format.
"""

import subprocess
import logging
import re
from typing import List, Optional, Dict
import textwrap

logger = logging.getLogger(__name__)


class PodcastConverter:
    """Converts repository content to podcast dialogue using Claude Code CLI"""

    def __init__(self):
        self.claude_cmd = "claude"
        logger.info("Initialized Podcast Converter with Claude Code CLI")

    def check_claude_availability(self) -> bool:
        """Check if Claude Code CLI is available"""
        try:
            result = subprocess.run(
                [self.claude_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                logger.info(f"Claude Code CLI available: {result.stdout.strip()}")
                return True
            else:
                logger.error("Claude Code CLI not found or not working")
                return False
        except Exception as e:
            logger.error(f"Failed to check Claude availability: {e}")
            return False

    def convert_to_podcast(
        self,
        repo_content: Dict[str, str],
        style: str = "technical",
        length: str = "medium",
    ) -> Optional[List[str]]:
        """Convert repository content to podcast dialogue format"""
        logger.info(
            f"Converting repository content to podcast format (style: {style}, length: {length})"
        )

        if not self.check_claude_availability():
            logger.error("Claude Code CLI not available, cannot convert content")
            return None

        try:
            # Create conversion prompt
            prompt = self._create_conversion_prompt(repo_content, style, length)

            # Use Claude Code CLI with -p flag for non-interactive output
            result = subprocess.run(
                [self.claude_cmd, "-p", prompt],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutes timeout
            )

            if result.returncode == 0:
                # Parse the Claude response to extract dialogue
                dialogue = self._parse_dialogue_response(result.stdout)
                if dialogue:
                    logger.info(
                        f"Successfully converted content to {len(dialogue)} dialogue segments"
                    )
                    return dialogue
                else:
                    logger.error("Failed to parse dialogue from Claude response")
                    return None
            else:
                logger.error(f"Claude CLI failed with error: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("Claude CLI conversion timed out")
            return None
        except Exception as e:
            logger.error(f"Failed to convert content to podcast: {e}")
            return None

    def _create_conversion_prompt(
        self, repo_content: Dict[str, str], style: str, length: str
    ) -> str:
        """Create the conversion prompt for Claude"""

        length_instructions = {
            "short": "Generate 3-4 dialogue exchanges (6-8 total segments)",
            "medium": "Generate 5-7 dialogue exchanges (10-14 total segments)",
            "long": "Generate 8-12 dialogue exchanges (16-24 total segments)",
        }

        style_instructions = {
            "educational": "Focus on explaining concepts, features, and benefits in an informative way",
            "casual": "Use conversational tone, personal opinions, and casual language",
            "technical": "Include technical details, implementation specifics, and developer insights",
            "marketing": "Emphasize benefits, use cases, and why people should use this project",
        }

        repo_name = repo_content.get("name", "Unknown Repository")
        repo_description = repo_content.get("description", "")
        readme_content = repo_content.get("readme", "")[:5000]  # Limit for prompt size

        prompt = f"""Convert this GitHub repository information into a natural podcast-style conversation between two speakers S1 and S2.

Repository: {repo_name}
Description: {repo_description}

README Content:
{readme_content}

Instructions:
- {length_instructions.get(length, length_instructions["medium"])}
- Style: {style} - {style_instructions.get(style, style_instructions["educational"])}
- Format each speaker line as: [S1]Text here or [S2]Text here
- Use natural Chinese mixed with English technical terms
- S1 should be knowledgeable and explain features with specific details
- S2 should ask follow-up questions and show interest
- Keep technical terms, numbers, and project names in English
- Include specific technical details and metrics when available
- Keep each segment under 200 characters for TTS performance
- Make it sound like a tech discussion between friends

Output only the dialogue lines in the specified format, one per line. Do not include any other text or explanations.

Example style:
[S1]....
[S2]....
[S1]...

Now generate the full conversation:"""

        return prompt

    def _parse_dialogue_response(self, response: str) -> Optional[List[str]]:
        """Parse Claude's response to extract dialogue segments"""
        try:
            lines = response.strip().split("\n")
            dialogue_segments = []

            for line in lines:
                line = line.strip()
                # Look for lines that start with [S1] or [S2]
                if re.match(r"^\[S[12]\]", line):
                    dialogue_segments.append(line)
                elif line and not line.startswith("#") and not line.startswith("*"):
                    # Sometimes Claude might not include the speaker tags, try to add them
                    if dialogue_segments:
                        # Alternate between S1 and S2
                        last_speaker = (
                            "S1" if dialogue_segments[-1].startswith("[S1]") else "S2"
                        )
                        next_speaker = "S2" if last_speaker == "S1" else "S1"
                        dialogue_segments.append(f"[{next_speaker}]{line}")
                    else:
                        # Start with S1
                        dialogue_segments.append(f"[S1]{line}")

            # Validate that we have proper dialogue
            if len(dialogue_segments) >= 2:
                logger.debug(f"Parsed {len(dialogue_segments)} dialogue segments")
                return dialogue_segments
            else:
                logger.warning("Not enough dialogue segments found in response")
                return None

        except Exception as e:
            logger.error(f"Failed to parse dialogue response: {e}")
            return None

    def validate_dialogue_format(self, dialogue: List[str]) -> bool:
        """Validate that dialogue is in correct format for TTS"""
        try:
            for segment in dialogue:
                if not re.match(r"^\[S[12]\]", segment):
                    logger.warning(f"Invalid dialogue format: {segment}")
                    return False

                # Check length (should be reasonable for TTS)
                text_content = re.sub(r"^\[S[12]\]", "", segment).strip()
                if len(text_content) > 300:
                    logger.warning(
                        f"Dialogue segment too long: {len(text_content)} chars"
                    )
                    return False

            return True

        except Exception as e:
            logger.error(f"Failed to validate dialogue format: {e}")
            return False
