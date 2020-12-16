import re
from typing import List
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


def content_shape(content: str) -> List[dict]:
    # [
    #     {
    #         "field": "左侧字段",
    #         "field_name": "Apply_id"
    #     }
    # ]
    content_list = [i.strip() for i in re.split('[\r|\n]', content) if i]
    result = []
    for content in content_list:
        _list = content.split('{{')
        length = len(_list)
        if length == 1:
            # 单字段
            result.append({
                "field": _list[0],
                "field_name": ""
            })
        elif length == 2:
            if _list[0] == '':
                # 单输入框
                result.append({
                    "field": "",
                    "field_name": _list[0]
                })
            else:
                # 左字段右输入框
                result.append({
                    "field": _list[0],
                    "field_name": _list[1].split('}}')[0].split('.')[0]
                })
        else:
            raise ValueError('err length')
    return result
