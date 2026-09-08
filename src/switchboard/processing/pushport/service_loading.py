from __future__ import annotations

import xml.etree.ElementTree as ET
import psycopg


def _local(tag: str) -> str:
    return tag.split("}")[-1].lower()


def ServiceLoading(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    attrs = {k.lower(): v for k, v in xml_element.attrib.items()}
    rid = attrs.get("rid")
    tpl = attrs.get("tpl")
    if not (rid and tpl):
        return

    loading_category = loading_category_src = loading_category_src_inst = None
    loading_percentage = loading_percentage_src = loading_percentage_src_inst = None

    for child in xml_element:
        tag = _local(child.tag)
        c_attrs = {k.lower(): v for k, v in child.attrib.items()}

        if tag == "loadingcategory":
            loading_category = (child.text or "").strip() or None
            loading_category_src = c_attrs.get("src")
            loading_category_src_inst = c_attrs.get("srcinst")
        elif tag == "loadingpercentage":
            loading_percentage = (child.text or "").strip() or None
            loading_percentage_src = c_attrs.get("src")
            loading_percentage_src_inst = c_attrs.get("srcinst")

    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO service_loading (
                rid, tpl, wta, wtd, wtp, pta, ptd,
                loading_category, loading_category_src, loading_category_src_inst,
                loading_percentage, loading_percentage_src, loading_percentage_src_inst
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT uq_service_loading
            DO UPDATE SET
                loading_category = EXCLUDED.loading_category,
                loading_category_src = EXCLUDED.loading_category_src,
                loading_category_src_inst = EXCLUDED.loading_category_src_inst,
                loading_percentage = EXCLUDED.loading_percentage,
                loading_percentage_src = EXCLUDED.loading_percentage_src,
                loading_percentage_src_inst = EXCLUDED.loading_percentage_src_inst;
            """,
            (
                rid,
                tpl,
                attrs.get("wta"),
                attrs.get("wtd"),
                attrs.get("wtp"),
                attrs.get("pta"),
                attrs.get("ptd"),
                loading_category,
                loading_category_src,
                loading_category_src_inst,
                loading_percentage,
                loading_percentage_src,
                loading_percentage_src_inst,
            ),
        )
