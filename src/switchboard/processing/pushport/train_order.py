from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TypedDict

import psycopg


class TrainOrderEntry(TypedDict):
    rid: str | None
    train_id: str | None
    wta: str | None
    wtd: str | None
    wtp: str | None
    pta: str | None
    ptd: str | None


def _local(tag: str) -> str:
    return tag.split("}")[-1].lower()


def TrainOrder(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    def clean_attribs(elem: ET.Element) -> dict[str, str]:
        return {k.split("}")[-1].lower(): v for k, v in elem.attrib.items()}

    root_attrs = clean_attribs(xml_element)
    tiploc = root_attrs.get("tiploc")
    crs = root_attrs.get("crs")
    platform = root_attrs.get("platform")

    if not (tiploc and crs and platform):
        return

    # Check for <clear>
    for child in xml_element:
        if _local(child.tag) == "clear":
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM train_order WHERE tiploc = %s AND crs = %s;",
                    (tiploc, crs),
                )
            return

    entries: list[TrainOrderEntry] = []

    def parse_item(item_elem: ET.Element) -> TrainOrderEntry | None:
        rid: str | None = None
        train_id: str | None = None
        times_elem = item_elem

        for child in item_elem:
            ctag = _local(child.tag)
            if ctag == "rid":
                rid = (child.text or "").strip() or None
                times_elem = child
            elif ctag in ("trainid", "headcode"):
                train_id = (child.text or "").strip() or None

        c_attrs = clean_attribs(times_elem)
        if not (rid or train_id):
            rid = c_attrs.get("rid")
            train_id = c_attrs.get("trainid")

        if not (rid or train_id):
            return None

        return {
            "rid": rid,
            "train_id": train_id,
            "wta": c_attrs.get("wta"),
            "wtd": c_attrs.get("wtd"),
            "wtp": c_attrs.get("wtp"),
            "pta": c_attrs.get("pta"),
            "ptd": c_attrs.get("ptd"),
        }

    for child in xml_element:
        ctag = _local(child.tag)
        if ctag == "set":
            for rank_elem in child:
                entry = parse_item(rank_elem)
                if entry:
                    entries.append(entry)
        elif ctag in ("first", "second", "third"):
            entry = parse_item(child)
            if entry:
                entries.append(entry)

    entries = entries[:3]
    if not entries:
        return

    # 3. Database Upsert
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO train_order (tiploc, crs)
            VALUES (%s, %s)
            ON CONFLICT ON CONSTRAINT uq_train_order_platform
            DO UPDATE SET tiploc = EXCLUDED.tiploc
            RETURNING id;
            """,
            (tiploc, crs),
        )
        result = cursor.fetchone()
        if not result:
            return

        train_order_id: int = result[0]

        cursor.execute(
            "DELETE FROM train_order_entries WHERE train_order_id = %s;",
            (train_order_id,),
        )

        for order_rank, order_entry in enumerate(entries, start=1):
            cursor.execute(
                """
                INSERT INTO train_order_entries (
                    train_order_id, order_rank, rid, train_id, wta, wtd, wtp, pta, ptd
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    train_order_id,
                    order_rank,
                    order_entry["rid"],
                    order_entry["train_id"],
                    order_entry["wta"],
                    order_entry["wtd"],
                    order_entry["wtp"],
                    order_entry["pta"],
                    order_entry["ptd"],
                ),
            )
