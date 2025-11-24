"""Tests for configurable hybrid search weighting.

Tests cover:
- HybridSearchConfig validation and presets
- YAML config loading
- IndexingEngine integration
- CLI flag override
- Weight calculation correctness
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from mcp_skills.models.config import HybridSearchConfig, MCPSkillsConfig
from mcp_skills.services.indexing.engine import IndexingEngine
from mcp_skills.services.indexing.hybrid_search import HybridSearcher


class TestHybridSearchConfig:
    """Test HybridSearchConfig validation and presets."""

    def test_default_values(self):
        """Test default configuration values."""
        config = HybridSearchConfig()
        assert config.vector_weight == 0.7
        assert config.graph_weight == 0.3
        assert config.preset is None

    def test_weights_must_sum_to_one(self):
        """Test that weights must sum to 1.0."""
        # Valid weights
        config = HybridSearchConfig(vector_weight=0.6, graph_weight=0.4)
        assert config.vector_weight == 0.6
        assert config.graph_weight == 0.4

        # Invalid weights - don't sum to 1.0
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            HybridSearchConfig(vector_weight=0.5, graph_weight=0.6)

        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            HybridSearchConfig(vector_weight=0.8, graph_weight=0.1)

    def test_floating_point_tolerance(self):
        """Test that small floating point errors are tolerated."""
        # Should not raise due to floating point precision
        config = HybridSearchConfig(
            vector_weight=0.7, graph_weight=0.30000000000000004
        )
        assert config.vector_weight == 0.7
        assert abs(config.graph_weight - 0.3) < 1e-6

    def test_semantic_focused_preset(self):
        """Test semantic_focused preset (0.9 vector, 0.1 graph)."""
        config = HybridSearchConfig.semantic_focused()
        assert config.vector_weight == 0.9
        assert config.graph_weight == 0.1
        assert config.preset == "semantic_focused"

    def test_graph_focused_preset(self):
        """Test graph_focused preset (0.3 vector, 0.7 graph)."""
        config = HybridSearchConfig.graph_focused()
        assert config.vector_weight == 0.3
        assert config.graph_weight == 0.7
        assert config.preset == "graph_focused"

    def test_balanced_preset(self):
        """Test balanced preset (0.5 vector, 0.5 graph)."""
        config = HybridSearchConfig.balanced()
        assert config.vector_weight == 0.5
        assert config.graph_weight == 0.5
        assert config.preset == "balanced"

    def test_current_preset(self):
        """Test current preset (0.7 vector, 0.3 graph)."""
        config = HybridSearchConfig.current()
        assert config.vector_weight == 0.7
        assert config.graph_weight == 0.3
        assert config.preset == "current"

    def test_all_presets_sum_to_one(self):
        """Test that all presets have weights summing to 1.0."""
        presets = [
            HybridSearchConfig.semantic_focused(),
            HybridSearchConfig.graph_focused(),
            HybridSearchConfig.balanced(),
            HybridSearchConfig.current(),
        ]

        for preset in presets:
            total = preset.vector_weight + preset.graph_weight
            assert abs(total - 1.0) < 1e-6, f"Preset {preset.preset} weights don't sum to 1.0"


class TestMCPSkillsConfigYAMLLoading:
    """Test YAML configuration loading."""

    def test_default_config_without_yaml(self):
        """Test that default config uses current preset when no YAML exists."""
        with patch("pathlib.Path.exists", return_value=False):
            config = MCPSkillsConfig()
            assert config.hybrid_search.vector_weight == 0.7
            assert config.hybrid_search.graph_weight == 0.3

    def test_yaml_preset_string_format(self):
        """Test loading preset from YAML using string format."""
        yaml_content = """hybrid_search: semantic_focused
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            # Create mock config directory structure
            config_dir = yaml_path.parent / ".mcp-skills"
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / "config.yaml"

            # Copy temp file to expected location
            import shutil

            shutil.copy(yaml_path, config_file)

            with patch.object(Path, "home", return_value=yaml_path.parent):
                config = MCPSkillsConfig()
                assert config.hybrid_search.vector_weight == 0.9
                assert config.hybrid_search.graph_weight == 0.1

            # Cleanup
            shutil.rmtree(config_dir, ignore_errors=True)
        finally:
            yaml_path.unlink(missing_ok=True)

    def test_yaml_preset_dict_format(self):
        """Test loading preset from YAML using dict format."""
        yaml_content = """hybrid_search:
  preset: graph_focused
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            # Create mock config directory structure
            config_dir = yaml_path.parent / ".mcp-skills"
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / "config.yaml"

            # Copy temp file to expected location
            import shutil

            shutil.copy(yaml_path, config_file)

            with patch.object(Path, "home", return_value=yaml_path.parent):
                config = MCPSkillsConfig()
                assert config.hybrid_search.vector_weight == 0.3
                assert config.hybrid_search.graph_weight == 0.7

            # Cleanup
            shutil.rmtree(config_dir, ignore_errors=True)
        finally:
            yaml_path.unlink(missing_ok=True)

    def test_yaml_custom_weights(self):
        """Test loading custom weights from YAML."""
        yaml_content = """hybrid_search:
  vector_weight: 0.6
  graph_weight: 0.4
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            # Create mock config directory structure
            config_dir = yaml_path.parent / ".mcp-skills"
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / "config.yaml"

            # Copy temp file to expected location
            import shutil

            shutil.copy(yaml_path, config_file)

            with patch.object(Path, "home", return_value=yaml_path.parent):
                config = MCPSkillsConfig()
                assert config.hybrid_search.vector_weight == 0.6
                assert config.hybrid_search.graph_weight == 0.4

            # Cleanup
            shutil.rmtree(config_dir, ignore_errors=True)
        finally:
            yaml_path.unlink(missing_ok=True)

    def test_invalid_preset_name(self):
        """Test that invalid preset names raise ValueError."""
        with pytest.raises(ValueError, match="Invalid preset"):
            MCPSkillsConfig._get_preset("invalid_preset")

    def test_get_preset_valid_names(self):
        """Test _get_preset method with all valid preset names."""
        preset_names = ["semantic_focused", "graph_focused", "balanced", "current"]

        for name in preset_names:
            config = MCPSkillsConfig._get_preset(name)
            assert config.preset == name
            assert abs(config.vector_weight + config.graph_weight - 1.0) < 1e-6


