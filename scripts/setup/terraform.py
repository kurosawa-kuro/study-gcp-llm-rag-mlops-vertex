"""Terraform インストール・初期設定（未インストール時のみ）

Usage: python3 scripts/setup/terraform.py
"""

import shutil
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "shared"))

from core import run


def main() -> None:
    if shutil.which("terraform"):
        print(f"terraform 既にインストール済み: {shutil.which('terraform')}")
        run("terraform version", capture=True)
        print("スキップ。再インストールが必要な場合は --force オプションを使用してください。")
        if "--force" not in sys.argv:
            return

    print("=== Terraform インストール ===")

    gpg_key = "/usr/share/keyrings/hashicorp-archive-keyring.gpg"
    apt_list = "/etc/apt/sources.list.d/hashicorp.list"

    run(f"sudo rm -f {gpg_key}")
    run(f"wget -qO- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o {gpg_key}")
    run(f'grep -q "hashicorp" {apt_list} 2>/dev/null || echo "deb [signed-by={gpg_key}] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee {apt_list}')
    run("sudo apt-get update && sudo apt-get install -y terraform")
    run("terraform version")
    print("Terraform インストール完了")


if __name__ == "__main__":
    main()
