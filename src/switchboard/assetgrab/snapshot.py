import os
import time
import xml.etree.ElementTree as ET
from switchboard.assetgrab.util import download_snapshot_file
from switchboard.util import load_config_item
from datetime import datetime, timezone


def acquire_latest_snapshot() -> list[ET.Element] | None:
    url = load_config_item("snapshot", "snapshot_url", str)
    request_period = load_config_item("snapshot", "snapshot_request_period", int)
    request_max_attempts = load_config_item(
        "snapshot", "snapshot_request_max_attempts", int
    )

    now = datetime.now(timezone.utc)

    payload = {
        "date": f"{now.year}-{now.month:02d}-{now.day:02d}",
        "hour": f"{now.hour:02d}",
    }

    api_key = os.getenv("SNAPSHOT_API_KEY")
    if api_key == None:
        raise Exception("snapshot api key is missing")

    headers = {
        "x-apikey": api_key,
        "User-agent": "RDG",
        "Content-Type": "application/json",
    }

    snapshot_response = None
    attempts = 0

    while snapshot_response == None and attempts <= request_max_attempts:
        attempts += 1
        snapshot_response = download_snapshot_file(url, headers, payload)

        if snapshot_response == None:
            time.sleep(request_period)

    return snapshot_response
