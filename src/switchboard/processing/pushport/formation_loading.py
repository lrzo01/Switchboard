from __future__ import annotations

import xml.etree.ElementTree as ET
import psycopg


def _local(tag: str) -> str:
    return tag.split("}")[-1].lower()


def FormationLoading(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    attrs = {k.lower(): v for k, v in xml_element.attrib.items()}
    fid = attrs.get("fid")
    rid = attrs.get("rid")
    tpl = attrs.get("tpl")
    if not (fid and rid and tpl):
        return

    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO formation_loading (fid, rid, tpl, wta, wtd, wtp, pta, ptd)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT uq_formation_loading
            DO UPDATE SET fid = EXCLUDED.fid
            RETURNING id;
            """,
            (
                fid,
                rid,
                tpl,
                attrs.get("wta"),
                attrs.get("wtd"),
                attrs.get("wtp"),
                attrs.get("pta"),
                attrs.get("ptd"),
            ),
        )
        result = cursor.fetchone()
        if result is None:
            return
        loading_id: int = result[0]

        cursor.execute(
            "DELETE FROM formation_loading_coaches WHERE formation_loading_id = %s;",
            (loading_id,),
        )

        for loading in xml_element:
            if _local(loading.tag) != "loading":
                continue

            c_attrs = {k.lower(): v for k, v in loading.attrib.items()}
            coach_number = c_attrs.get("coachnumber")
            if not coach_number:
                continue

            loading_value = (loading.text or "").strip() or None

            cursor.execute(
                """
                INSERT INTO formation_loading_coaches (
                    formation_loading_id, coach_number, src, src_inst, loading_value
                )
                VALUES (%s, %s, %s, %s, %s);
                """,
                (
                    loading_id,
                    coach_number,
                    c_attrs.get("src"),
                    c_attrs.get("srcinst"),
                    loading_value,
                ),
            )
