import xml.etree.ElementTree as ET
import psycopg


def OW(conn: psycopg.Connection, xml_element: ET.Element):
    with conn.cursor() as cursor:
        station_message_id = xml_element.attrib.get("id")
        category = xml_element.attrib.get("cat")
        severity = xml_element.attrib.get("sev")

        suppress = xml_element.attrib.get("suppress", "false").lower() == "true"

        msg_element = xml_element.find("{*}Msg")

        message = None
        if msg_element is not None:
            tagged_msg = ET.tostring(msg_element, encoding="unicode").replace(
                "ns0:", ""
            )

            opening_tag_end = tagged_msg.find(">") + 1
            closing_tag_start = tagged_msg.rfind("</")

            message = tagged_msg[opening_tag_end:closing_tag_start].strip()

        cursor.execute(
            """
            INSERT INTO station_messages (
                station_message_id,
                msg,
                category,
                severity,
                suppress
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (station_message_id)
            DO UPDATE SET
                msg = EXCLUDED.msg,
                category = EXCLUDED.category,
                severity = EXCLUDED.severity,
                suppress = EXCLUDED.suppress
            """,
            (
                station_message_id,
                message,
                category,
                severity,
                suppress,
            ),
        )

        cursor.execute(
            """
            DELETE FROM station_messages_locations
            WHERE station_message_id = %s
            """,
            (station_message_id,),
        )

        stations = {
            station.attrib["crs"]
            for station in xml_element.findall("{*}Station")
            if station.attrib.get("crs")
        }

        cursor.executemany(
            """
            INSERT INTO station_messages_locations (
                station_message_id,
                crs
            )
            VALUES (%s, %s)
            """,
            ((station_message_id, crs) for crs in stations),
        )
