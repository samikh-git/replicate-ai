"""Tests for sandbox image dependency loading."""

from pathlib import Path

import pytest

from replicate_ai.sandbox_image import (
    PYPROJECT_PATH,
    build_sandbox_image,
    load_sandbox_dependencies,
)


class TestLoadSandboxDependencies:
    def test_loads_sandbox_group_from_pyproject(self):
        deps = load_sandbox_dependencies()
        assert "pandas==2.2.*" in deps
        assert "statsmodels==0.14.*" in deps
        assert not any("pymupdf" in d for d in deps)
        assert len(deps) == 6

    def test_missing_group_raises(self, tmp_path: Path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "x"\n', encoding="utf-8")
        with pytest.raises(ValueError, match="dependency-groups.sandbox"):
            load_sandbox_dependencies(pyproject)


class TestBuildSandboxImage:
    def test_returns_modal_image_with_uv_pip_install(self, monkeypatch):
        captured: list[tuple] = []

        class FakeImage:
            @staticmethod
            def debian_slim(python_version=None):
                return FakeImage()

            def uv_pip_install(self, *packages):
                captured.append(packages)
                return "built-image"

        monkeypatch.setattr("replicate_ai.sandbox_image.modal.Image", FakeImage)
        deps = load_sandbox_dependencies()
        result = build_sandbox_image()

        assert result == "built-image"
        assert captured[0] == tuple(deps)

    def test_pyproject_path_is_next_to_src(self):
        assert PYPROJECT_PATH.name == "pyproject.toml"
        assert PYPROJECT_PATH.parent.name == "replicate_ai"
