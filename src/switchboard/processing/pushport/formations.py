from __future__ import annotations

import xml.etree.ElementTree as ET
import psycopg


def _local(tag: str) -> str:
    return tag.split("}")[-1].lower()


def ScheduleFormations(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    attrs = {k.lower(): v for k, v in xml_element.attrib.items()}
    rid = attrs.get("rid")
    if not rid:
        return

    with conn.cursor() as cursor:
        for formation in xml_element:
            if _local(formation.tag) != "formation":
                continue
            _process_formation(cursor, rid, formation)


def _process_formation(cursor: psycopg.Cursor, rid: str, formation: ET.Element) -> None:
    f_attrs = {k.lower(): v for k, v in formation.attrib.items()}
    fid = f_attrs.get("fid")
    if not fid:
        return

    cursor.execute(
        """
        INSERT INTO train_formations (fid, rid, src, src_inst)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (fid) DO UPDATE SET
            rid = EXCLUDED.rid,
            src = EXCLUDED.src,
            src_inst = EXCLUDED.src_inst;
        """,
        (fid, rid, f_attrs.get("src"), f_attrs.get("srcinst")),
    )

    cursor.execute("DELETE FROM formation_coaches WHERE fid = %s;", (fid,))

    coaches_el = next(
        (child for child in formation if _local(child.tag) == "coaches"), None
    )
    if coaches_el is None:
        return

    seq = 0
    for coach in coaches_el:
        if _local(coach.tag) != "coach":
            continue

        c_attrs = {k.lower(): v for k, v in coach.attrib.items()}
        coach_number = c_attrs.get("coachnumber")
        if not coach_number:
            continue

        seq += 1
        toilet_availability = "Unknown"
        toilet_status = "Unknown"
        for toilet in coach:
            if _local(toilet.tag) == "toilet":
                toilet_availability = (toilet.text or "").strip() or "Unknown"
                t_attrs = {k.lower(): v for k, v in toilet.attrib.items()}
                toilet_status = t_attrs.get("status", "Unknown")

        cursor.execute(
            """
            INSERT INTO formation_coaches (
                fid, coach_number, coach_class, toilet_availability, toilet_status, seq
            )
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            (
                fid,
                coach_number,
                c_attrs.get("coachclass"),
                toilet_availability,
                toilet_status,
                seq,
            ),
        )
