from __future__ import annotations

import xml.etree.ElementTree as ET
import psycopg

LOCATION_TAGS = {"or", "opor", "ip", "opip", "pp", "dt", "opdt"}


def _local(tag: str) -> str:
    return tag.split("}")[-1].lower()


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() == "true"


def Schedule(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    attrs = {k.lower(): v for k, v in xml_element.attrib.items()}

    rid = attrs.get("rid")
    uid = attrs.get("uid")
    train_id = attrs.get("trainid")
    ssd = attrs.get("ssd")
    toc = attrs.get("toc")

    if not (rid and uid and train_id and ssd and toc):
        return

    cancel_reason_code = attrs.get("cancreason")
    diverted_via = None
    diversion_reason_code = None
    diversion_reason_tiploc = None
    diversion_reason_near = None

    for child in xml_element:
        tag = _local(child.tag)
        if tag == "divertedvia":
            diverted_via = (child.text or "").strip() or None
        elif tag == "diversionreason":
            diversion_reason_code = (child.text or "").strip() or None
            c_attrs = {k.lower(): v for k, v in child.attrib.items()}
            diversion_reason_tiploc = c_attrs.get("tiploc")
            diversion_reason_near = _bool(c_attrs.get("near"))
        elif tag in ("cancelreason", "cancreason"):
            cancel_reason_code = (child.text or "").strip() or cancel_reason_code

    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO schedules (
                rid, uid, train_id, ssd, toc, status, train_cat,
                is_passenger_svc, deleted, is_charter, qtrain, can,
                cancel_reason_code, rsid, is_active,
                diverted_via, diversion_reason_code,
                diversion_reason_tiploc, diversion_reason_near
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (rid) DO UPDATE SET
                uid = EXCLUDED.uid,
                train_id = EXCLUDED.train_id,
                ssd = EXCLUDED.ssd,
                toc = EXCLUDED.toc,
                status = EXCLUDED.status,
                train_cat = EXCLUDED.train_cat,
                is_passenger_svc = EXCLUDED.is_passenger_svc,
                deleted = EXCLUDED.deleted,
                is_charter = EXCLUDED.is_charter,
                qtrain = EXCLUDED.qtrain,
                can = EXCLUDED.can,
                cancel_reason_code = EXCLUDED.cancel_reason_code,
                rsid = EXCLUDED.rsid,
                is_active = EXCLUDED.is_active,
                diverted_via = EXCLUDED.diverted_via,
                diversion_reason_code = EXCLUDED.diversion_reason_code,
                diversion_reason_tiploc = EXCLUDED.diversion_reason_tiploc,
                diversion_reason_near = EXCLUDED.diversion_reason_near;
            """,
            (
                rid,
                uid,
                train_id,
                ssd,
                toc,
                attrs.get("status", "P"),
                attrs.get("traincat", "OO"),
                _bool(attrs.get("ispassengersvc"), True),
                _bool(attrs.get("deleted")),
                _bool(attrs.get("ischarter")),
                _bool(attrs.get("qtrain")),
                _bool(attrs.get("can")),
                cancel_reason_code,
                attrs.get("rsid"),
                _bool(attrs.get("isactive"), True),
                diverted_via,
                diversion_reason_code,
                diversion_reason_tiploc,
                diversion_reason_near,
            ),
        )

        cursor.execute("DELETE FROM schedule_locations WHERE rid = %s;", (rid,))

        seq = 0
        loc_rows = []
        for child in xml_element:
            tag = _local(child.tag)
            if tag not in LOCATION_TAGS:
                continue

            c_attrs = {k.lower(): v for k, v in child.attrib.items()}
            tpl = c_attrs.get("tpl")
            if not tpl:
                continue

            loc_cancel_reason = c_attrs.get("canreason")
            for loc_child in child:
                if _local(loc_child.tag) in ("cancelreason", "canreason"):
                    loc_cancel_reason = (
                        loc_child.text or ""
                    ).strip() or loc_cancel_reason

            seq += 1
            loc_rows.append(
                (
                    rid,
                    tag,
                    tpl,
                    c_attrs.get("act", "  "),
                    c_attrs.get("planact"),
                    _bool(c_attrs.get("can")),
                    c_attrs.get("plat"),
                    c_attrs.get("wta"),
                    c_attrs.get("wtd"),
                    c_attrs.get("wtp"),
                    c_attrs.get("pta"),
                    c_attrs.get("ptd"),
                    c_attrs.get("fd"),
                    c_attrs.get("rdelay", 0),
                    seq,
                    c_attrs.get("fid"),
                    c_attrs.get("avgloading"),
                    loc_cancel_reason,
                    _bool(c_attrs.get("affectedbydiversion")),
                )
            )

        if loc_rows:
            with cursor.copy("""
                COPY schedule_locations (
                    rid, loc_type, tpl, act, plan_act, can, plat,
                    wta, wtd, wtp, pta, ptd, fd, rdelay, seq,
                    fid, avg_loading, cancel_reason_code, affected_by_diversion
                ) FROM STDIN
                """) as copy:
                for row in loc_rows:
                    copy.write_row(row)
