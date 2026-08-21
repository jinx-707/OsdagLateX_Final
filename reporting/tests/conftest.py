"""Shared test fixtures."""

import os
import tempfile
from typing import Generator

import pytest


@pytest.fixture
def tmp_dir() -> Generator[str, None, None]:
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def sample_image(tmp_dir: str) -> str:
    img_path = os.path.join(tmp_dir, "test_image.png")
    with open(img_path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
    return img_path