class TestHybridSearcherIntegration:
    """Test HybridSearcher with configurable weights."""

    def test_hybrid_searcher_default_weights(self):
        """Test that HybridSearcher uses class defaults when no weights provided."""
        vector_store = MagicMock()
        graph_store = MagicMock()

        searcher = HybridSearcher(
            vector_store=vector_store,
            graph_store=graph_store,
        )

        assert searcher.vector_weight == 0.7
        assert searcher.graph_weight == 0.3

    def test_hybrid_searcher_custom_weights(self):
        """Test that HybridSearcher accepts custom weights."""
        vector_store = MagicMock()
        graph_store = MagicMock()

        searcher = HybridSearcher(
            vector_store=vector_store,
            graph_store=graph_store,
            vector_weight=0.9,
            graph_weight=0.1,
        )

        assert searcher.vector_weight == 0.9
        assert searcher.graph_weight == 0.1

    def test_hybrid_searcher_only_vector_weight(self):
        """Test that providing only vector_weight computes graph_weight."""
        vector_store = MagicMock()
        graph_store = MagicMock()

        searcher = HybridSearcher(
            vector_store=vector_store,
            graph_store=graph_store,
            vector_weight=0.8,
        )

        assert searcher.vector_weight == 0.8
        assert abs(searcher.graph_weight - 0.2) < 1e-6  # Floating point tolerance

    def test_hybrid_searcher_only_graph_weight(self):
        """Test that providing only graph_weight computes vector_weight."""
        vector_store = MagicMock()
        graph_store = MagicMock()

        searcher = HybridSearcher(
            vector_store=vector_store,
            graph_store=graph_store,
            graph_weight=0.4,
        )

        assert searcher.vector_weight == 0.6
        assert searcher.graph_weight == 0.4

    def test_hybrid_searcher_invalid_weights(self):
        """Test that invalid weights raise ValueError."""
        vector_store = MagicMock()
        graph_store = MagicMock()

        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            HybridSearcher(
                vector_store=vector_store,
                graph_store=graph_store,
                vector_weight=0.5,
                graph_weight=0.6,
            )


class TestIndexingEngineIntegration:
    """Test IndexingEngine with config-based weights."""

    @patch("mcp_skills.services.indexing.engine.VectorStore")
    @patch("mcp_skills.services.indexing.engine.GraphStore")
    def test_indexing_engine_without_config(self, mock_graph, mock_vector):
        """Test that IndexingEngine works without config (backward compatibility)."""
        engine = IndexingEngine()

        # Should use default weights
        assert engine.hybrid_searcher.vector_weight == 0.7
        assert engine.hybrid_searcher.graph_weight == 0.3

    @patch("mcp_skills.services.indexing.engine.VectorStore")
    @patch("mcp_skills.services.indexing.engine.GraphStore")
    def test_indexing_engine_with_config(self, mock_graph, mock_vector):
        """Test that IndexingEngine uses config weights when provided."""
        config = MCPSkillsConfig()
        config.hybrid_search = HybridSearchConfig.semantic_focused()

        engine = IndexingEngine(config=config)

        # Should use config weights
        assert engine.hybrid_searcher.vector_weight == 0.9
        assert engine.hybrid_searcher.graph_weight == 0.1

    @patch("mcp_skills.services.indexing.engine.VectorStore")
    @patch("mcp_skills.services.indexing.engine.GraphStore")
    def test_indexing_engine_with_all_presets(self, mock_graph, mock_vector):
        """Test IndexingEngine with all preset configurations."""
        presets = [
            ("semantic_focused", 0.9, 0.1),
            ("graph_focused", 0.3, 0.7),
            ("balanced", 0.5, 0.5),
            ("current", 0.7, 0.3),
        ]

        for preset_name, expected_vector, expected_graph in presets:
            config = MCPSkillsConfig()
            config.hybrid_search = config._get_preset(preset_name)

            engine = IndexingEngine(config=config)

            assert (
                engine.hybrid_searcher.vector_weight == expected_vector
            ), f"Failed for {preset_name}"
            assert (
                engine.hybrid_searcher.graph_weight == expected_graph
            ), f"Failed for {preset_name}"


