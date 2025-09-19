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

    def test_get_top5_unrecorded_trending_repos_success(self):
        """Test successful top 5 unrecorded trending repositories fetch"""
        repos = self.fetcher.get_top5_unrecorded_trending_repos()

        print(f"\nFetched {len(repos)} unrecorded trending repositories:")
        for i, repo in enumerate(repos):
            print(
                f"  {i+1}. {repo.get('full_name', 'Unknown')} - {repo.get('stargazers_count', 0)} stars"
            )

        self.assertIsInstance(repos, list)
        self.assertLessEqual(len(repos), 5)  # Should return at most 5 repos

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

    def test_recorded_repos_tracking(self):
        """Test recorded repositories tracking functionality"""
        repo_id = "test/repo"

        # Initially should not be recorded
        self.assertFalse(self.fetcher._is_repo_recently_recorded(repo_id))

        # Mark as recorded
        self.fetcher.mark_repo_as_recorded(repo_id)

        # Now should be recorded
        self.assertTrue(self.fetcher._is_repo_recently_recorded(repo_id))

        # Test with custom threshold
        self.assertTrue(self.fetcher._is_repo_recently_recorded(repo_id, days_threshold=1))

        # For threshold=0, it should still return True since it was recorded today (day 0)
        # A better test is to use a negative threshold or test edge cases differently
        self.assertTrue(self.fetcher._is_repo_recently_recorded(repo_id, days_threshold=0))

    def test_recorded_repos_persistence(self):
        """Test that recorded repositories persist across instances"""
        repo_id = "test/persistent-repo"

        # Mark as recorded in first instance
        self.fetcher.mark_repo_as_recorded(repo_id)

        # Create new fetcher instance with same cache dir
        new_fetcher = GitHubContentFetcher(cache_dir=self.temp_dir)

        # Should still be marked as recorded
        self.assertTrue(new_fetcher._is_repo_recently_recorded(repo_id))

    def test_skip_recently_recorded_repos(self):
        """Test that recently recorded repos are skipped in trending fetch"""
        # Get initial trending repos
        initial_repos = self.fetcher.get_top5_unrecorded_trending_repos()

        if initial_repos:
            # Mark the first repo as recorded
            first_repo_id = initial_repos[0]["full_name"]
            self.fetcher.mark_repo_as_recorded(first_repo_id)

            # Fetch again - should skip the recorded repo
            new_repos = self.fetcher.get_top5_unrecorded_trending_repos()

            # The previously recorded repo should not be in new results
            new_repo_ids = [repo["full_name"] for repo in new_repos]
            self.assertNotIn(first_repo_id, new_repo_ids)

    def test_recorded_repos_file_creation(self):
        """Test that recorded repos file is created properly"""
        repo_id = "test/file-creation"

        # File should not exist initially
        self.assertFalse(self.fetcher.recorded_repos_file.exists())

        # Mark a repo as recorded
        self.fetcher.mark_repo_as_recorded(repo_id)

        # File should now exist
        self.assertTrue(self.fetcher.recorded_repos_file.exists())

        # Verify file content
        with open(self.fetcher.recorded_repos_file, 'r') as f:
            data = json.load(f)

        self.assertIn(repo_id, data)
        # Verify timestamp format
        import datetime
        timestamp = datetime.datetime.fromisoformat(data[repo_id])
        self.assertIsInstance(timestamp, datetime.datetime)


if __name__ == "__main__":
    unittest.main(verbosity=2)
