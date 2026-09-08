from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TypedDict

import psycopg


def _local(tag: str) -> str:
    return tag.split("}")[-1].lower()


def _bool(text: str | None) -> bool:
    return (text or "").strip().lower() == "true"


class AlertService(TypedDict):
    rid: str | None
    uid: str | None
    ssd: str | None
    locations: list[str]


def TrainAlert(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    alert_id: str | None = None
    source: str | None = None
    alert_text: str | None = None
    audience: str | None = None
    alert_type: str | None = None
    copied_from_alert_id: str | None = None
    copied_from_source: str | None = None
    send_sms = False
    send_email = False
    send_twitter = False
    services: list[AlertService] = []

    for child in xml_element:
        tag = _local(child.tag)
        text = (child.text or "").strip()

        if tag == "alertid":
            alert_id = text
        elif tag == "source":
            source = text
        elif tag == "alerttext":
            alert_text = text
        elif tag == "audience":
            audience = text
        elif tag == "alerttype":
            alert_type = text
        elif tag in ("sendalertbysms", "sendalert"):
            send_sms = _bool(text)
        elif tag == "sendalertbyemail":
            send_email = _bool(text)
        elif tag == "sendalertbytwitter":
            send_twitter = _bool(text)
        elif tag == "copiedfromalertid":
            copied_from_alert_id = text
        elif tag == "copiedfromsource":
            copied_from_source = text
        elif tag in ("alertservices", "services"):
            for service in child:
                if _local(service.tag) not in ("alertservice", "service"):
                    continue
                s_attrs = {k.lower(): v for k, v in service.attrib.items()}
                locations: list[str] = [
                    (loc.text or "").strip()
                    for loc in service
                    if _local(loc.tag) == "location" and (loc.text or "").strip()
                ]
                entry: AlertService = {
                    "rid": s_attrs.get("rid"),
                    "uid": s_attrs.get("uid"),
                    "ssd": s_attrs.get("ssd"),
                    "locations": locations,
                }
                services.append(entry)

    if not (alert_id and source and alert_text):
        return

    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO train_alerts (
                alert_id, source, alert_text, audience, alert_type,
                send_by_sms, send_by_email, send_by_twitter,
                copied_from_alert_id, copied_from_source
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (alert_id) DO UPDATE SET
                source = EXCLUDED.source,
                alert_text = EXCLUDED.alert_text,
                audience = EXCLUDED.audience,
                alert_type = EXCLUDED.alert_type,
                send_by_sms = EXCLUDED.send_by_sms,
                send_by_email = EXCLUDED.send_by_email,
                send_by_twitter = EXCLUDED.send_by_twitter,
                copied_from_alert_id = EXCLUDED.copied_from_alert_id,
                copied_from_source = EXCLUDED.copied_from_source;
            """,
            (
                alert_id,
                source,
                alert_text,
                audience,
                alert_type,
                send_sms,
                send_email,
                send_twitter,
                copied_from_alert_id,
                copied_from_source,
            ),
        )

        cursor.execute(
            "DELETE FROM train_alert_services WHERE alert_id = %s;", (alert_id,)
        )

        for service_entry in services:
            cursor.execute(
                """
                INSERT INTO train_alert_services (alert_id, uid, ssd)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (alert_id, service_entry["uid"], service_entry["ssd"]),
            )
            result = cursor.fetchone()
            if result is None:
                continue
            service_row_id: int = result[0]

            for seq, crs in enumerate(service_entry["locations"], start=1):
                cursor.execute(
                    """
                    INSERT INTO train_alert_locations (alert_service_id, crs, seq)
                    VALUES (%s, %s, %s);
                    """,
                    (service_row_id, crs, seq),
                )
