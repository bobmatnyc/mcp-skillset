"""Pydantic models for configuration management."""

import logging
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


logger = logging.getLogger(__name__)


class VectorStoreConfig(BaseSettings):
    """Vector store configuration.

    Attributes:
        backend: Vector store backend (chromadb, qdrant, faiss)
        embedding_model: Sentence transformer model name
        collection_name: Vector collection name
        persist_directory: Directory for persistent storage (defaults to ~/.mcp-skillset/indices/vector_store)
    """

    backend: Literal["chromadb", "qdrant", "faiss"] = Field(
        "chromadb", description="Vector store backend"
    )
    embedding_model: str = Field(
        "all-MiniLM-L6-v2", description="Sentence transformer model"
    )
    collection_name: str = Field("skills_v1", description="Collection name")
    persist_directory: Path | None = Field(
        None,
        description="Persistence directory (defaults to ~/.mcp-skillset/indices/vector_store)",
    )


class HybridSearchConfig(BaseSettings):
    """Hybrid search weighting configuration.

    Configures the relative weights of vector similarity search vs.
    knowledge graph relationships in hybrid search.

    Attributes:
        vector_weight: Weight for vector similarity (0.0-1.0)
        graph_weight: Weight for graph relationships (0.0-1.0)
        preset: Optional preset name for identification

    Constraints:
        - vector_weight + graph_weight must equal 1.0
        - Both weights must be non-negative

    Use Cases:
        - semantic_focused (0.9/0.1): Best for natural language queries
        - graph_focused (0.3/0.7): Best for discovering related skills
        - balanced (0.5/0.5): General purpose, equal weighting
        - current (0.7/0.3): Optimized through testing (default)
    """

    vector_weight: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Weight for vector similarity search (0.0-1.0)",
    )
    graph_weight: float = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="Weight for knowledge graph relationships (0.0-1.0)",
    )
    preset: str | None = Field(
        None,
        description="Preset name (semantic_focused, graph_focused, balanced, current)",
    )

    @field_validator("graph_weight")
    @classmethod
    def validate_weights_sum(cls, v: float, info: Any) -> float:
        """Validate that weights sum to 1.0.

        Args:
            v: graph_weight value
            info: Validation context containing vector_weight

        Returns:
            Validated graph_weight

        Raises:
            ValueError: If weights don't sum to 1.0
        """
        vector_weight = info.data.get("vector_weight", 0.0)
        total = vector_weight + v
        if abs(total - 1.0) > 1e-6:  # Allow small floating point error
            raise ValueError(
                f"Weights must sum to 1.0, got {total:.6f} "
                f"(vector_weight={vector_weight}, graph_weight={v})"
            )
        return v

    @classmethod
    def semantic_focused(cls) -> "HybridSearchConfig":
        """Preset optimized for semantic similarity queries.

        Best for: Natural language queries, fuzzy matching, concept search
        Trade-off: Less emphasis on explicit skill relationships

        Returns:
            HybridSearchConfig with 0.9 vector, 0.1 graph weighting
        """
        return cls(vector_weight=0.9, graph_weight=0.1, preset="semantic_focused")

    @classmethod
    def graph_focused(cls) -> "HybridSearchConfig":
        """Preset optimized for relationship discovery.

        Best for: Finding related skills, dependency traversal, connected components
        Trade-off: Less emphasis on semantic similarity

        Returns:
            HybridSearchConfig with 0.3 vector, 0.7 graph weighting
        """
        return cls(vector_weight=0.3, graph_weight=0.7, preset="graph_focused")

    @classmethod
    def balanced(cls) -> "HybridSearchConfig":
        """Preset with equal weighting.

        Best for: General purpose, no preference between methods
        Trade-off: May not excel at either semantic or relationship queries

        Returns:
            HybridSearchConfig with 0.5 vector, 0.5 graph weighting
        """
        return cls(vector_weight=0.5, graph_weight=0.5, preset="balanced")

    @classmethod
    def current(cls) -> "HybridSearchConfig":
        """Default preset optimized through testing.

        Best for: General skill discovery with slight semantic emphasis
        This is the proven default from testing and should work well for most use cases.

        Returns:
            HybridSearchConfig with 0.7 vector, 0.3 graph weighting
        """
        return cls(vector_weight=0.7, graph_weight=0.3, preset="current")


