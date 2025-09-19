"""
GitHub repository content fetcher for dynamic podcast generation.
"""

import requests
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import json

logger = logging.getLogger(__name__)


class GitHubContentFetcher:
    """Fetches content from GitHub repositories for podcast generation"""

    def __init__(self, github_token: Optional[str] = None, cache_dir: Optional[Path] = None):
        self.github_token = github_token
        self.cache_dir = cache_dir or Path.home() / ".cache" / "ai_video_driver"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Video-Driver/1.0"
        }

        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"

        logger.info(f"Initialized GitHub fetcher with cache dir: {self.cache_dir}")

    def get_trending_repos(self, language: str = "python", limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch trending repositories from GitHub"""
        logger.info(f"Fetching trending {language} repositories")

        cache_file = self.cache_dir / f"trending_{language}_{limit}.json"

        # Check cache (1 hour expiry)
        if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < 3600:
            logger.debug("Using cached trending repositories")
            with open(cache_file, 'r') as f:
                return json.load(f)

        try:
            # Search for trending repos (created in last week, sorted by stars)
            url = "https://api.github.com/search/repositories"
            params = {
                "q": f"language:{language} created:>{self._get_week_ago_date()}",
                "sort": "stars",
                "order": "desc",
                "per_page": limit
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()

            repos = response.json().get("items", [])

            # Cache the results
            with open(cache_file, 'w') as f:
                json.dump(repos, f, indent=2)

            logger.info(f"Fetched {len(repos)} trending repositories")
            return repos

        except Exception as e:
            logger.error(f"Failed to fetch trending repositories: {e}")
            return []

    def fetch_repository_content(self, repo_url: str) -> Optional[Dict[str, str]]:
        """Fetch README and basic info from a GitHub repository"""
        logger.info(f"Fetching content from repository: {repo_url}")

        try:
            # Parse repository URL
            parsed = urlparse(repo_url)
            if "github.com" not in parsed.netloc:
                raise ValueError("Not a GitHub URL")

            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 2:
                raise ValueError("Invalid GitHub repository URL format")

            owner, repo = path_parts[0], path_parts[1]

            # Check cache (1 hour expiry)
            cache_file = self.cache_dir / f"{owner}_{repo}_content.json"
            if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < 3600:
                logger.debug("Using cached repository content")
                with open(cache_file, 'r') as f:
                    return json.load(f)

            # Fetch repository info
            repo_info = self._fetch_repo_info(owner, repo)
            if not repo_info:
                return None

            # Fetch README content
            readme_content = self._fetch_readme(owner, repo)

            content = {
                "name": repo_info.get("name", ""),
                "description": repo_info.get("description", ""),
                "stars": repo_info.get("stargazers_count", 0),
                "language": repo_info.get("language", ""),
                "topics": repo_info.get("topics", []),
                "readme": readme_content or "",
                "url": repo_url,
                "owner": owner,
                "repo": repo
            }

            # Cache the results
            with open(cache_file, 'w') as f:
                json.dump(content, f, indent=2)

            logger.info(f"Successfully fetched content for {owner}/{repo}")
            return content

        except Exception as e:
            logger.error(f"Failed to fetch repository content: {e}")
            return None

    def _fetch_repo_info(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Fetch basic repository information"""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch repo info for {owner}/{repo}: {e}")
            return None

    def _fetch_readme(self, owner: str, repo: str) -> Optional[str]:
        """Fetch README content from repository"""
        try:
            # Try common README filenames
            readme_files = ["README.md", "readme.md", "README.rst", "readme.rst", "README.txt", "readme.txt"]

            for readme_file in readme_files:
                try:
                    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{readme_file}"
                    response = requests.get(url, headers=self.headers, timeout=30)

                    if response.status_code == 200:
                        content_data = response.json()
                        if content_data.get("encoding") == "base64":
                            import base64
                            content = base64.b64decode(content_data["content"]).decode('utf-8')
                            logger.debug(f"Successfully fetched {readme_file}")
                            return content

                except Exception:
                    continue

            logger.warning(f"No README found for {owner}/{repo}")
            return None

        except Exception as e:
            logger.error(f"Failed to fetch README for {owner}/{repo}: {e}")
            return None

    def _get_week_ago_date(self) -> str:
        """Get date string for one week ago"""
        import datetime
        week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        return week_ago.strftime("%Y-%m-%d")

    def get_repository_summary(self, content: Dict[str, str]) -> str:
        """Generate a summary of repository content for podcast conversion"""
        summary_parts = []

        if content.get("name"):
            summary_parts.append(f"Repository: {content['name']}")

        if content.get("description"):
            summary_parts.append(f"Description: {content['description']}")

        if content.get("language"):
            summary_parts.append(f"Primary Language: {content['language']}")

        if content.get("stars"):
            summary_parts.append(f"GitHub Stars: {content['stars']}")

        if content.get("topics"):
            summary_parts.append(f"Topics: {', '.join(content['topics'])}")

        if content.get("readme"):
            # Truncate README to reasonable length for conversion
            readme = content["readme"]
            if len(readme) > 5000:
                readme = readme[:5000] + "..."
            summary_parts.append(f"README Content:\n{readme}")

        return "\n\n".join(summary_parts)