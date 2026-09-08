import xml.etree.ElementTree as ET
import psycopg


def LoadingCategory(conn: psycopg.Connection, xml_element: ET.Element) -> None:
    attrs = {k.lower(): v for k, v in xml_element.attrib.items()}

    code = attrs.get("code")
    name = attrs.get("name")
    toc = attrs.get("toc") or None

    if not code or not name:
        return

    children = {
        child.tag.split("}")[-1].lower(): (child.text or "").strip()
        for child in xml_element
    }

    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO loading_categories (
                code,
                name,
                toc,
                typical_description,
                expected_description,
                definition,
                colour,
                image_file
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT uq_loading_categories
            DO UPDATE SET
                name = EXCLUDED.name,
                typical_description = EXCLUDED.typical_description,
                expected_description = EXCLUDED.expected_description,
                definition = EXCLUDED.definition,
                colour = EXCLUDED.colour,
                image_file = EXCLUDED.image_file
            """,
            (
                code,
                name,
                toc,
                children.get("typicaldescription", ""),
                children.get("expecteddescription", ""),
                children.get("definition", ""),
                children.get("colour", ""),
                children.get("image", ""),
            ),
        )