class KnowledgeGraphConfig(BaseSettings):
    """Knowledge graph configuration.

    Attributes:
        backend: Graph backend (networkx, neo4j)
        persist_path: Path for graph persistence (defaults to ~/.mcp-skillset/indices/knowledge_graph.pkl)
    """

    backend: Literal["networkx", "neo4j"] = Field(
        "networkx", description="Knowledge graph backend"
    )
    persist_path: Path | None = Field(
        None,
        description="Graph persistence path (defaults to ~/.mcp-skillset/indices/knowledge_graph.pkl)",
    )


class ServerConfig(BaseSettings):
    """MCP server configuration.

    Attributes:
        transport: Transport protocol (stdio, http, sse)
        port: Port for HTTP transport
        log_level: Logging level
        max_loaded_skills: Maximum skills to keep in memory
    """

    transport: Literal["stdio", "http", "sse"] = Field(
        "stdio", description="Transport protocol"
    )
    port: int = Field(8000, description="HTTP server port", ge=1024, le=65535)
    log_level: Literal["debug", "info", "warning", "error"] = Field(
        "info", description="Logging level"
    )
    max_loaded_skills: int = Field(
        50, description="Maximum skills in memory cache", ge=1
    )


class GitHubDiscoveryConfig(BaseSettings):
    """GitHub discovery configuration.

    Attributes:
        enabled: Enable GitHub repository discovery
        min_stars: Minimum star count for discovered repositories
        topics: Default topics to search for
        github_token: Optional GitHub token for higher rate limits
    """

    enabled: bool = Field(True, description="Enable GitHub discovery")
    min_stars: int = Field(2, description="Minimum stars filter", ge=0)
    topics: list[str] = Field(
        default_factory=lambda: [
            "claude-skills",
            "anthropic-skills",
            "mcp-skills",
            "ai-skills",
        ],
        description="Default search topics",
    )
    github_token: str | None = Field(
        None,
        description="GitHub personal access token (optional, for higher rate limits)",
    )


class RepositoryConfig(BaseSettings):
    """Repository configuration.

    Attributes:
        url: Git repository URL
        priority: Repository priority (0-100)
        auto_update: Automatically update on startup
    """

    url: str = Field(..., description="Git repository URL")
    priority: int = Field(50, description="Repository priority", ge=0, le=100)
    auto_update: bool = Field(True, description="Auto-update on startup")


class HookConfig(BaseSettings):
    """Hook enrichment configuration.

    Configures the behavior of Claude Code hook enrichment.

    Attributes:
        enabled: Whether hook enrichment is enabled
        threshold: Similarity threshold for skill matching (0.0-1.0)
        max_skills: Maximum number of skills to suggest
    """

    enabled: bool = Field(True, description="Enable hook enrichment")
    threshold: float = Field(
        0.6,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for skill matching",
    )
    max_skills: int = Field(
        5,
        ge=1,
        le=10,
        description="Maximum skills to suggest in hints",
    )


class AutoUpdateConfig(BaseSettings):
    """Auto-update configuration for repository maintenance.

    Configures automatic repository updates when MCP server starts.

    Attributes:
        enabled: Enable auto-update on MCP server startup
        max_age_hours: Maximum age in hours before repository is considered stale
    """

    enabled: bool = Field(True, description="Enable auto-update on startup")
    max_age_hours: int = Field(
        24,
        ge=1,
        le=168,
        description="Max age in hours before update (1-168 hours, default: 24)",
    )


