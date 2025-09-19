"""
Tests for GitHubContentFetcher module.
"""

import unittest
import tempfile
import json
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_video_driver.content_fetcher import GitHubContentFetcher


class TestGitHubContentFetcher(unittest.TestCase):
    """Test cases for GitHubContentFetcher"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.fetcher = GitHubContentFetcher(cache_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_trending_repos_success(self):
        """Test successful trending repositories fetch with real API"""
        repos = self.fetcher.get_trending_repos(language="python", limit=5)

        print(f"\nFetched {len(repos)} repositories:")
        for i, repo in enumerate(repos):
            print(
                f"  {i+1}. {repo.get('full_name', 'Unknown')} - {repo.get('stargazers_count', 0)} stars"
            )

        self.assertIsInstance(repos, list)
        if repos:  # Only test if we got results
            repo = repos[0]
            self.assertIn("name", repo)
            self.assertIn("full_name", repo)
            self.assertIn("html_url", repo)
            self.assertIn("stargazers_count", repo)
            self.assertTrue(repo["html_url"].startswith("https://github.com/"))

    def test_fetch_repository_content_success(self):
        """Test successful repository content fetch with real repo"""
        # Use a well-known public repository
        content = self.fetcher.fetch_repository_content(
            "https://github.com/OpenBMB/VoxCPM"
        )

        if content:  # Only test if fetch was successful
            print(f"\nFetched repository content:")
            print(f"  Name: {content.get('name', 'Unknown')}")
            print(f"  Description: {content.get('description', 'No description')}")
            print(f"  Language: {content.get('language', 'Unknown')}")
            print(f"  Stars: {content.get('stars', 0)}")
            print(f"  Topics: {content.get('topics', [])}")
            print(f"  README preview: {content.get('readme', 'No README')[:100]}...")

            self.assertIsInstance(content, dict)
            self.assertIn("name", content)
            self.assertIn("description", content)

    def test_get_repository_summary(self):
        """Test repository summary generation"""
        content = {
            "name": "test-repo",
            "description": "A test repository",
            "language": "Python",
            "stars": 100,
            "topics": ["test", "python"],
            "readme": "# Test Repository\n\nThis is a test.",
        }

        summary = self.fetcher.get_repository_summary(content)

        self.assertIn("test-repo", summary)
        self.assertIn("A test repository", summary)
        self.assertIn("Python", summary)
        self.assertIn("100", summary)
        self.assertIn("test, python", summary)
        self.assertIn("# Test Repository", summary)

    def test_cache_functionality(self):
        """Test caching mechanism"""
        # Create a mock cache file
        cache_file = self.temp_dir / "trending_python_10.json"
        test_data = [{"name": "cached-repo"}]

        with open(cache_file, "w") as f:
            json.dump(test_data, f)

        # This should return cached data
        repos = self.fetcher.get_trending_repos()
        self.assertEqual(repos[0]["name"], "cached-repo")


if __name__ == "__main__":
    unittest.main(verbosity=2)
