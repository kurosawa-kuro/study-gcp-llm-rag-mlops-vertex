"""GCP CLI インストール・初期設定

Usage: python scripts/setup/gcp.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "shared"))

from core import run


def main() -> None:
    print("=== GCP CLI インストール ===")
    run("sudo apt-get update -y")
    run("sudo apt-get install -y ca-certificates gnupg curl")
    run("curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg")
    run('echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list')
    run("sudo apt-get update && sudo apt-get install -y google-cloud-cli")
    print("gcloud CLI インストール完了。次に 'gcloud init' を実行してください。")


if __name__ == "__main__":
    main()