class MCPSkillsConfig(BaseSettings):
    """Main mcp-skillset configuration.

    Loads configuration from:
    1. Environment variables (MCP_SKILLS_*)
    2. Config file (~/.mcp-skillset/config.yaml)
    3. Defaults
    """

    # Base directories
    base_dir: Path = Field(
        default_factory=lambda: Path.home() / ".mcp-skillset",
        description="Base directory for mcp-skillset",
    )
    repos_dir: Path | None = Field(None, description="Repositories directory")
    indices_dir: Path | None = Field(None, description="Indices directory")

    # Component configurations
    vector_store: VectorStoreConfig = Field(
        default_factory=VectorStoreConfig,
        description="Vector store config",
    )
    knowledge_graph: KnowledgeGraphConfig = Field(
        default_factory=KnowledgeGraphConfig,
        description="Knowledge graph config",
    )
    server: ServerConfig = Field(
        default_factory=ServerConfig,
        description="Server config",
    )
    hybrid_search: HybridSearchConfig = Field(
        default_factory=HybridSearchConfig.current,
        description="Hybrid search weighting config",
    )
    github_discovery: GitHubDiscoveryConfig = Field(
        default_factory=GitHubDiscoveryConfig,
        description="GitHub discovery config",
    )

    # Repositories
    repositories: list[RepositoryConfig] = Field(
        default_factory=list, description="Configured repositories"
    )

    # Toolchain detection
    toolchain_cache_duration: int = Field(
        3600, description="Toolchain cache duration (seconds)", ge=0
    )
    auto_recommend: bool = Field(True, description="Auto-recommend skills on detection")

    # Hook configuration
    hooks: HookConfig = Field(
        default_factory=HookConfig,
        description="Claude Code hook enrichment config",
    )

    # Auto-update configuration
    auto_update: AutoUpdateConfig = Field(
        default_factory=AutoUpdateConfig,
        description="Auto-update config for repository maintenance",
    )

    class Config:
        """Pydantic configuration."""

        env_prefix = "MCP_SKILLS_"
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):  # type: ignore
        """Initialize configuration with computed defaults.

        Configuration loading priority:
        1. Explicit kwargs (highest priority)
        2. Environment variables (MCP_SKILLS_*)
        3. Config file (~/.mcp-skillset/config.yaml)
        4. Defaults (lowest priority)
        """
        # Load YAML config if not provided in kwargs
        config_path = Path.home() / ".mcp-skillset" / "config.yaml"
        yaml_config: dict[str, Any] = {}

        if config_path.exists() and "hybrid_search" not in kwargs:
            try:
                with open(config_path) as f:
                    yaml_config = yaml.safe_load(f) or {}
                logger.debug(f"Loaded config from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")

        # Process hybrid_search configuration from YAML
        if "hybrid_search" in yaml_config and "hybrid_search" not in kwargs:
            hs_config = yaml_config["hybrid_search"]

            # Handle preset shortcuts
            if isinstance(hs_config, str):
                # Support: hybrid_search: "current"
                preset = hs_config
                kwargs["hybrid_search"] = self._get_preset(preset)
            elif isinstance(hs_config, dict):
                # Support: hybrid_search: {preset: "current"}
                # or hybrid_search: {vector_weight: 0.7, graph_weight: 0.3}
                if "preset" in hs_config and len(hs_config) == 1:
                    preset = hs_config["preset"]
                    kwargs["hybrid_search"] = self._get_preset(preset)
                else:
                    # Custom weights
                    kwargs["hybrid_search"] = HybridSearchConfig(**hs_config)

        super().__init__(**kwargs)

        # Set computed paths if not provided
        if self.repos_dir is None:
            self.repos_dir = self.base_dir / "repos"
        if self.indices_dir is None:
            self.indices_dir = self.base_dir / "indices"
        if self.vector_store.persist_directory is None:
            self.vector_store.persist_directory = self.indices_dir / "vector_store"
        if self.knowledge_graph.persist_path is None:
            self.knowledge_graph.persist_path = self.indices_dir / "knowledge_graph.pkl"

        # Create directories
        self.base_dir.mkdir(parents=True, exist_ok=True)
        if self.repos_dir:
            self.repos_dir.mkdir(parents=True, exist_ok=True)
        if self.indices_dir:
            self.indices_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _get_preset(preset: str) -> HybridSearchConfig:
        """Get preset configuration by name.

        Args:
            preset: Preset name (semantic_focused, graph_focused, balanced, current)

        Returns:
            HybridSearchConfig instance for the preset

        Raises:
            ValueError: If preset name is invalid
        """
        presets = {
            "semantic_focused": HybridSearchConfig.semantic_focused,
            "graph_focused": HybridSearchConfig.graph_focused,
            "balanced": HybridSearchConfig.balanced,
            "current": HybridSearchConfig.current,
        }

        if preset not in presets:
            raise ValueError(
                f"Invalid preset '{preset}'. "
                f"Valid options: {', '.join(presets.keys())}"
            )

        return presets[preset]()
