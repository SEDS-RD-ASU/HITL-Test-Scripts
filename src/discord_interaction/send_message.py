import json
import logging
import os
import urllib.error
import urllib.request
from typing import BinaryIO


logger = logging.getLogger(name=__name__)

def _commit_link() -> str:
    return f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/blob/{os.environ['GITHUB_SHA']}"


def _multipart_payload(message: str, plots: list[BinaryIO]) -> tuple[bytes, str]:
    boundary = "----HITLReportBoundary"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="payload_json"\r\n'
        "Content-Type: application/json\r\n\r\n"
        f"{json.dumps({'content': message})}\r\n"
    ).encode()

    for index, plot in enumerate(plots):
        filename = getattr(plot, "name", f"plot_{index}.png")
        body += (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="files[{index}]"; filename="{filename}"\r\n'
            "Content-Type: image/png\r\n\r\n"
        ).encode()
        body += plot.read()
        body += b"\r\n"

    body += f"\r\n--{boundary}--\r\n".encode("ascii")
    return body, boundary



def send_message(plot_paths: list[BinaryIO], skipped: int, webhook_url: str | None) -> None:
    if webhook_url is None:
        logger.warning("No Discord webhook URL provided. Skipping report sending.")
        return

    message = (
        f"HITL run complete\n"
        f"Firmware commit: [{os.environ['GITHUB_SHA']}]({_commit_link()})\n"
        f"Skipped packets: {skipped}"
    )
    body, boundary = _multipart_payload(message, plot_paths)
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
