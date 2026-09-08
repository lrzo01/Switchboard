import xml.etree.ElementTree as ET
import psycopg


def CISSource(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    with conn.cursor() as cursor:
        code = xml_element.attrib.get("code")
        name = xml_element.attrib.get("name")

        cursor.execute(
            """
            INSERT INTO cis_sources (
                code,
                name
            )
            VALUES (%s, %s)
            ON CONFLICT (code)
            DO UPDATE SET
                name = EXCLUDED.name
            """,
            (code, name),
        )
