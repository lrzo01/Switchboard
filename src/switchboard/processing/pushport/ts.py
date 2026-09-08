from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import psycopg
from psycopg import sql


def _local(tag: str) -> str:
    return tag.split("}")[-1].lower()


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() == "true"


def TS(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    attrs = {k.lower(): v for k, v in xml_element.attrib.items()}
    rid = attrs.get("rid")
    if not rid:
        return

    is_reverse = _bool(attrs.get("isreverseformation"))

    with conn.cursor() as cursor:
        for child in xml_element:
            tag = _local(child.tag)

            if tag in ("latereason", "latereasoncode"):
                cursor.execute(
                    "UPDATE schedules SET late_reason_code = %s WHERE rid = %s;",
                    ((child.text or "").strip() or None, rid),
                )
                continue

            if tag != "location":
                continue

            _process_location(cursor, rid, child, root_reverse=is_reverse)


def _process_location(
    cursor: psycopg.Cursor[Any],
    rid: str,
    location: ET.Element,
    root_reverse: bool = False,
) -> None:
    l_attrs = {k.lower(): v for k, v in location.attrib.items()}
    tpl = l_attrs.get("tpl")
    if not tpl:
        return

    row: dict[str, str | bool | None] = {
        "wta": l_attrs.get("wta"),
        "wtd": l_attrs.get("wtd"),
        "wtp": l_attrs.get("wtp"),
        "pta": l_attrs.get("pta"),
        "ptd": l_attrs.get("ptd"),
        "plat": None,
        "plat_src": None,
        "plat_conf": False,
        "plat_sup": False,
        "plat_cis_sup": False,
        "suppr": False,
        "length": None,
        "detach_front": None,
        "divide_reverse_formation": root_reverse if root_reverse else None,
        "arr_at": None,
        "arr_et": None,
        "arr_wet": None,
        "arr_src": None,
        "arr_src_inst": None,
        "arr_at_class": None,
        "arr_at_removed": False,
        "arr_delayed": False,
        "arr_uncertainty": None,
        "dep_at": None,
        "dep_et": None,
        "dep_wet": None,
        "dep_etmin": None,
        "dep_src": None,
        "dep_src_inst": None,
        "dep_at_class": None,
        "dep_at_removed": False,
        "dep_delayed": False,
        "dep_uncertainty": None,
        "pass_at": None,
        "pass_et": None,
        "pass_wet": None,
        "pass_src": None,
        "pass_src_inst": None,
        "pass_at_class": None,
        "pass_at_removed": False,
        "pass_delayed": False,
        "pass_uncertainty": None,
    }

    for child in location:
        tag = _local(child.tag)
        c_attrs = {k.lower(): v for k, v in child.attrib.items()}

        if tag == "arr":
            update: dict[str, str | bool | None] = {
                "arr_at": c_attrs.get("at"),
                "arr_et": c_attrs.get("et"),
                "arr_wet": c_attrs.get("wet"),
                "arr_src": c_attrs.get("src"),
                "arr_src_inst": c_attrs.get("srcinst"),
                "arr_at_class": c_attrs.get("atclass"),
                "arr_at_removed": _bool(c_attrs.get("atremoved")),
                "arr_delayed": _bool(c_attrs.get("delayed")),
                "arr_uncertainty": c_attrs.get("uncertainty"),
            }
            row.update(update)
        elif tag == "dep":
            update = {
                "dep_at": c_attrs.get("at"),
                "dep_et": c_attrs.get("et"),
                "dep_wet": c_attrs.get("wet"),
                "dep_etmin": c_attrs.get("etmin"),
                "dep_src": c_attrs.get("src"),
                "dep_src_inst": c_attrs.get("srcinst"),
                "dep_at_class": c_attrs.get("atclass"),
                "dep_at_removed": _bool(c_attrs.get("atremoved")),
                "dep_delayed": _bool(c_attrs.get("delayed")),
                "dep_uncertainty": c_attrs.get("uncertainty"),
            }
            row.update(update)
        elif tag == "pass":
            update = {
                "pass_at": c_attrs.get("at"),
                "pass_et": c_attrs.get("et"),
                "pass_wet": c_attrs.get("wet"),
                "pass_src": c_attrs.get("src"),
                "pass_src_inst": c_attrs.get("srcinst"),
                "pass_at_class": c_attrs.get("atclass"),
                "pass_at_removed": _bool(c_attrs.get("atremoved")),
                "pass_delayed": _bool(c_attrs.get("delayed")),
                "pass_uncertainty": c_attrs.get("uncertainty"),
            }
            row.update(update)
        elif tag == "plat":
            update = {
                "plat": child.text,
                "plat_src": c_attrs.get("platsrc"),
                "plat_conf": _bool(c_attrs.get("conf")),
                "plat_sup": _bool(c_attrs.get("platsup")),
                "plat_cis_sup": _bool(c_attrs.get("cisplatsup")),
            }
            row.update(update)
        elif tag == "suppr":
            row["suppr"] = (child.text or "").strip().lower() == "true"
        elif tag == "length":
            row["length"] = child.text
        elif tag == "detachfront":
            row["detach_front"] = (child.text or "").strip().lower() == "true"
        elif tag in ("divideinreverse", "reverseformation", "isreverseformation"):
            row["divide_reverse_formation"] = (
                child.text or ""
            ).strip().lower() == "true"
        elif tag == "uncertainty":
            unc_status = c_attrs.get("status") or (child.text or "").strip() or None
            if unc_status:
                row["arr_uncertainty"] = row["arr_uncertainty"] or unc_status
                row["dep_uncertainty"] = row["dep_uncertainty"] or unc_status

    field_names: list[str] = list(row.keys())
    field_values: list[str | bool | None] = list(row.values())

    all_columns: list[str] = ["rid", "tpl"] + field_names
    params: list[str | bool | None] = [rid, tpl] + field_values

    query = sql.SQL(
        "INSERT INTO ts_locations ({columns}) "
        "VALUES ({placeholders}) "
        "ON CONFLICT ON CONSTRAINT uq_ts_locations "
        "DO UPDATE SET {updates};"
    ).format(
        columns=sql.SQL(", ").join(sql.Identifier(c) for c in all_columns),
        placeholders=sql.SQL(", ").join(sql.Placeholder() * len(all_columns)),
        updates=sql.SQL(", ").join(
            sql.SQL("{col} = EXCLUDED.{col}").format(col=sql.Identifier(c))
            for c in field_names
        ),
    )

    cursor.execute(query, params)
