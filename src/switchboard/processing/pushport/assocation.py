import xml.etree.ElementTree as ET
import psycopg


def Association(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    attrs = {k.lower(): v for k, v in xml_element.attrib.items()}

    tiploc = attrs.get("tiploc")
    category = attrs.get("category")

    if not tiploc or not category:
        return

    is_cancelled = attrs.get("iscancelled", "false").lower() == "true"
    is_deleted = attrs.get("isdeleted", "false").lower() == "true"

    main_rid = None
    main_times = {}
    assoc_rid = None
    assoc_times = {}

    for child in xml_element:
        tag = child.tag.split("}")[-1].lower()
        c_attrs = {k.lower(): v for k, v in child.attrib.items()}

        if tag == "main":
            main_rid = c_attrs.get("rid")
            main_times = c_attrs
        elif tag == "assoc":
            assoc_rid = c_attrs.get("rid")
            assoc_times = c_attrs

    if not main_rid or not assoc_rid:
        return

    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO associations (
                main_rid, assoc_rid, tiploc, category, is_cancelled, is_deleted,
                main_wta, main_wtd, main_wtp, main_pta, main_ptd,
                assoc_wta, assoc_wtd, assoc_wtp, assoc_pta, assoc_ptd
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT uq_associations
            DO UPDATE SET
                is_cancelled = EXCLUDED.is_cancelled,
                is_deleted = EXCLUDED.is_deleted,
                main_wta = EXCLUDED.main_wta,
                main_wtd = EXCLUDED.main_wtd,
                main_wtp = EXCLUDED.main_wtp,
                main_pta = EXCLUDED.main_pta,
                main_ptd = EXCLUDED.main_ptd,
                assoc_wta = EXCLUDED.assoc_wta,
                assoc_wtd = EXCLUDED.assoc_wtd,
                assoc_wtp = EXCLUDED.assoc_wtp,
                assoc_pta = EXCLUDED.assoc_pta,
                assoc_ptd = EXCLUDED.assoc_ptd;
            """,
            (
                main_rid,
                assoc_rid,
                tiploc,
                category,
                is_cancelled,
                is_deleted,
                main_times.get("wta"),
                main_times.get("wtd"),
                main_times.get("wtp"),
                main_times.get("pta"),
                main_times.get("ptd"),
                assoc_times.get("wta"),
                assoc_times.get("wtd"),
                assoc_times.get("wtp"),
                assoc_times.get("pta"),
                assoc_times.get("ptd"),
            ),
        )
