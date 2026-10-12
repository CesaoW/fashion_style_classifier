import hashlib
import tempfile
from pathlib import Path
from PIL import Image

import pytest

from src.processors.deduplicator import Deduplicator


class TestDeduplicator:
    def setup_method(self):
        self.deduper = Deduplicator(max_hash_distance=5)
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_image(self, name: str, color: tuple = (255, 0, 0), size: tuple = (100, 100)) -> Path:
        img = Image.new("RGB", size, color)
        path = self.temp_dir / name
        img.save(path)
        return path

    def test_get_md5(self):
        img_path = self.create_test_image("test.jpg")
        md5 = self.deduper.get_md5(img_path)
        assert len(md5) == 32
        assert all(c in "0123456789abcdef" for c in md5)

    def test_get_md5_consistent(self):
        img_path = self.create_test_image("test.jpg")
        md5_1 = self.deduper.get_md5(img_path)
        md5_2 = self.deduper.get_md5(img_path)
        assert md5_1 == md5_2

    def test_get_md5_different_images(self):
        img1 = self.create_test_image("test1.jpg", color=(255, 0, 0))
        img2 = self.create_test_image("test2.jpg", color=(0, 255, 0))
        md5_1 = self.deduper.get_md5(img1)
        md5_2 = self.deduper.get_md5(img2)
        assert md5_1 != md5_2

    def test_get_phash(self):
        img_path = self.create_test_image("test.jpg")
        with Image.open(img_path) as img:
            phash = self.deduper.get_phash(img)
        assert phash is not None
        assert hasattr(phash, '__sub__')

    def test_process_style_empty_dir(self):
        empty_style_dir = self.temp_dir / "empty_style"
        empty_style_dir.mkdir()
        from src.config.settings import RAW_DIR, CLEANED_DIR
        import src.processors.deduplicator as dedup_module
        original_raw = dedup_module.RAW_DIR
        original_cleaned = dedup_module.CLEANED_DIR
        try:
            dedup_module.RAW_DIR = self.temp_dir
            dedup_module.CLEANED_DIR = self.temp_dir / "cleaned"
            result = self.deduper.process_style("empty_style")
            assert result == []
        finally:
            dedup_module.RAW_DIR = original_raw
            dedup_module.CLEANED_DIR = original_cleaned

    def test_md5_deduplication(self):
        from src.config.settings import RAW_DIR, CLEANED_DIR
        import src.processors.deduplicator as dedup_module
        original_raw = dedup_module.RAW_DIR
        original_cleaned = dedup_module.CLEANED_DIR
        try:
            dedup_module.RAW_DIR = self.temp_dir
            dedup_module.CLEANED_DIR = self.temp_dir / "cleaned"
            
            style_dir = self.temp_dir / "test_style"
            style_dir.mkdir()
            
            img1 = self.create_test_image("img1.jpg", color=(255, 0, 0))
            img2 = self.create_test_image("img2.jpg", color=(255, 0, 0))
            
            import json
            metadata = [
                {"id": "img1", "style": "test_style", "local_path": str(img1)},
                {"id": "img2", "style": "test_style", "local_path": str(img2)},
            ]
            with open(style_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)
            
            global_md5 = set()
            global_hashes = []
            result = self.deduper.process_style("test_style", global_md5, global_hashes)
            
            assert len(result) == 1
            assert len(global_md5) == 1
        finally:
            dedup_module.RAW_DIR = original_raw
            dedup_module.CLEANED_DIR = original_cleaned


if __name__ == "__main__":
    pytest.main([__file__, "-v"])