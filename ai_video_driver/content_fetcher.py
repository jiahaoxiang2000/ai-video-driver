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
import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class GitHubContentFetcher:
    """Fetches content from GitHub repositories for podcast generation"""

    def __init__(
        self, github_token: Optional[str] = None, cache_dir: Optional[Path] = None
    ):
        self.github_token = github_token
        self.cache_dir = cache_dir or Path.home() / ".cache" / "ai_video_driver"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Track recorded repositories
        self.recorded_repos_file = self.cache_dir / "recorded_repos.json"

        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Video-Driver/1.0",
        }

        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"

        logger.info(f"Initialized GitHub fetcher with cache dir: {self.cache_dir}")

    def _load_recorded_repos(self) -> Dict[str, datetime.datetime]:
        """Load previously recorded repositories with their timestamps"""
        if not self.recorded_repos_file.exists():
            return {}

        try:
            with open(self.recorded_repos_file, "r") as f:
                data = json.load(f)

            # Convert string timestamps back to datetime objects
            recorded_repos = {}
            for repo_id, timestamp_str in data.items():
                recorded_repos[repo_id] = datetime.datetime.fromisoformat(timestamp_str)

            return recorded_repos
        except Exception as e:
            logger.error(f"Failed to load recorded repos: {e}")
            return {}

    def _save_recorded_repos(self, recorded_repos: Dict[str, datetime.datetime]):
        """Save recorded repositories with timestamps"""
        try:
            # Convert datetime objects to strings for JSON serialization
            data = {}
            for repo_id, timestamp in recorded_repos.items():
                data[repo_id] = timestamp.isoformat()

            with open(self.recorded_repos_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save recorded repos: {e}")

    def mark_repo_as_recorded(self, repo_id: str):
        """Mark a repository as recorded with current timestamp"""
        recorded_repos = self._load_recorded_repos()
        recorded_repos[repo_id] = datetime.datetime.now()
        self._save_recorded_repos(recorded_repos)
        logger.info(f"Marked {repo_id} as recorded")

    def _is_repo_recently_recorded(self, repo_id: str, days_threshold: int = 7) -> bool:
        """Check if a repository was recorded within the threshold period"""
        recorded_repos = self._load_recorded_repos()

        if repo_id not in recorded_repos:
            return False

        recorded_time = recorded_repos[repo_id]
        time_diff = datetime.datetime.now() - recorded_time

        return time_diff.days <= days_threshold

    def get_top5_unrecorded_trending_repos(self) -> List[Dict[str, Any]]:
        """Fetch top 5 trending repositories from GitHub trending page, skipping recently recorded ones"""
        logger.info(
            "Fetching top 5 unrecorded trending repositories from GitHub trending page"
        )

        try:
            # Fetch GitHub trending page
            trending_url = "https://github.com/trending"
            headers = {
                "User-Agent": "AI-Video-Driver/1.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }

            response = requests.get(trending_url, headers=headers, timeout=30)
            response.raise_for_status()

            # Parse the HTML content
            soup = BeautifulSoup(response.content, "html.parser")

            # Find trending repositories
            trending_repos = []
            repo_articles = soup.find_all("article", {"class": "Box-row"})

            for article in repo_articles:
                try:
                    # Extract repository name and owner
                    h2_elem = article.find("h2", {"class": "h3"})
                    if not h2_elem:
                        continue

                    repo_link = h2_elem.find("a")
                    if not repo_link:
                        continue

                    repo_path = repo_link.get("href", "")
                    if repo_path:
                        repo_path = repo_path.strip("/")

                    repo_parts = repo_path.split("/")
                    if len(repo_parts) != 2:
                        continue

                    owner, repo_name = repo_parts
                    repo_id = f"{owner}/{repo_name}"

                    # Skip if recently recorded
                    if self._is_repo_recently_recorded(repo_id):
                        logger.debug(f"Skipping recently recorded repo: {repo_id}")
                        continue

                    # Extract additional info
                    description_elem = article.find("p", {"class": "col-9"})
                    description = (
                        description_elem.get_text(strip=True)
                        if description_elem
                        else ""
                    )

                    # Extract language
                    language_elem = article.find(
                        "span", attrs={"itemprop": "programmingLanguage"}
                    )
                    language = (
                        language_elem.get_text(strip=True) if language_elem else ""
                    )

                    # Extract stars count
                    stars_elem = article.find(
                        "a", attrs={"href": f"/{repo_id}/stargazers"}
                    )
                    stars = 0
                    if stars_elem:
                        stars_text = stars_elem.get_text(strip=True).replace(",", "")
                        try:
                            stars = int(stars_text)
                        except (ValueError, TypeError):
                            stars = 0

                    repo_info = {
                        "name": repo_name,
                        "full_name": repo_id,
                        "owner": {"login": owner},
                        "description": description,
                        "language": language,
                        "stargazers_count": stars,
                        "html_url": f"https://github.com/{repo_id}",
                        "topics": [],  # GitHub trending page doesn't show topics
                    }

                    trending_repos.append(repo_info)

                    # Stop when we have 5 unrecorded repos
                    if len(trending_repos) >= 5:
                        break

                except Exception as e:
                    logger.warning(
                        f"Failed to parse repository from trending page: {e}"
                    )
                    continue

            logger.info(f"Found {len(trending_repos)} unrecorded trending repositories")
            return trending_repos

        except Exception as e:
            logger.error(f"Failed to fetch trending repositories from GitHub page: {e}")
            return []

    def fetch_repository_content(self, repo_url: str) -> Optional[Dict[str, str]]:
        """Fetch README and basic info from a GitHub repository"""
        logger.info(f"Fetching content from repository: {repo_url}")

        try:
            # Parse repository URL
            parsed = urlparse(repo_url)
            if "github.com" not in parsed.netloc:
                raise ValueError("Not a GitHub URL")

            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) < 2:
                raise ValueError("Invalid GitHub repository URL format")

            owner, repo = path_parts[0], path_parts[1]

            # Check cache (1 hour expiry)
            cache_file = self.cache_dir / f"{owner}_{repo}_content.json"
            if (
                cache_file.exists()
                and (time.time() - cache_file.stat().st_mtime) < 3600
            ):
                logger.debug("Using cached repository content")
                with open(cache_file, "r") as f:
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
                "repo": repo,
            }

            # Cache the results
            with open(cache_file, "w") as f:
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
            readme_files = [
                "README.md",
                "readme.md",
                "README.rst",
                "readme.rst",
                "README.txt",
                "readme.txt",
            ]

            for readme_file in readme_files:
                try:
                    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{readme_file}"
                    response = requests.get(url, headers=self.headers, timeout=30)

                    if response.status_code == 200:
                        content_data = response.json()
                        if content_data.get("encoding") == "base64":
                            import base64

                            content = base64.b64decode(content_data["content"]).decode(
                                "utf-8"
                            )
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
