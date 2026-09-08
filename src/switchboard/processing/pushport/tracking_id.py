from __future__ import annotations

import xml.etree.ElementTree as ET
import psycopg


def _local(tag: str) -> str:
    return tag.split("}")[-1].lower()


def TrackingID(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    attrs = {k.lower(): v for k, v in xml_element.attrib.items()}

    berth = attrs.get("berth") or attrs.get("tdberth")
    td_area = attrs.get("tdareaid") or attrs.get("area")
    incorrect_id = (
        attrs.get("incorrecttrackingid")
        or attrs.get("wrongheadcode")
        or attrs.get("from")
    )
    correct_id = (
        attrs.get("correcttrackingid") or attrs.get("headcode") or attrs.get("to")
    )

    for child in xml_element:
        tag = _local(child.tag)
        text = (child.text or "").strip()
        c_attrs = {k.lower(): v for k, v in child.attrib.items()}

        if tag == "berth":
            berth = text or berth
            td_area = c_attrs.get("area") or td_area
        elif tag in ("incorrecttrainid", "incorrecttrackingid"):
            incorrect_id = text or incorrect_id
        elif tag in ("correcttrainid", "correcttrackingid"):
            correct_id = text or correct_id

    if not (berth and correct_id):
        return

    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO tracking_id_corrections (
                berth, td_area, incorrect_tracking_id, correct_tracking_id
            )
            VALUES (%s, %s, %s, %s);
            """,
            (berth, td_area, incorrect_id, correct_id),
        )
