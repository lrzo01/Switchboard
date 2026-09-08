from __future__ import annotations

import xml.etree.ElementTree as ET
import psycopg


def _local(tag: str) -> str:
    return tag.split("}")[-1].lower()


def Alarm(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    with conn.cursor() as cursor:
        for child in xml_element:
            tag = _local(child.tag)
            c_attrs = {k.lower(): v for k, v in child.attrib.items()}

            if tag == "clear":
                alarm_id = (child.text or "").strip() or c_attrs.get("id")
                if not alarm_id:
                    continue
                cursor.execute(
                    """
                    UPDATE alarms
                    SET is_cleared = TRUE, cleared_at = now()
                    WHERE alarm_id = %s;
                    """,
                    (alarm_id,),
                )
                continue

            if tag == "set":
                alarm_id = c_attrs.get("id")
                for inner in child:
                    inner_tag = _local(inner.tag)
                    if inner_tag in (
                        "tdareafail",
                        "tdfeedfail",
                        "tyrellfeedfail",
                        "tdareafailure",
                        "tdfeedfailure",
                        "tyrellfeedfailure",
                    ):
                        td_area = (
                            (inner.text or "").strip()
                            or inner.attrib.get("tdAreaID")
                            or inner.attrib.get("tdareaid")
                            or None
                        )
                        if not alarm_id:
                            alarm_id = f"{inner_tag}:{td_area or ''}"
                        cursor.execute(
                            """
                            INSERT INTO alarms (alarm_id, alarm_type, td_area, is_cleared)
                            VALUES (%s, %s, %s, FALSE)
                            ON CONFLICT (alarm_id) DO UPDATE SET
                                alarm_type = EXCLUDED.alarm_type,
                                td_area = EXCLUDED.td_area,
                                is_cleared = FALSE,
                                cleared_at = NULL;
                            """,
                            (alarm_id, inner_tag, td_area),
                        )
