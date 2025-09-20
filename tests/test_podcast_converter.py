"""
Tests for PodcastConverter module.
"""

import unittest
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

    def test_convert_to_podcast(self):
        """Test podcast conversion"""
        repo_content = {
            "name": "DeepResearch",
            "description": "Tongyi DeepResearch - an agentic large language model featuring 30.5 billion total parameters, with only 3.3 billion activated per token. Designed for long-horizon, deep information-seeking tasks.",
            "readme": """# Introduction

We present Tongyi DeepResearch, an agentic large language model featuring 30.5 billion total parameters, with only 3.3 billion activated per token. Developed by Tongyi Lab, the model is specifically designed for long-horizon, deep information-seeking tasks. Tongyi DeepResearch demonstrates state-of-the-art performance across a range of agentic search benchmarks, including Humanity's Last Exam, BrowserComp, BrowserComp-ZH, WebWalkerQA, xbench-DeepSearch, FRAMES and SimpleQA.

## Features

- ⚙️ Fully automated synthetic data generation pipeline: We design a highly scalable data synthesis pipeline, which is fully automatic and empowers agentic pre-training, supervised fine-tuning, and reinforcement learning.
- 🔄 Large-scale continual pre-training on agentic data: Leveraging diverse, high-quality agentic interaction data to extend model capabilities, maintain freshness, and strengthen reasoning performance.
- 🔁 End-to-end reinforcement learning: We employ a strictly on-policy RL approach based on a customized Group Relative Policy Optimization framework, with token-level policy gradients, leave-one-out advantage estimation, and selective filtering of negative samples.
- 🤖 Agent Inference Paradigm Compatibility: At inference, Tongyi DeepResearch is compatible with two inference paradigms: ReAct, for rigorously evaluating the model's core intrinsic abilities, and an IterResearch-based 'Heavy' mode.

## Model Download

The model features 30B-A3B parameters with 128K context length and is available on HuggingFace and ModelScope.

## Quick Start

This guide provides instructions for setting up the environment and running inference scripts:

1. Environment Setup - Recommended Python version: 3.10.0
2. Installation - Install required dependencies with pip install -r requirements.txt
3. Prepare Evaluation Data - Create eval_data/ folder and place QA files in JSONL format
4. Configure the Inference Script - Modify run_react_infer.sh with model path and dataset
5. Run the Inference Script - Execute bash run_react_infer.sh

## Deep Research Agent Family

Tongyi DeepResearch has an extensive deep research agent family including WebWalker, WebDancer, WebSailor, WebShaper, WebWatcher, WebResearcher, ReSum, WebWeaver and more, all designed for advanced web navigation and information seeking tasks.""",
        }

        dialogue = self.converter.convert_to_podcast(repo_content, style="casual")
        print("Generated dialogue:")
        if dialogue:
            for i, line in enumerate(dialogue, 1):
                print(f"{i}: {line}")
        else:
            print("No dialogue generated")

        # Should either get real Claude response or fallback dialogue
        self.assertIsNotNone(dialogue)
        assert dialogue is not None  # Type guard
        self.assertGreater(len(dialogue), 0)
        # All lines should have speaker tags
        self.assertTrue(
            all(line.startswith("[S1]") or line.startswith("[S2]") for line in dialogue)
        )

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

    def test_validate_dialogue_format_valid(self):
        """Test dialogue format validation - valid"""
        dialogue = [
            "[S1]This is a valid dialogue segment.",
            "[S2]This is another valid segment.",
        ]

        is_valid = self.converter.validate_dialogue_format(dialogue)
        self.assertTrue(is_valid)

    def test_validate_dialogue_format_invalid_speaker(self):
        """Test dialogue format validation - invalid speaker"""
        dialogue = ["[S1]This is valid.", "[S3]This has invalid speaker tag."]

        is_valid = self.converter.validate_dialogue_format(dialogue)
        self.assertFalse(is_valid)

    def test_validate_dialogue_format_too_long(self):
        """Test dialogue format validation - too long"""
        long_text = "x" * 350  # Exceeds 300 character limit
        dialogue = [f"[S1]{long_text}"]

        is_valid = self.converter.validate_dialogue_format(dialogue)
        self.assertFalse(is_valid)

    def test_generate_summary_dialogue(self):
        """Test summary dialogue generation from multiple repositories"""
        summary_content = {
            "name": "GitHub Top 5 Trending Repositories Summary",
            "description": "Summary of top 5 trending repositories: DeepResearch, FireRedTTS2, Claude-Code, React-Native, TensorFlow",
            "readme": """Repository: DeepResearch
Key discussion points: [S1]今天我们来聊聊一个很厉害的AI model叫DeepResearch。 [S2]听起来很有意思，这个model有什么特别的地方呢？ [S1]这个model有30.5 billion parameters，但是每个token只activate 3.3 billion，专门designed for long-horizon information-seeking tasks。

Repository: FireRedTTS2
Key discussion points: [S1]接下来我们聊聊FireRedTTS2，这是一个很powerful的TTS system。 [S2]TTS是什么意思啊？ [S1]TTS就是Text-to-Speech，FireRedTTS2可以generate multi-speaker dialogue，而且support超过3分钟的conversational speech。

Repository: Claude-Code
Key discussion points: [S1]然后我们来看看Claude-Code，这是Anthropic推出的coding assistant。 [S2]这个跟其他的coding tools有什么不同吗？ [S1]Claude-Code integrated了很多advanced features，可以help developers write better code with AI assistance。""",
        }

        dialogue = self.converter._generate_summary_dialogue(summary_content)
        print("Generated summary dialogue:")
        if dialogue:
            for i, line in enumerate(dialogue, 1):
                print(f"{i}: {line}")
        else:
            print("No summary dialogue generated")

        # Should either get real AI response or None (if API fails)
        if dialogue is not None:
            self.assertGreater(len(dialogue), 0)
            # All lines should have speaker tags
            self.assertTrue(
                all(
                    line.startswith("[S1]") or line.startswith("[S2]")
                    for line in dialogue
                )
            )
            # Should validate format
            self.assertTrue(self.converter.validate_dialogue_format(dialogue))
            # Should be reasonably sized for an introduction
            self.assertGreaterEqual(len(dialogue), 4)  # At least 4 segments
            self.assertLessEqual(len(dialogue), 15)  # Not too many for intro


if __name__ == "__main__":
    unittest.main(verbosity=2)
