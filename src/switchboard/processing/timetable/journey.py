import xml.etree.ElementTree as ET
import psycopg


def Journey(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    attrs = {k.lower(): v for k, v in xml_element.attrib.items()}

    rid = attrs.get("rid")
    uid = attrs.get("uid")
    train_id = attrs.get("trainid")
    ssd = attrs.get("ssd")
    toc = attrs.get("toc")

    if not rid or not uid or not train_id or not ssd or not toc:
        return

    status = attrs.get("status", "P")
    train_cat = attrs.get("traincat", "OO")
    is_passenger_svc = attrs.get("ispassengersvc", "true").lower() == "true"
    deleted = attrs.get("deleted", "false").lower() == "true"
    is_charter = attrs.get("ischarter", "false").lower() == "true"
    qtrain = attrs.get("qtrain", "false").lower() == "true"
    can = attrs.get("can", "false").lower() == "true"

    cancel_reason = None
    for child in xml_element:
        if child.tag.split("}")[-1].lower() == "cancelreason":
            cancel_reason = child.attrib.get("code") or child.text

    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO schedules (
                rid, uid, train_id, ssd, toc, status, train_cat,
                is_passenger_svc, deleted, is_charter, qtrain, can, cancel_reason_code
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (rid)
            DO UPDATE SET
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
                cancel_reason_code = EXCLUDED.cancel_reason_code;
            """,
            (
                rid,
                uid,
                train_id,
                ssd,
                toc,
                status,
                train_cat,
                is_passenger_svc,
                deleted,
                is_charter,
                qtrain,
                can,
                cancel_reason,
            ),
        )

        cursor.execute("DELETE FROM schedule_locations WHERE rid = %s;", (rid,))

        seq = 1
        loc_rows = []
        for child in xml_element:
            loc_type = child.tag.split("}")[-1]
            if loc_type not in ("OR", "OPOR", "IP", "OPIP", "PP", "DT", "OPDT"):
                continue

            c_attrs = {k.lower(): v for k, v in child.attrib.items()}
            loc_rows.append(
                (
                    rid,
                    loc_type,
                    c_attrs.get("tpl"),
                    c_attrs.get("act", "  "),
                    c_attrs.get("planact"),
                    c_attrs.get("can", "false").lower() == "true",
                    c_attrs.get("plat"),
                    c_attrs.get("wta"),
                    c_attrs.get("wtd"),
                    c_attrs.get("wtp"),
                    c_attrs.get("pta"),
                    c_attrs.get("ptd"),
                    c_attrs.get("fd"),
                    int(c_attrs.get("rdelay", 0)),
                    seq,
                )
            )
            seq += 1

        if loc_rows:
            with cursor.copy("""
                COPY schedule_locations (
                    rid, loc_type, tpl, act, plan_act, can, plat,
                    wta, wtd, wtp, pta, ptd, fd, rdelay, seq
                ) FROM STDIN
                """) as copy:
                for row in loc_rows:
                    copy.write_row(row)
