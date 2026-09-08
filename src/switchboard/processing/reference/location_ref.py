import xml.etree.ElementTree as ET
import psycopg


def LocationRef(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    with conn.cursor() as cursor:
        tiploc = xml_element.attrib.get("tpl")
        crs = xml_element.attrib.get("crs")
        toc = xml_element.attrib.get("toc")
        location_name = xml_element.attrib.get("locname")

        cursor.execute(
            """
            INSERT INTO location_refs (
                tiploc,
                crs,
                toc,
                location_name
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (tiploc)
            DO UPDATE SET
                crs = EXCLUDED.crs,
                toc = EXCLUDED.toc,
                location_name = EXCLUDED.location_name
            """,
            (tiploc, crs, toc, location_name),
        )
