from typing import TYPE_CHECKING
import switchboard.assetgrab as assetgrab
import xml.etree.ElementTree as ET

if TYPE_CHECKING:
    import switchboard.processing.processing as processing


def load_timetable_ref_file(processor: "processing.Processing") -> None:
    timetable_ref_file: ET.Element = assetgrab.acquire_latest_timetable_reference()
    processor.process([timetable_ref_file])


def load_snapshot_file(processor: "processing.Processing") -> None:
    snapshot_file: list[ET.Element] | None = assetgrab.acquire_latest_snapshot()
    if snapshot_file:
        processor.process(snapshot_file)


def load_timetable_file(processor: "processing.Processing"):
    timetable_file: ET.Element = assetgrab.acquire_latest_timetable()
    processor.process([timetable_file])


def populate(processor: "processing.Processing"):
    print("populating database, standby")
    load_timetable_ref_file(processor)
    load_timetable_file(processor)
    load_snapshot_file(processor)
    print("database populated using static timetable files and snapshots")
