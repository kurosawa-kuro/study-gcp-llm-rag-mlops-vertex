"""Elastic Cloud 接続確認用 Docker操作"""
import subprocess
from pathlib import Path

from es_config import JOB_NAME, IMAGE_URI
from core import dispatch

ES_DIR = str(Path(__file__).resolve().parent.parent / "src" / "elastic-search")


def build() -> None:
    subprocess.run(["docker", "build", "-t", JOB_NAME, "."], cwd=ES_DIR, check=True)


def build_gcr() -> None:
    subprocess.run(["docker", "build", "-t", IMAGE_URI, "."], cwd=ES_DIR, check=True)


def push() -> None:
    build_gcr()
    subprocess.run(["docker", "push", IMAGE_URI], check=True)


def docker_run() -> None:
    build()
    env_file = str(Path(ES_DIR) / ".env")
    subprocess.run(["docker", "run", "--env-file", env_file, JOB_NAME], check=True)


def clean() -> None:
    subprocess.run(["docker", "rmi", JOB_NAME], check=False)


if __name__ == "__main__":
    dispatch({
        "build": build,
        "build-gcr": build_gcr,
        "push": push,
        "docker-run": docker_run,
        "clean": clean,
    })
