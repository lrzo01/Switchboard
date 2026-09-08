from switchboard.assetgrab.util import (
    get_timetable_directory_contents,
    timestamp_sanity_check,
    load_xml_by_file_name,
)
import xml.etree.ElementTree as ET


def retrieve_timetable_item(find_string: str) -> ET.Element:
    timetable_files = get_timetable_directory_contents()
    ref_files: list[str] = []

    for timetable in timetable_files:
        if find_string in timetable:
            ref_files.append(timetable)

    newest_ref = None

    for reference_file in ref_files:
        timestamp = reference_file[12:26]

        if newest_ref == None:
            newest_ref = reference_file

        newest_ref_timestamp = newest_ref[12:26]

        if newest_ref_timestamp < timestamp:
            newest_ref = reference_file

    if newest_ref == None:
        raise FileNotFoundError("no timetable file could be found")

    timestamp_sanity_check(newest_ref[12:26])
    return load_xml_by_file_name(newest_ref)


def acquire_latest_timetable() -> ET.Element:
    return retrieve_timetable_item("_v8.xml")


def acquire_latest_timetable_reference() -> ET.Element:
    return retrieve_timetable_item("_ref_v4.xml")