class TestWeightCalculation:
    """Test that weight calculation in search is correct."""

    @patch("mcp_skills.services.indexing.engine.VectorStore")
    @patch("mcp_skills.services.indexing.engine.GraphStore")
    def test_weight_calculation_in_combine_results(self, mock_graph, mock_vector):
        """Test that _combine_results uses configured weights correctly."""
        # Create mock skill manager
        mock_skill = MagicMock()
        mock_skill.id = "test-skill"
        mock_skill.name = "Test Skill"

        mock_skill_manager = MagicMock()
        mock_skill_manager.load_skill.return_value = mock_skill

        # Create mock stores
        vector_store = MagicMock()
        graph_store = MagicMock()

        # Test with semantic_focused weights (0.9 vector, 0.1 graph)
        searcher = HybridSearcher(
            vector_store=vector_store,
            graph_store=graph_store,
            skill_manager=mock_skill_manager,
            vector_weight=0.9,
            graph_weight=0.1,
        )

        # Mock results
        vector_results = [{"skill_id": "test-skill", "score": 1.0}]
        graph_results = [{"skill_id": "test-skill", "score": 0.5}]

        # Combine results
        combined = searcher._combine_results(vector_results, graph_results)

        # Expected score: 0.9 * 1.0 + 0.1 * 0.5 = 0.95
        assert len(combined) == 1
        assert abs(combined[0].score - 0.95) < 1e-6

    @patch("mcp_skills.services.indexing.engine.VectorStore")
    @patch("mcp_skills.services.indexing.engine.GraphStore")
    def test_weight_calculation_graph_focused(self, mock_graph, mock_vector):
        """Test weight calculation with graph_focused preset."""
        mock_skill = MagicMock()
        mock_skill.id = "test-skill"
        mock_skill.name = "Test Skill"

        mock_skill_manager = MagicMock()
        mock_skill_manager.load_skill.return_value = mock_skill

        vector_store = MagicMock()
        graph_store = MagicMock()

        # Test with graph_focused weights (0.3 vector, 0.7 graph)
        searcher = HybridSearcher(
            vector_store=vector_store,
            graph_store=graph_store,
            skill_manager=mock_skill_manager,
            vector_weight=0.3,
            graph_weight=0.7,
        )

        vector_results = [{"skill_id": "test-skill", "score": 0.8}]
        graph_results = [{"skill_id": "test-skill", "score": 0.6}]

        combined = searcher._combine_results(vector_results, graph_results)

        # Expected score: 0.3 * 0.8 + 0.7 * 0.6 = 0.24 + 0.42 = 0.66
        assert len(combined) == 1
        assert abs(combined[0].score - 0.66) < 1e-6


class TestCLIIntegration:
    """Test CLI flag override functionality."""

    def test_cli_override_with_search_mode(self):
        """Test that CLI --search-mode flag overrides config."""
        # Load default config
        config = MCPSkillsConfig()
        assert config.hybrid_search.vector_weight == 0.7  # Default

        # Simulate CLI override
        config.hybrid_search = config._get_preset("semantic_focused")

        # Should be overridden
        assert config.hybrid_search.vector_weight == 0.9
        assert config.hybrid_search.graph_weight == 0.1

    def test_all_cli_presets(self):
        """Test that all CLI preset values are valid."""
        config = MCPSkillsConfig()

        cli_presets = ["semantic_focused", "graph_focused", "balanced", "current"]

        for preset_name in cli_presets:
            # This should not raise
            preset_config = config._get_preset(preset_name)
            assert preset_config.preset == preset_name
            assert abs(preset_config.vector_weight + preset_config.graph_weight - 1.0) < 1e-6


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    @patch("mcp_skills.services.indexing.engine.VectorStore")
    @patch("mcp_skills.services.indexing.engine.GraphStore")
    def test_existing_code_without_config_still_works(self, mock_graph, mock_vector):
        """Test that existing code using IndexingEngine still works."""
        # Old usage pattern - should still work with defaults
        engine = IndexingEngine(skill_manager=None)

        assert engine.hybrid_searcher.vector_weight == 0.7
        assert engine.hybrid_searcher.graph_weight == 0.3

    @patch("mcp_skills.services.indexing.engine.VectorStore")
    @patch("mcp_skills.services.indexing.engine.GraphStore")
    def test_class_constants_still_exist(self, mock_graph, mock_vector):
        """Test that class constants are maintained for backward compatibility."""
        assert HybridSearcher.VECTOR_WEIGHT == 0.7
        assert HybridSearcher.GRAPH_WEIGHT == 0.3
        assert IndexingEngine.VECTOR_WEIGHT == 0.7
        assert IndexingEngine.GRAPH_WEIGHT == 0.3
