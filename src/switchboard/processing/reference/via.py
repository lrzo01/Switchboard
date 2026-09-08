import xml.etree.ElementTree as ET
import psycopg


def Via(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    with conn.cursor() as cursor:
        at = xml_element.attrib.get("at")
        destination = xml_element.attrib.get("dest")
        loc1 = xml_element.attrib.get("loc1")
        loc2 = xml_element.attrib.get("loc2")
        via_text = xml_element.attrib.get("viatext")

        cursor.execute(
            """
            INSERT INTO via_points (
                at,
                destination,
                loc1,
                loc2,
                via_text
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT uq_via_points
            DO UPDATE SET
                via_text = EXCLUDED.via_text
            """,
            (at, destination, loc1, loc2, via_text),
        )
