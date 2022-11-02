"""
此文件用来存储一些与头部信息相关的数据结构
包括一个标准fits头部包含的信息, Excel(csv文件)需要存储的数据名称


@author: seu_wxy
"""

from astropy.io import fits
import datetime


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
                if len(l_split_first) == 1:  # 说明是comment
                    tempDic['key'] = None
                    tempDic['value'] = None
                    tempDic['comment'] = l_split_first[0].strip().replace('COMMENT ', '')
                    tempList.append(tempDic)
                    continue
                else:
                    continue
            l_split_second = l_split_first[-1].split('/')
            if l_split_second[-1].strip() == 'Instrument':
                tempDic['key'] = 'INSTRUM'
                tempDic['value'] = 'CHASE/HIS'
                tempDic['comment'] = 'Instrument'
            else:
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
                tempDic['comment'] = l_split_second[-1].strip()
            tempList.append(tempDic)
    if work_mode == 0:
        with open(txtPath, encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            tempList.append(line.rstrip('\n'))
    return tempList


# standard_header_list: 一个写入fits的标准头部参考dic数组
# 在构造真正的header时, 应从对照此list进行构造
standard_header_list = read_header_from_txt('raw_header.txt', work_mode=1)

# all_header_list: 包含有需要写入csv的所有信息
all_header_list = read_header_from_txt('all_header.txt', work_mode=0)


def get_real_header(real_dict: dict):
    """
    获取真正头部所需函数, 输入从DataProcessTool中代码获得的dict_list
    将会把standard_header_list中拥有的key相应value进行替换, 返回真正的fits.header
    :param real_dict: 输入的包含真正信息的dict
    :return: fits.header对象, 可以直接用来输入fits文件
    """
    real_header = fits.Header()
    for s_ele in standard_header_list:
        if s_ele['key'] is None:
            real_header.add_comment(s_ele['comment'])
        else:
            real_header.set(s_ele['key'], value=s_ele['value'], comment=s_ele['comment'])
    for key in real_dict:
        for this_dict in standard_header_list:
            if key == this_dict['key']:
                real_header.set(key, real_dict[key])
    return real_header


if __name__ == '__main__':
    print(repr(standard_header_list))
