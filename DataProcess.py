"""
本py代码的主要用途为:
读取当前文件夹内的对应格式文件列表, 调用DataProcessTools.py内的解析函数获取分块图像
分块图像以file stream(object) list的形式传入
并对上述获得的图像进行拼接获得一张完整的fits文件, 最后将必须的头部信息写入fits完成帧数据处理
主程序代码逻辑:
I.      载入参数, 预读文件(是否存在), (创建)输出文件夹;
II.     定义分段, 开始并行处理文件, 每个进程(线程)处理一个文件夹之后都会提交一个写入任务进任务队列;
III.    使用生产者-消费者模型(producer-consumer model), 使用一个单独的cpu处理写入队列;
IV.

@author seu_wxy
"""

from openjpeg import decode
from astropy.io import fits
from multiprocessing import JoinableQueue
import numpy as np
import DataProcessTools
import config
import os
import sys
import multiprocessing
import util

# 载入参数
GLOBAL_MULTIPROCESS_COUNT = config.multiprocess_count
GLOBAL_INPUT_FILE_URL = config.input_file_url
GLOBAL_OUTPUT_DIR = config.output_dir
GLOBAL_FILE_SIZE = None  # 文件大小, 单位(Byte)
GLOBAL_MULTIPROCESS_LIST = []  # 迭代数组, 存储了每次执行并行函数时的参数
GLOBAL_CHUNK_SIZE = config.iteration_chunk_size

# 预读文件, 预读文件大小
try:
    if not os.path.exists(GLOBAL_INPUT_FILE_URL):
        raise OSError
    with open(GLOBAL_INPUT_FILE_URL, 'rb') as tempFile:
        tempFile.seek(0)  # seek一次查看是否有读取权限, 如果没有则会产生OSError
        tempFile.close()  # 成功则直接关闭 继续
except BaseException as exception:
    util.log(str(exception))
    util.log("文件读取失败, 请检查文件路径是否输入正确以及是否拥有读取权限")
    sys.exit("程序终止")
GLOBAL_FILE_SIZE = os.path.getsize(GLOBAL_INPUT_FILE_URL)  # 获得文件大小(Bytes)

# 创造Iteration数组
i = 0
while i < GLOBAL_FILE_SIZE:
    GLOBAL_MULTIPROCESS_LIST.append(i)
    i = i + GLOBAL_CHUNK_SIZE

# 预读输出目录
try:
    if not os.path.exists(GLOBAL_OUTPUT_DIR):
        os.makedirs(GLOBAL_OUTPUT_DIR)
    if not os.access(GLOBAL_OUTPUT_DIR, os.W_OK):
        raise OSError
except OSError as exception:
    util.log(str(exception))
    util.log("创建输出文件夹失败或文件夹无写入权限")
    sys.exit("程序终止")


# 读入文件, 创建共享内存(格式为mmap)
# 已弃用: 使用mmap, mmap可以使文件立刻载入至内存, 略去之后的磁盘读取时间, mmap将作为每个子进程的全局数据, 对于linux, 其父进程fork()时将对此数据一并共享(会产生许多内存损耗)
# 直接使用python的文件流 在多个进程进行共享读取, 速度并不会很慢
# 如何控制写入队列是影响速度的关键

# 并行函数(worker函数), process pool中的每个进程都将执行此函数
# 函数输入: 文件的开始比特数位
# 函数处理完之后会给队列提交结果, consumer进程将监视队列进行文件写出工作
def process_file(queue: JoinableQueue, start_byte: int):
    out_dict = {}
    with open(GLOBAL_INPUT_FILE_URL, 'rb') as input_file:
        input_file.seek(start_byte)
        # TODO: 等待对接
    # 结果是一个dict, dict内部有两个list元素, list内容为图像数组与头数据数组
    # 将此结果放入queue中
    queue.put(out_dict)
    queue.join()


# 传入的jpList为file stream的list
# list内的每个元素为一个JP2文件的stream
def jointJP2(jpList):
    imageList = []
    for stream in jpList:
        # 将jp2文件流转为二维图像数组
        # jp2的shape应为(188, 384)
        # 188为Y axis shape, 384为 X axis shape
        imageList.append(decode(stream))
    childShape = imageList[0].shape
    print(childShape)
    completeImage = np.zeros((childShape[0], childShape[1] * 6))
    for i in range(len(imageList)):
        completeImage[:, i * childShape[1]: (i + 1) * childShape[1]] = imageList[i]
    return completeImage


# 创建fits文件, 将数据, 头部写入文件, 输出到指定目录
def createFits(image, header, outDir):
    tempHDUList = fits.HDUList(fits.PrimaryHDU(image, header))
    tempHDUList.writeto(outDir, overwrite=True)


# 程序入口函数
def main():
    tempList = []
    with open('jp2/SCSY1_KSC_HIS_20220808_004514.dat', 'rb') as testFile:
        tempList = DataProcessTools.dataWork(testFile)
    for i in range(len(tempList)):
        if i == 200:
            image = jointJP2(tempList[i][1])
            createFits(image, None, 'jp2/a.fits')


if __name__ == '__main__':
    main()
