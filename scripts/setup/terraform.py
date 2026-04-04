"""Terraform インストール・初期設定

Usage: python scripts/setup/terraform.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "shared"))

from core import run


def main() -> None:
    print("=== Terraform インストール ===")
    run("wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg")
    run('echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list')
    run("sudo apt-get update && sudo apt-get install -y terraform")
    run("terraform version")
    print("Terraform インストール完了")


if __name__ == "__main__":
    main()
