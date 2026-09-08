import xml.etree.ElementTree as ET
import psycopg


def TocRef(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    with conn.cursor() as cursor:
        toc = xml_element.attrib.get("toc")
        toc_name = xml_element.attrib.get("tocname")
        url = xml_element.attrib.get("url")

        cursor.execute(
            """
            INSERT INTO toc_refs (
                toc,
                toc_name,
                url
            )
            VALUES (%s, %s, %s)
            ON CONFLICT (toc)
            DO UPDATE SET
                toc_name = EXCLUDED.toc_name,
                url = EXCLUDED.url
            """,
            (toc, toc_name, url),
        )
