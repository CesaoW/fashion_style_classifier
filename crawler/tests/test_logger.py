import logging
import tempfile
from pathlib import Path

import pytest

from src.utils.logger import setup_logger


class TestLogger:
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_setup_logger_creates_file(self):
        log_file = self.temp_dir / "test.log"
        logger = setup_logger("TestLogger", str(log_file))
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "TestLogger"
        assert logger.level == logging.INFO

    def test_setup_logger_writes_to_file(self):
        log_file = self.temp_dir / "test.log"
        logger = setup_logger("TestLogger2", str(log_file))
        
        logger.info("Test message")
        
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content
        assert "TestLogger2" in content

    def test_setup_logger_rotating_handler(self):
        log_file = self.temp_dir / "test.log"
        logger = setup_logger("TestLogger3", str(log_file))
        
        handlers = logger.handlers
        rotating_handlers = [h for h in handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(rotating_handlers) == 1
        assert rotating_handlers[0].maxBytes == 5 * 1024 * 1024
        assert rotating_handlers[0].backupCount == 2

    def test_setup_logger_stream_handler(self):
        log_file = self.temp_dir / "test.log"
        logger = setup_logger("TestLogger4", str(log_file))
        
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(stream_handlers) >= 1

    def test_setup_logger_idempotent(self):
        log_file = self.temp_dir / "test.log"
        logger1 = setup_logger("TestLogger5", str(log_file))
        logger2 = setup_logger("TestLogger5", str(log_file))
        
        assert logger1 is logger2
        assert len(logger1.handlers) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])