from __future__ import annotations

import xml.etree.ElementTree as ET
import psycopg


def _local(tag: str) -> str:
    return tag.split("}")[-1].lower()


def StationInformation(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    attrs = {k.lower(): v for k, v in xml_element.attrib.items()}
    crs = attrs.get("crs")
    if not crs:
        return

    current_lift_ids: list[str] = []

    with conn.cursor() as cursor:
        for child in xml_element:
            if _local(child.tag) != "liftstatus":
                continue

            c_attrs = {k.lower(): v for k, v in child.attrib.items()}
            lift_id = c_attrs.get("liftid")
            if not lift_id:
                continue

            current_lift_ids.append(lift_id)
            cursor.execute(
                """
                INSERT INTO station_lift_status (crs, lift_id, status, description)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT ON CONSTRAINT uq_station_lift_status
                DO UPDATE SET status = EXCLUDED.status, description = EXCLUDED.description;
                """,
                (
                    crs,
                    lift_id,
                    c_attrs.get("status", "OutOfService"),
                    (child.text or "").strip() or None,
                ),
            )

        if current_lift_ids:
            cursor.execute(
                "DELETE FROM station_lift_status WHERE crs = %s AND lift_id NOT IN %s;",
                (crs, tuple(current_lift_ids)),
            )
        else:
            cursor.execute("DELETE FROM station_lift_status WHERE crs = %s;", (crs,))
