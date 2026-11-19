"""
Tests validating Dockerfile and .dockerignore configuration.
Checks syntax rules, base image selection, and non-root security.
"""

import os
import shutil
import pytest

ROOT_DIR = os.path.join(os.path.dirname(__file__), "..")


def test_dockerfile_exists_and_valid():
    """Verify Dockerfile presence and directives."""
    dockerfile_path = os.path.join(ROOT_DIR, "Dockerfile")
    assert os.path.exists(dockerfile_path)

    with open(dockerfile_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "FROM python:3.12-slim" in content, "Dockerfile should use python:3.12-slim"
    assert "WORKDIR /app" in content, "Dockerfile should set working directory"
    assert "COPY app/requirements.txt" in content, "Dockerfile should copy requirements first for caching"
    assert "pip install" in content, "Dockerfile should install dependencies"
    assert "useradd" in content or "USER" in content, "Dockerfile should configure non-root user"
    assert "CMD" in content or "ENTRYPOINT" in content, "Dockerfile should specify default CMD/ENTRYPOINT"


def test_dockerignore_exists_and_covers_essentials():
    """Verify .dockerignore excludes unnecessary files to keep image minimal."""
    dockerignore_path = os.path.join(ROOT_DIR, ".dockerignore")
    assert os.path.exists(dockerignore_path)

    with open(dockerignore_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert ".git" in content
    assert "__pycache__" in content


def test_local_docker_daemon_status():
    """
    Check if Docker CLI / daemon is available locally.
    Per instructions: If Docker is not installed locally, do not claim a Docker build succeeded.
    Prepare configuration for remote GMT execution instead.
    """
    docker_bin = shutil.which("docker")
    if docker_bin is None:
        pytest.skip("Docker CLI is not installed locally. Container builds will be handled remotely by GMT.")
    else:
        # If installed, check version
        import subprocess
        res = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        assert res.returncode == 0
