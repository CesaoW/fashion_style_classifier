import tempfile
from pathlib import Path

import pytest

from src.config.settings import (
    ROOT_DIR, DATA_DIR, RAW_DIR, CLEANED_DIR, FILTERED_DIR, DATASET_DIR,
    STYLES_CONFIG_PATH, load_styles_config, STYLES, AI_BLACKLIST_KEYWORDS, NEGATIVE_KEYWORDS
)


class TestSettings:
    def test_paths_exist(self):
        assert ROOT_DIR.exists()
        assert ROOT_DIR.name == "crawler"

    def test_styles_config_path(self):
        assert STYLES_CONFIG_PATH.exists()
        assert STYLES_CONFIG_PATH.name == "styles_config.yaml"

    def test_load_styles_config(self):
        config = load_styles_config()
        assert isinstance(config, dict)
        assert "styles" in config

    def test_styles_loaded(self):
        assert isinstance(STYLES, dict)
        assert len(STYLES) == 6
        expected_styles = {"streetwear", "classico", "casual", "alternativo", "country", "boho"}
        assert set(STYLES.keys()) == expected_styles

    def test_style_structure(self):
        for style_name, style_info in STYLES.items():
            assert "display_name" in style_info
            assert "search_queries" in style_info
            assert isinstance(style_info["search_queries"], list)
            assert len(style_info["search_queries"]) > 0

    def test_ai_blacklist_keywords(self):
        assert isinstance(AI_BLACKLIST_KEYWORDS, list)

    def test_negative_keywords(self):
        assert isinstance(NEGATIVE_KEYWORDS, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])