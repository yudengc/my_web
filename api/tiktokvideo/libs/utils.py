from xml.etree.ElementTree import Element

from bs4 import BeautifulSoup


def trans_xml_to_dict(data_xml):
    soup = BeautifulSoup(data_xml, features='xml')
    xml = soup.find('xml')  # 解析XML
    if not xml:
        return {}
    data_dict = dict([(item.name, item.text) for item in xml.find_all()])
    return data_dict


def trans_dict_to_xml(d, tag='xml'):
    elem = Element(tag)
    for key, val in d.items():
        if isinstance(val, dict):
            child = trans_dict_to_xml(val, tag=key)
            elem.append(child)
            continue
        child = Element(key)
        child.text = str(val)
        elem.append(child)
    return elem
