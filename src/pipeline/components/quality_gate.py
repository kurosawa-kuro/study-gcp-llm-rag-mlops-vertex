from typing import NamedTuple

from kfp import dsl


@dsl.component(base_image="python:3.11-slim")
def quality_gate(
    rmse: float,
    rmse_threshold: float,
    model_gcs_path: str,
    discord_webhook_url: str,
) -> NamedTuple("Outputs", [("is_passed", str)]):
    """RMSE が閾値以下かを判定する品質ゲート。"""
    import json
    import urllib.request
    from collections import namedtuple

    def notify_discord(message: str, fields: list, color: int = 15158332):
        if not discord_webhook_url:
            return
        payload = {
            "embeds": [{
                "title": message,
                "color": color,
                "fields": fields,
            }]
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            discord_webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req)

    is_passed = rmse <= rmse_threshold

    if is_passed:
        print(f"品質ゲート合格: RMSE={rmse:.4f} <= 閾値{rmse_threshold:.4f}")
    else:
        print(f"品質ゲート不合格: RMSE={rmse:.4f} > 閾値{rmse_threshold:.4f}")
        notify_discord(
            "品質ゲート不合格",
            [
                {"name": "RMSE", "value": f"{rmse:.4f}", "inline": True},
                {"name": "閾値", "value": f"{rmse_threshold:.4f}", "inline": True},
                {"name": "モデル", "value": model_gcs_path, "inline": False},
            ],
            color=16776960,  # 黄
        )

    Outputs = namedtuple("Outputs", ["is_passed"])
    return Outputs(is_passed="true" if is_passed else "false")
