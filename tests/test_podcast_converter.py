"""
Tests for PodcastConverter module.
"""

import unittest
from unittest.mock import Mock, patch
import subprocess
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_video_driver.podcast_converter import PodcastConverter


class TestPodcastConverter(unittest.TestCase):
    """Test cases for PodcastConverter"""

    def setUp(self):
        """Set up test environment"""
        self.converter = PodcastConverter()

    @patch('subprocess.run')
    def test_check_claude_availability_success(self, mock_run):
        """Test Claude CLI availability check - success"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Claude Code CLI v1.0.0"
        mock_run.return_value = mock_result

        available = self.converter.check_claude_availability()

        self.assertTrue(available)
        mock_run.assert_called_once_with(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

    @patch('subprocess.run')
    def test_check_claude_availability_failure(self, mock_run):
        """Test Claude CLI availability check - failure"""
        mock_run.side_effect = FileNotFoundError("Command not found")

        available = self.converter.check_claude_availability()

        self.assertFalse(available)

    @patch('subprocess.run')
    def test_convert_to_podcast_success(self, mock_run):
        """Test successful podcast conversion"""
        # Mock Claude CLI availability check
        availability_result = Mock()
        availability_result.returncode = 0
        availability_result.stdout = "Claude Code CLI v1.0.0"

        # Mock conversion result
        conversion_result = Mock()
        conversion_result.returncode = 0
        conversion_result.stdout = """[S1]Today I want to talk about this amazing repository.
[S2]Oh interesting! What does it do exactly?
[S1]It's a Python library for data processing.
[S2]That sounds really useful! How does it work?"""

        mock_run.side_effect = [availability_result, conversion_result]

        repo_content = {
            "name": "test-repo",
            "description": "A Python data processing library",
            "readme": "# Test Repo\n\nThis is a test repository."
        }

        dialogue = self.converter.convert_to_podcast(repo_content)

        self.assertIsNotNone(dialogue)
        assert dialogue is not None  # Type guard
        self.assertEqual(len(dialogue), 4)
        self.assertTrue(dialogue[0].startswith("[S1]"))
        self.assertTrue(dialogue[1].startswith("[S2]"))

    @patch('subprocess.run')
    def test_convert_to_podcast_claude_unavailable(self, mock_run):
        """Test podcast conversion when Claude CLI is unavailable"""
        mock_run.side_effect = FileNotFoundError("Command not found")

        repo_content = {"name": "test-repo"}
        dialogue = self.converter.convert_to_podcast(repo_content)

        self.assertIsNone(dialogue)

    @patch('subprocess.run')
    def test_convert_to_podcast_timeout(self, mock_run):
        """Test podcast conversion timeout"""
        # Mock Claude CLI availability check
        availability_result = Mock()
        availability_result.returncode = 0
        availability_result.stdout = "Claude Code CLI v1.0.0"

        mock_run.side_effect = [availability_result, subprocess.TimeoutExpired("claude", 120)]

        repo_content = {"name": "test-repo"}
        dialogue = self.converter.convert_to_podcast(repo_content)

        self.assertIsNone(dialogue)

    def test_parse_dialogue_response_valid(self):
        """Test parsing valid dialogue response"""
        response = """[S1]Hello, this is speaker one.
[S2]Hi there, this is speaker two.
[S1]Great to meet you!"""

        dialogue = self.converter._parse_dialogue_response(response)

        self.assertIsNotNone(dialogue)
        assert dialogue is not None  # Type guard
        self.assertEqual(len(dialogue), 3)
        self.assertEqual(dialogue[0], "[S1]Hello, this is speaker one.")
        self.assertEqual(dialogue[1], "[S2]Hi there, this is speaker two.")

    def test_parse_dialogue_response_mixed_format(self):
        """Test parsing dialogue with mixed format"""
        response = """[S1]Hello, this is speaker one.
This is a response without speaker tag.
[S2]Hi there, this is speaker two."""

        dialogue = self.converter._parse_dialogue_response(response)

        self.assertIsNotNone(dialogue)
        assert dialogue is not None  # Type guard
        self.assertEqual(len(dialogue), 3)
        self.assertTrue(dialogue[1].startswith("[S2]"))  # Should alternate speakers

    def test_parse_dialogue_response_insufficient(self):
        """Test parsing insufficient dialogue"""
        response = "[S1]Only one line"

        dialogue = self.converter._parse_dialogue_response(response)

        self.assertIsNone(dialogue)

    def test_create_conversion_prompt(self):
        """Test conversion prompt creation"""
        repo_content = {
            "name": "test-repo",
            "description": "A test repository",
            "readme": "# Test Repo\n\nThis is a test."
        }

        prompt = self.converter._create_conversion_prompt(repo_content, "educational", "medium")

        self.assertIn("test-repo", prompt)
        self.assertIn("A test repository", prompt)
        self.assertIn("educational", prompt)
        self.assertIn("Generate 5-7 dialogue exchanges", prompt)

    def test_get_fallback_dialogue(self):
        """Test fallback dialogue generation"""
        repo_content = {
            "name": "awesome-project",
            "description": "An awesome software project",
            "language": "Python"
        }

        dialogue = self.converter.get_fallback_dialogue(repo_content)

        self.assertIsInstance(dialogue, list)
        self.assertGreater(len(dialogue), 0)
        self.assertTrue(any("awesome-project" in line for line in dialogue))

    def test_validate_dialogue_format_valid(self):
        """Test dialogue format validation - valid"""
        dialogue = [
            "[S1]This is a valid dialogue segment.",
            "[S2]This is another valid segment."
        ]

        is_valid = self.converter.validate_dialogue_format(dialogue)
        self.assertTrue(is_valid)

    def test_validate_dialogue_format_invalid_speaker(self):
        """Test dialogue format validation - invalid speaker"""
        dialogue = [
            "[S1]This is valid.",
            "[S3]This has invalid speaker tag."
        ]

        is_valid = self.converter.validate_dialogue_format(dialogue)
        self.assertFalse(is_valid)

    def test_validate_dialogue_format_too_long(self):
        """Test dialogue format validation - too long"""
        long_text = "x" * 350  # Exceeds 300 character limit
        dialogue = [f"[S1]{long_text}"]

        is_valid = self.converter.validate_dialogue_format(dialogue)
        self.assertFalse(is_valid)


if __name__ == "__main__":
    unittest.main(verbosity=2)