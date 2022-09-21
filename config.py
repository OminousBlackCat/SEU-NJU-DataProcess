"""
本程序在运行前需要配置的config参数
注: 带有TODO标志的需要在每次运行程序前进行确认
TODO: 确认以下参数是否正确

@author: seu_wxy
"""

# 程序将单独文件分段的段数, 以及后续处理多核并行的并行数
# 推荐使用当前可用cpu核数-4的并行数, 可以使得程序运行效率最大化
# type: int
# TODO: 影响程序运行效率的关键参数
multiprocess_count = 4

# 程序入口读入文件, 需精确至整个文件绝对路径
# 完整示例: /data/chase/Chase/data/data******.dat
# 需精确到后续的拓展名
# type: str
# TODO: 程序入口参数
input_file_url = "jp2/SCSY1_KSC_HIS_20220808_004514.dat"

# 程序输出所在文件夹, 需精确至文件夹最后的绝对路径
# 完整示例: /data/chase/Chase/Lev1/2022/3-4545/
# 如果程序检测不到文件夹则会连带父目录一起创建
# type: str
# TODO: 程序输出参数
output_dir = "jp2/"

# 写入进程的数量, 在磁盘阵列写入效率较高的情况下可以选择增加此参数
# 一般不需要修改此参数
# type: int
writer_process_count = 3

# 文件的迭代块大小
# 推荐固定为200MB, 每个worker都会在自己的迭代块大小内进行寻找帧头, 随后解析的操作, 直到寻找到迭代块大小之后的第一个帧头(确保不会丢失数据)
# type: int
iteration_chunk_size = 10 * 1024 * 1024
