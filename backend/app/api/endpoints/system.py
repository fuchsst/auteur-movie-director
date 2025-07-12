"""
System information endpoints.
"""

import platform
import subprocess

from fastapi import APIRouter

from app.config import settings

router = APIRouter(prefix="/system", tags=["system"])


def get_command_version(command: list[str]) -> str | None:
    """Get version output from a command"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


@router.get("/info")
async def get_system_info():
    """Get system information for display in settings"""
    # Get Git version
    git_version = get_command_version(["git", "--version"])
    if git_version and git_version.startswith("git version "):
        git_version = git_version.replace("git version ", "")

    # Check Git LFS
    git_lfs_version = get_command_version(["git", "lfs", "version"])
    git_lfs_installed = bool(git_lfs_version)

    # Get Node version
    node_version = get_command_version(["node", "--version"])
    if node_version and node_version.startswith("v"):
        node_version = node_version[1:]  # Remove 'v' prefix

    # Get Docker version
    docker_version = get_command_version(["docker", "--version"])
    if docker_version and docker_version.startswith("Docker version "):
        docker_version = docker_version.replace("Docker version ", "").split(",")[0]

    # Check GPU support (simplified check)
    gpu_support = False
    try:
        # Check for NVIDIA GPU
        nvidia_smi = get_command_version(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"]
        )
        if nvidia_smi:
            gpu_support = True
    except Exception:
        pass

    return {
        "version": settings.version,
        "pythonVersion": platform.python_version(),
        "nodeVersion": node_version,
        "platform": f"{platform.system()} {platform.release()}",
        "gitVersion": git_version,
        "gitLFSInstalled": git_lfs_installed,
        "dockerVersion": docker_version,
        "workspacePath": str(settings.workspace_root),
        "apiEndpoint": f"http://localhost:{settings.port}",
        "gpuSupport": gpu_support,
    }
