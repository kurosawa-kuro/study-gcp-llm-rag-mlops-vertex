"""GCP CLI インストール・初期設定（未インストール時のみ）

Usage: python3 scripts/setup/gcp.py
"""

import shutil
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "shared"))

from core import run


def main() -> None:
    if shutil.which("gcloud"):
        print(f"gcloud 既にインストール済み: {shutil.which('gcloud')}")
        run("gcloud version", capture=True)
        print("スキップ。再インストールが必要な場合は --force オプションを使用してください。")
        if "--force" not in sys.argv:
            return

    print("=== GCP CLI インストール ===")
    run("sudo apt-get update -y")
    run("sudo apt-get install -y ca-certificates gnupg curl")

    gpg_key = "/usr/share/keyrings/cloud.google.gpg"
    apt_list = "/etc/apt/sources.list.d/google-cloud-sdk.list"

    run(f"sudo rm -f {gpg_key}")
    run(f"curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o {gpg_key}")
    run(f'grep -q "cloud-sdk" {apt_list} 2>/dev/null || echo "deb [signed-by={gpg_key}] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee {apt_list}')
    run("sudo apt-get update && sudo apt-get install -y google-cloud-cli")
    print("gcloud CLI インストール完了。次に 'gcloud init' を実行してください。")


if __name__ == "__main__":
    main()
