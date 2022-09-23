"""
此文件用来存储一些与头部信息相关的数据结构
包括一个标准fits头部包含的信息, Excel(csv文件)需要存储的数据名称


@author: seu_wxy
"""

from astropy.io import fits


def read_header_from_txt(txtPath: str, work_mode=1):
    """
    工具函数, 从txt中读取header的key与value以及comment
    主要用来获得standard_header_list
    :param txtPath: 路径
    :param work_mode: 工作模式(0 all_header 或 1 raw_header)
    """
    tempList = []
    if work_mode == 1:
        with open(txtPath) as f:
            lines = f.readlines()
        for line in lines:
            tempDic = {
                'key': '',
                'value': '',
                'comment': ''
            }
            l_split_first = line.split('=')
            if len(l_split_first) < 2:
                continue
            l_split_second = l_split_first[1].split('/')
            tempDic['key'] = l_split_first[0].strip()
            true_value = None
            try:
                true_value = int(l_split_second[0].strip())
            except ValueError:
                try:
                    true_value = float(l_split_second[0].strip())
                except ValueError:
                    true_value = l_split_second[0].replace("'", "")
                    true_value = true_value.strip()
            tempDic['value'] = true_value
            tempDic['comment'] = l_split_second[1].strip()
            tempList.append(tempDic)
    if work_mode == 0:
        with open(txtPath) as f:
            lines = f.readlines()
        for line in lines:
            tempList.append({
                'key': line,
                'value': None
            })
    return tempList


# standard_header_list: 一个写入fits的标准头部参考dic数组
# 在构造真正的header时, 应从对照此list进行构造
standard_header_list = read_header_from_txt('raw_header.txt', work_mode=1)

# all_header_list: 包含有需要写入csv的所有信息
all_header_list = read_header_from_txt('all_header.txt', work_mode=0)


def get_real_header(real_list: list):
    """
    获取真正头部所需函数, 输入从DataProcessTool中代码获得的dict_list
    将会把standard_header_list中拥有的key相应value进行替换, 返回真正的fits.header
    :param real_list: 输入的包含有多余Key的List
    :return: fits.header对象, 可以直接用来输入fits文件
    """
    real_header = fits.Header()
    for s_ele in standard_header_list:
        real_header.set(s_ele['key'], value=s_ele['value'], comment=s_ele['comment'])
    for r_ele in real_list:
        try:
            temp = real_header[r_ele['key']]  # raise KeyError
            real_header.set(r_ele['key'], value=r_ele['value'])
        except KeyError:
            continue
    return real_header
