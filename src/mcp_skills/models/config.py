"""Pydantic models for configuration management."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class VectorStoreConfig(BaseSettings):
    """Vector store configuration.

    Attributes:
        backend: Vector store backend (chromadb, qdrant, faiss)
        embedding_model: Sentence transformer model name
        collection_name: Vector collection name
        persist_directory: Directory for persistent storage
    """

    backend: Literal["chromadb", "qdrant", "faiss"] = Field(
        "chromadb", description="Vector store backend"
    )
    embedding_model: str = Field(
        "all-MiniLM-L6-v2", description="Sentence transformer model"
    )
    collection_name: str = Field("skills_v1", description="Collection name")
    persist_directory: Path | None = Field(None, description="Persistence directory")


class KnowledgeGraphConfig(BaseSettings):
    """Knowledge graph configuration.

    Attributes:
        backend: Graph backend (networkx, neo4j)
        persist_path: Path for graph persistence
    """

    backend: Literal["networkx", "neo4j"] = Field(
        "networkx", description="Knowledge graph backend"
    )
    persist_path: Path | None = Field(None, description="Graph persistence path")


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


class MCPSkillsConfig(BaseSettings):
    """Main mcp-skills configuration.

    Loads configuration from:
    1. Environment variables (MCP_SKILLS_*)
    2. Config file (~/.mcp-skills/config.yaml)
    3. Defaults
    """

    # Base directories
    base_dir: Path = Field(
        default_factory=lambda: Path.home() / ".mcp-skills",
        description="Base directory for mcp-skills",
    )
    repos_dir: Path | None = Field(None, description="Repositories directory")
    indices_dir: Path | None = Field(None, description="Indices directory")

    # Component configurations
    vector_store: VectorStoreConfig = Field(
        default_factory=VectorStoreConfig, description="Vector store config"
    )
    knowledge_graph: KnowledgeGraphConfig = Field(
        default_factory=KnowledgeGraphConfig, description="Knowledge graph config"
    )
    server: ServerConfig = Field(
        default_factory=ServerConfig, description="Server config"
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

    class Config:
        """Pydantic configuration."""

        env_prefix = "MCP_SKILLS_"
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):  # type: ignore
        """Initialize configuration with computed defaults."""
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
