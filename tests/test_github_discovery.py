"""Tests for GitHub discovery service."""

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_skills.services.github_discovery import GitHubDiscovery, GitHubRepo


@pytest.fixture
def discovery_service(tmp_path: Path) -> GitHubDiscovery:
    """Create GitHubDiscovery instance with temp cache dir."""
    return GitHubDiscovery(cache_dir=tmp_path / "cache")


@pytest.fixture
def mock_api_response() -> dict:
    """Mock GitHub API search response."""
    return {
        "total_count": 1,
        "items": [
            {
                "full_name": "test/repo",
                "clone_url": "https://github.com/test/repo.git",
                "description": "Test repository",
                "stargazers_count": 10,
                "forks_count": 2,
                "updated_at": "2025-11-20T10:00:00Z",
                "license": {"spdx_id": "MIT"},
                "topics": ["claude-skills", "python"],
            }
        ],
    }


class TestGitHubDiscovery:
    """Test GitHub discovery service."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test service initialization."""
        cache_dir = tmp_path / "test_cache"
        discovery = GitHubDiscovery(
            github_token="test_token",
            cache_dir=cache_dir,
        )

        assert discovery.github_token == "test_token"
        assert discovery.cache_dir == cache_dir
        assert cache_dir.exists()  # Should create cache directory

    def test_initialization_default_cache_dir(self) -> None:
        """Test service initialization with default cache dir."""
        discovery = GitHubDiscovery()

        expected_cache_dir = Path.home() / ".mcp-skillset" / "cache"
        assert discovery.cache_dir == expected_cache_dir

    @patch("mcp_skills.services.github_discovery.request.urlopen")
    def test_search_repos_success(
        self,
        mock_urlopen: Mock,
        discovery_service: GitHubDiscovery,
        mock_api_response: dict,
    ) -> None:
        """Test successful repository search."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_api_response).encode()
        mock_response.headers = {}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Mock verify_skill_repo to avoid additional API calls
        with patch.object(discovery_service, "verify_skill_repo", return_value=True):
            repos = discovery_service.search_repos("test query", min_stars=5)

        assert len(repos) == 1
        assert repos[0].full_name == "test/repo"
        assert repos[0].stars == 10
        assert repos[0].has_skill_file is True

    @patch("mcp_skills.services.github_discovery.request.urlopen")
    def test_search_repos_with_topics(
        self,
        mock_urlopen: Mock,
        discovery_service: GitHubDiscovery,
        mock_api_response: dict,
    ) -> None:
        """Test repository search with topic filter."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_api_response).encode()
        mock_response.headers = {}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with patch.object(discovery_service, "verify_skill_repo", return_value=True):
            repos = discovery_service.search_repos(
                "test query",
                min_stars=2,
                topics=["claude-skills"],
            )

        assert len(repos) == 1
        assert "claude-skills" in repos[0].topics

    @patch("mcp_skills.services.github_discovery.request.urlopen")
    def test_search_repos_empty_results(
        self,
        mock_urlopen: Mock,
        discovery_service: GitHubDiscovery,
    ) -> None:
        """Test search with no results."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"total_count": 0, "items": []}).encode()
        mock_response.headers = {}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        repos = discovery_service.search_repos("nonexistent query")

        assert len(repos) == 0

    @patch("mcp_skills.services.github_discovery.request.urlopen")
    def test_search_by_topic(
        self,
        mock_urlopen: Mock,
        discovery_service: GitHubDiscovery,
        mock_api_response: dict,
    ) -> None:
        """Test search by topic."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_api_response).encode()
        mock_response.headers = {}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        repos = discovery_service.search_by_topic("claude-skills", min_stars=2)

        assert len(repos) == 1
        assert repos[0].has_skill_file is True

    @patch("mcp_skills.services.github_discovery.request.urlopen")
    def test_get_trending(
        self,
        mock_urlopen: Mock,
        discovery_service: GitHubDiscovery,
        mock_api_response: dict,
    ) -> None:
        """Test get trending repositories."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_api_response).encode()
        mock_response.headers = {}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        repos = discovery_service.get_trending(timeframe="week")

        assert len(repos) == 1
        assert repos[0].has_skill_file is True

    @patch("mcp_skills.services.github_discovery.request.urlopen")
    def test_verify_skill_repo_valid(
        self,
        mock_urlopen: Mock,
        discovery_service: GitHubDiscovery,
    ) -> None:
        """Test verify_skill_repo with valid repository."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"total_count": 5}).encode()
        mock_response.headers = {}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        is_valid = discovery_service.verify_skill_repo("https://github.com/test/repo.git")

        assert is_valid is True

    @patch("mcp_skills.services.github_discovery.request.urlopen")
    def test_verify_skill_repo_invalid(
        self,
        mock_urlopen: Mock,
        discovery_service: GitHubDiscovery,
    ) -> None:
        """Test verify_skill_repo with invalid repository."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"total_count": 0}).encode()
        mock_response.headers = {}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        is_valid = discovery_service.verify_skill_repo("https://github.com/test/invalid.git")

        assert is_valid is False

    def test_verify_skill_repo_malformed_url(
        self,
        discovery_service: GitHubDiscovery,
    ) -> None:
        """Test verify_skill_repo with malformed URL."""
        is_valid = discovery_service.verify_skill_repo("not-a-url")

        assert is_valid is False

    @patch("mcp_skills.services.github_discovery.request.urlopen")
    def test_get_repo_metadata(
        self,
        mock_urlopen: Mock,
        discovery_service: GitHubDiscovery,
    ) -> None:
        """Test get repository metadata."""
        mock_repo_data = {
            "full_name": "test/repo",
            "clone_url": "https://github.com/test/repo.git",
            "description": "Test repository",
            "stargazers_count": 15,
            "forks_count": 3,
            "updated_at": "2025-11-20T10:00:00Z",
            "license": {"spdx_id": "Apache-2.0"},
            "topics": ["python", "testing"],
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_repo_data).encode()
        mock_response.headers = {}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with patch.object(discovery_service, "verify_skill_repo", return_value=True):
            metadata = discovery_service.get_repo_metadata(
                "https://github.com/test/repo.git"
            )

        assert metadata is not None
        assert metadata.full_name == "test/repo"
        assert metadata.stars == 15
        assert metadata.license == "Apache-2.0"
        assert "python" in metadata.topics

    @patch("mcp_skills.services.github_discovery.request.urlopen")
    def test_get_rate_limit_status(
        self,
        mock_urlopen: Mock,
        discovery_service: GitHubDiscovery,
    ) -> None:
        """Test get rate limit status."""
        mock_rate_limit_data = {
            "resources": {
                "core": {
                    "limit": 5000,
                    "remaining": 4999,
                    "reset": 1732550400,  # Unix timestamp
                },
                "search": {
                    "limit": 30,
                    "remaining": 29,
                    "reset": 1732550400,
                },
            }
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_rate_limit_data).encode()
        mock_response.headers = {}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        status = discovery_service.get_rate_limit_status()

        assert status["core_limit"] == 5000
        assert status["core_remaining"] == 4999
        assert status["search_limit"] == 30
        assert status["search_remaining"] == 29

    def test_parse_repo(self, discovery_service: GitHubDiscovery) -> None:
        """Test _parse_repo helper method."""
        data = {
            "full_name": "owner/repo",
            "clone_url": "https://github.com/owner/repo.git",
            "description": "Test description",
            "stargazers_count": 100,
            "forks_count": 20,
            "updated_at": "2025-11-20T10:00:00Z",
            "license": {"spdx_id": "MIT"},
            "topics": ["python", "testing"],
        }

        repo = discovery_service._parse_repo(data)

        assert repo.full_name == "owner/repo"
        assert repo.url == "https://github.com/owner/repo.git"
        assert repo.description == "Test description"
        assert repo.stars == 100
        assert repo.forks == 20
        assert repo.license == "MIT"
        assert repo.topics == ["python", "testing"]

    def test_cache_functionality(
        self,
        discovery_service: GitHubDiscovery,
    ) -> None:
        """Test caching mechanism."""
        # Set cached data
        cache_key = "/test/endpoint?param=value"
        test_data = {"test": "data"}
        discovery_service._set_cached(cache_key, test_data)

        # Retrieve cached data
        cached = discovery_service._get_cached(cache_key)
        assert cached == test_data

        # Test cache miss
        missing = discovery_service._get_cached("/nonexistent")
        assert missing is None

    def test_make_cache_key(
        self,
        discovery_service: GitHubDiscovery,
    ) -> None:
        """Test cache key generation."""
        # Without params
        key1 = discovery_service._make_cache_key("/endpoint", None)
        assert key1 == "/endpoint"

        # With params (should be sorted)
        params = {"b": "2", "a": "1"}
        key2 = discovery_service._make_cache_key("/endpoint", params)
        assert key2 == "/endpoint?a=1&b=2"

    @patch("mcp_skills.services.github_discovery.request.urlopen")
    def test_rate_limit_exceeded(
        self,
        mock_urlopen: Mock,
        discovery_service: GitHubDiscovery,
    ) -> None:
        """Test handling of rate limit exceeded (403)."""
        from urllib.error import HTTPError

        # Mock 403 rate limit error
        mock_error = HTTPError(
            url="https://api.github.com/test",
            code=403,
            msg="rate limit exceeded",
            hdrs={"X-RateLimit-Reset": "1732550400"},
            fp=None,
        )
        mock_urlopen.side_effect = mock_error

        # Should return empty dict, not raise
        result = discovery_service._api_request("/test")
        assert result == {}

    @patch("mcp_skills.services.github_discovery.request.urlopen")
    def test_network_error_handling(
        self,
        mock_urlopen: Mock,
        discovery_service: GitHubDiscovery,
    ) -> None:
        """Test handling of network errors."""
        from urllib.error import URLError

        mock_urlopen.side_effect = URLError("Network unreachable")

        with pytest.raises(URLError):
            discovery_service._api_request("/test")


class TestGitHubRepo:
    """Test GitHubRepo dataclass."""

    def test_github_repo_creation(self) -> None:
        """Test creating GitHubRepo instance."""
        repo = GitHubRepo(
            full_name="test/repo",
            url="https://github.com/test/repo.git",
            description="Test repository",
            stars=10,
            forks=2,
            updated_at=datetime.now(UTC),
            license="MIT",
            topics=["python", "testing"],
            has_skill_file=True,
        )

        assert repo.full_name == "test/repo"
        assert repo.stars == 10
        assert repo.has_skill_file is True
        assert len(repo.topics) == 2

    def test_github_repo_optional_fields(self) -> None:
        """Test GitHubRepo with optional fields as None."""
        repo = GitHubRepo(
            full_name="test/repo",
            url="https://github.com/test/repo.git",
            description=None,
            stars=5,
            forks=1,
            updated_at=datetime.now(UTC),
            license=None,
            topics=[],
        )

        assert repo.description is None
        assert repo.license is None
        assert repo.topics == []
        assert repo.has_skill_file is False  # Default value
