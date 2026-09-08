import toml
import xml.etree.ElementTree as ET
import re
import warnings


def load_config_item[T](group_name: str, item_name: str, item_type: type[T]) -> T:
    config = None
    try:
        config = toml.load("config.toml")
        group = config.get(group_name, {})
        item = group.get(item_name)
        if type(item) != item_type:
            raise TypeError(
                f"{item_name} in {group_name} was expecting {item_type} but got {type(item)}"
            )
        elif item != None:
            return item
        else:
            raise Exception(f"{item_name} is missing in {group_name}")
    except FileNotFoundError:
        raise FileNotFoundError("config.toml is missing")
    except:
        raise Exception("issue loading config.toml")


def parse_pport_into_loadable_xml(decode: str) -> list[ET.Element]:
    elements: list[ET.Element] = []
    parts = re.findall(r"<Pport.*?>.*?</Pport>", decode, flags=re.DOTALL)
    for xml in parts:
        try:
            parse: ET.Element = ET.fromstring(xml)
            elements.append(parse)
        except Exception:
            warnings.warn(f"decode failed {xml}")

    return elements
