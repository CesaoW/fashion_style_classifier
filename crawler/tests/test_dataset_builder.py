import json
import tempfile
from pathlib import Path
from PIL import Image

import pytest

from src.dataset.dataset_builder import DatasetBuilder


class TestDatasetBuilder:
    def setup_method(self):
        self.builder = DatasetBuilder(train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, seed=42)
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_image(self, name: str, color: tuple = (255, 0, 0)) -> Path:
        img = Image.new("RGB", (100, 100), color)
        path = self.temp_dir / name
        img.save(path)
        return path

    def test_build_dataset_empty(self):
        from src.config.settings import FILTERED_DIR, DATASET_DIR
        import src.dataset.dataset_builder as ds_module
        original_filtered = ds_module.FILTERED_DIR
        original_dataset = ds_module.DATASET_DIR
        try:
            ds_module.FILTERED_DIR = self.temp_dir
            ds_module.DATASET_DIR = self.temp_dir / "dataset"
            
            manifest = self.builder.build_dataset()
            
            assert manifest["total_images"] == 0
            assert manifest["splits"]["train"] == 0
            assert manifest["splits"]["val"] == 0
            assert manifest["splits"]["test"] == 0
        finally:
            ds_module.FILTERED_DIR = original_filtered
            ds_module.DATASET_DIR = original_dataset

    def test_build_dataset_single_style(self):
        from src.config.settings import FILTERED_DIR, DATASET_DIR, STYLES
        import src.dataset.dataset_builder as ds_module
        original_filtered = ds_module.FILTERED_DIR
        original_dataset = ds_module.DATASET_DIR
        original_styles = ds_module.STYLES
        try:
            ds_module.FILTERED_DIR = self.temp_dir
            ds_module.DATASET_DIR = self.temp_dir / "dataset"
            ds_module.STYLES = {"test_style": {"display_name": "Test"}}
            
            style_dir = self.temp_dir / "test_style"
            style_dir.mkdir()
            
            images = []
            for i in range(10):
                img_path = self.create_test_image(f"img_{i}.jpg", color=(i*25, 0, 0))
                img_path.rename(style_dir / f"img_{i}.jpg")
                images.append(style_dir / f"img_{i}.jpg")
            
            metadata = [
                {"id": f"img_{i}", "style": "test_style", "filtered_path": str(images[i])}
                for i in range(10)
            ]
            with open(style_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)
            
            manifest = self.builder.build_dataset()
            
            assert manifest["total_images"] == 10
            assert manifest["styles"]["test_style"]["total"] == 10
            assert manifest["styles"]["test_style"]["train"] == 7
            assert manifest["styles"]["test_style"]["val"] == 1
            assert manifest["styles"]["test_style"]["test"] == 2
            
            train_dir = self.temp_dir / "dataset" / "train" / "test_style"
            val_dir = self.temp_dir / "dataset" / "val" / "test_style"
            test_dir = self.temp_dir / "dataset" / "test" / "test_style"
            
            assert len(list(train_dir.glob("*.jpg"))) == 7
            assert len(list(val_dir.glob("*.jpg"))) == 1
            assert len(list(test_dir.glob("*.jpg"))) == 2
        finally:
            ds_module.FILTERED_DIR = original_filtered
            ds_module.DATASET_DIR = original_dataset
            ds_module.STYLES = original_styles

    def test_split_ratios_sum_to_one(self):
        assert abs(self.builder.train_ratio + self.builder.val_ratio + self.builder.test_ratio - 1.0) < 1e-9

    def test_reproducibility(self):
        from src.config.settings import FILTERED_DIR, DATASET_DIR, STYLES
        import src.dataset.dataset_builder as ds_module
        original_filtered = ds_module.FILTERED_DIR
        original_dataset = ds_module.DATASET_DIR
        original_styles = ds_module.STYLES
        try:
            ds_module.FILTERED_DIR = self.temp_dir
            ds_module.DATASET_DIR = self.temp_dir / "dataset"
            ds_module.STYLES = {"test_style": {"display_name": "Test"}}
            
            style_dir = self.temp_dir / "test_style"
            style_dir.mkdir()
            
            images = []
            for i in range(20):
                img_path = self.create_test_image(f"img_{i}.jpg")
                img_path.rename(style_dir / f"img_{i}.jpg")
                images.append(style_dir / f"img_{i}.jpg")
            
            metadata = [
                {"id": f"img_{i}", "style": "test_style", "filtered_path": str(images[i])}
                for i in range(20)
            ]
            with open(style_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)
            
            manifest1 = self.builder.build_dataset()
            
            import shutil
            shutil.rmtree(self.temp_dir / "dataset")
            
            builder2 = DatasetBuilder(train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, seed=42)
            manifest2 = builder2.build_dataset()
            
            assert manifest1["styles"]["test_style"]["train"] == manifest2["styles"]["test_style"]["train"]
            assert manifest1["styles"]["test_style"]["val"] == manifest2["styles"]["test_style"]["val"]
            assert manifest1["styles"]["test_style"]["test"] == manifest2["styles"]["test_style"]["test"]
        finally:
            ds_module.FILTERED_DIR = original_filtered
            ds_module.DATASET_DIR = original_dataset
            ds_module.STYLES = original_styles


if __name__ == "__main__":
    pytest.main([__file__, "-v"])