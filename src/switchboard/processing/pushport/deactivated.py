from __future__ import annotations

import xml.etree.ElementTree as ET
import psycopg


def Deactivated(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    attrs = {k.lower(): v for k, v in xml_element.attrib.items()}
    rid = attrs.get("rid") or (xml_element.text or "").strip()
    if not rid:
        return

    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE schedules SET is_active = FALSE WHERE rid = %s;",
            (rid,),
        )
