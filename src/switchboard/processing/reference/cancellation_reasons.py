import xml.etree.ElementTree as ET
import psycopg


def CancellationReason(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    with conn.cursor() as cursor:
        reason_code = xml_element.attrib.get("code")
        reason_text = xml_element.attrib.get("reasontext")

        cursor.execute(
            """
            INSERT INTO cancellation_reasons (
                reason_code,
                reason_text
            )
            VALUES (%s, %s)
            ON CONFLICT (reason_code)
            DO UPDATE SET
                reason_text = EXCLUDED.reason_text
            """,
            (reason_code, reason_text),
        )
