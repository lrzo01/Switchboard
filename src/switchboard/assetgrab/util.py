import requests
import gzip
import os
import warnings
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from switchboard.util import load_config_item, parse_pport_into_loadable_xml


def download_snapshot_file(
    url: str, headers: dict[str, str], payload: dict[str, str]
) -> list[ET.Element] | None:
    request = requests.post(url, headers=headers, json=payload)

    if request.status_code == 200:
        response = request.json()

        if len(response) == 1:
            temp_url = response[0]
            actual_response = requests.get(temp_url)

            if actual_response.status_code == 200:
                decompressed = gzip.decompress(actual_response.content)
                decoded = decompressed.decode("utf-8")
                return parse_pport_into_loadable_xml(decoded)


def get_timetable_directory_contents() -> list[str]:
    file_directory = load_config_item("darwin", "timetable_file_path", str)
    return os.listdir(file_directory)


def timestamp_sanity_check(timestamp: str) -> None:
    now = datetime.now(timezone.utc)
    warn_about_old_timetables = load_config_item(
        "darwin", "warn_about_old_timetables", bool
    )

    try:
        timestamp_dt = datetime.strptime(str(timestamp), "%Y%m%d%H%M%S").replace(
            tzinfo=timezone.utc
        )
        age_of_timetable = now - timestamp_dt

        if age_of_timetable > timedelta(hours=24.2) and warn_about_old_timetables:
            warnings.warn(
                "new timetable files should be available, you may be using an outdated timetable."
                "disable this behaviour in config.toml if incorrect"
            )

    except ValueError:
        print(f"could not parse timestamp")

def load_xml_by_file_name(name: str) -> ET.Element:
    file_directory = load_config_item("darwin", "timetable_file_path", str)
    file_path = os.path.join(file_directory, name)
    
    try:
        tree = ET.parse(file_path)
        return tree.getroot()
    except (FileNotFoundError, IsADirectoryError):
        raise FileNotFoundError(f"could not find timetable ref: {name}")
    except ET.ParseError:
        try:
            with gzip.open(file_path, 'rb') as f:
                tree = ET.parse(f)
                return tree.getroot()
        except Exception as e:
            raise RuntimeError(f"failed to open timetable (attempted gzip decompression) {name}: {e}")

