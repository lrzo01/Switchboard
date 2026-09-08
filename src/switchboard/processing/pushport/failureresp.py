import xml.etree.ElementTree as ET
import psycopg
from datetime import timezone, datetime


def FailureResp(conn: psycopg.Connection, xml_element: ET.Element):
    with conn.cursor() as cursor:
        code = xml_element.attrib.get("code")
        message = xml_element.text
        now = datetime.now(timezone.utc)
        if message:
            message.strip()

        if message != "Darwin Status Response":
            # we do this to prevent unnecessary status updates being added to the database
            cursor.execute(
                """
                INSERT INTO system_status_logs (
                    status_timestamp,
                    status_code,
                    status_message
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (status_timestamp)
                DO UPDATE SET
                    status_code = EXCLUDED.status_code,
                    status_message = EXCLUDED.status_message
                """,
                (now, code, message),
            )
