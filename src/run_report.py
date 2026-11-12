import csv
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


FIRMWARE_DIR = Path(
    os.environ.get("FIRMWARE_DIR", "/home/hitl/ascent-r3-firmware")
)


def _read_timestamps(dump_path: Path) -> list[tuple[int, int]]:
    packets = []
    with dump_path.open(newline="", encoding="utf-8") as dump_file:
        for row in csv.reader(dump_file):
            if len(row) < 2 or row[0].strip() == "n":
                continue
            try:
                packets.append((int(row[0]), int(row[1])))
            except ValueError:
                continue
    return packets


def _commit_link() -> str:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=FIRMWARE_DIR,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    remote = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=FIRMWARE_DIR,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if remote.startswith("git@github.com:"):
        remote = "https://github.com/" + remote.removeprefix("git@github.com:")
    remote = remote.removesuffix(".git")
    return f"{remote}/commit/{commit}"


def create_run_report(dump_path: Path) -> tuple[Path, int, str]:
    packets = _read_timestamps(dump_path)
    if not packets:
        raise RuntimeError(f"No valid packet timestamps found in {dump_path}.")

    skipped = sum(
        max(current_n - previous_n - 1, 0)
        for (previous_n, _), (current_n, _) in zip(packets, packets[1:])
    )
    delta_t = [
        (current_n, current_timestamp - previous_timestamp)
        for (previous_n, previous_timestamp), (current_n, current_timestamp)
        in zip(packets, packets[1:])
        if current_n > previous_n
    ]
    if not delta_t:
        raise RuntimeError(f"Not enough packet timestamps found in {dump_path}.")

    plot_path = dump_path.with_suffix(".dt.png")
    x_values, dt_values = zip(*delta_t)
    figure, axis = plt.subplots(figsize=(12, 6))
    axis.scatter(x_values, dt_values, s=4)
    axis.set_title("Delta T")
    axis.set_xlabel("Packet number")
    axis.set_ylabel("Delta T (microseconds)")
    axis.grid(True)
    figure.tight_layout()
    figure.savefig(plot_path, dpi=150)
    plt.close(figure)
    return plot_path, skipped, _commit_link()


def _multipart_payload(message: str, plot_path: Path) -> tuple[bytes, str]:
    boundary = "----HITLReportBoundary"
    parts = [
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="payload_json"\r\n'
        "Content-Type: application/json\r\n\r\n"
        f"{json.dumps({'content': message})}\r\n",
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="files[0]"; filename="{plot_path.name}"\r\n'
        "Content-Type: image/png\r\n\r\n",
    ]
    body = parts[0].encode("utf-8") + parts[1].encode("utf-8")
    body += plot_path.read_bytes()
    body += f"\r\n--{boundary}--\r\n".encode("ascii")
    return body, boundary


def send_run_report(plot_path: Path, skipped: int, commit_link: str) -> None:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError("DISCORD_WEBHOOK_URL is not set; cannot send HITL report.")

    message = (
        f"HITL run complete\n"
        f"Firmware commit: {commit_link}\n"
        f"Skipped packets: {skipped}"
    )
    body, boundary = _multipart_payload(message, plot_path)
    request = urllib.request.Request(
        webhook_url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "HITL-Test-Scripts/1.0",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30):
            pass
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Discord rejected the webhook ({error.code}): {details}"
        ) from error
