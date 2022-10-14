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
from multiprocessing import Manager, Pool, Process, Value
import queue as pyQueue
import numpy as np
import DataProcessTools
import config
import os
import sys
import datetime
import time
import util
import csv
import header

# 载入参数
GLOBAL_MULTIPROCESS_COUNT = config.multiprocess_count
GLOBAL_INPUT_FILE_URL = config.input_file_url
GLOBAL_OUTPUT_DIR = config.output_dir
GLOBAL_FILE_SIZE = None  # 文件大小, 单位(Byte)
GLOBAL_MULTIPROCESS_LIST = []  # 迭代数组, 存储了每次执行并行函数时的参数
GLOBAL_CHUNK_SIZE = config.iteration_chunk_size
GLOBAL_WRITER_COUNT = config.writer_process_count
GLOBAL_CSV_DIR = config.output_csv_dir

# 预读文件, 预读文件大小
with open(GLOBAL_INPUT_FILE_URL, 'rb') as tempFile:
    tempFile.seek(0)  # seek一次查看是否有读取权限, 如果没有则会产生OSError
    tempFile.close()  # 成功则直接关闭 继续
    util.log("预读文件成功")
try:
    if not os.path.exists(GLOBAL_INPUT_FILE_URL):
        raise OSError
    with open(GLOBAL_INPUT_FILE_URL, 'rb') as tempFile:
        tempFile.seek(0)  # seek一次查看是否有读取权限, 如果没有则会产生OSError
        tempFile.close()  # 成功则直接关闭 继续
        util.log("预读文件成功")
except BaseException as exception:
    util.log(exception)
    util.log("文件读取失败, 请检查文件路径是否输入正确以及是否拥有读取权限")
    sys.exit("程序终止")
GLOBAL_FILE_SIZE = os.path.getsize(GLOBAL_INPUT_FILE_URL)  # 获得文件大小(Bytes)

# 创造Iteration数组
iteration = 0
while iteration < GLOBAL_FILE_SIZE:
    GLOBAL_MULTIPROCESS_LIST.append(iteration)
    iteration = iteration + GLOBAL_CHUNK_SIZE

# 预读两种输出目录
try:
    if not os.path.exists(GLOBAL_OUTPUT_DIR):
        os.makedirs(GLOBAL_OUTPUT_DIR)
    if not os.path.exists(GLOBAL_CSV_DIR):
        os.makedirs(GLOBAL_CSV_DIR)
    if not os.access(GLOBAL_OUTPUT_DIR, os.W_OK):
        raise OSError
    if not os.access(GLOBAL_CSV_DIR, os.W_OK):
        raise OSError
except OSError as exception:
    util.log(str(exception))
    util.log("创建输出文件夹失败或文件夹无写入权限")
    sys.exit("程序终止")

# 创建csv文件, 每个dat文件对应一个csv
csv_file_name = GLOBAL_CSV_DIR + datetime.datetime.now().strftime('RSM%Y%m%d%H%M%S.csv')  # TODO: 这里的时间需不需要改一下
with open(csv_file_name, 'a', encoding='utf-8-sig') as csv_file:
    file_writer = csv.writer(csv_file)
    file_writer.writerow(header.all_header_list)
    util.log("创建CSV文件成功")

# 读入文件, 创建共享内存(格式为mmap)
# 已弃用: 使用mmap, mmap可以使文件立刻载入至内存, 略去之后的磁盘读取时间, mmap将作为每个子进程的全局数据, 对于linux, 其父进程fork()时将对此数据一并共享(会产生许多内存损耗)
# 直接使用python的文件流 在多个进程进行共享读取, 速度并不会很慢
# 如何控制写入队列是影响速度的关键
terminal_signal = Value('i', 0)


# 并行(创造者/工人)函数(worker/producer函数), process pool中的每个进程都将执行此函数
# 函数输入: 队列, 文件的开始比特数位
# 函数处理完之后会给队列提交结果, consumer进程将监视队列进行文件写出工作
def process_file(start_byte: int, queue: Manager().Queue):
    util.log("开启producer函数, start byte为:" + str(start_byte))
    out_dict = {
        'image_list': [],
        'head_list': [],
        'dict_list': []
    }
    with open(GLOBAL_INPUT_FILE_URL, 'rb') as input_file:
        input_file.seek(start_byte)
        out_dict['dict_list'], out_dict['head_list'], out_dict['image_list'] = DataProcessTools.parallel_work(
            input_file, start_byte)
    # 结果是一个dict, dict内部有两个list元素, list内容为图像数组与头数据数组
    # 将此结果放入queue中
    queue.put(out_dict)
    util.log("此块解析成功!  当前队列剩余文件: " + str(queue.qsize()))


# 处理(消费者)函数(consumer函数), 监视队列, 对队列里的元素进行处理
# 函数输入: 队列
def conduct_output(queue: Manager().Queue):
    while True:
        try:
            out_dic = queue.get(block=False)
            util.log("开始处理文件..." + "当前队列内文件: " + str(queue.qsize()))
            # 开始处理dict
            # TODO: 增加块的信息 输出每块的处理情况
            image_list = out_dic['image_list']
            head_list = out_dic['head_list']
            dict_list = out_dic['dict_list']
            for index in range(len(image_list)):
                # 每个元素代表了一个fits文件
                current_image = []
                for stream in image_list[index]:
                    # 将jp2文件流转为二维图像数组
                    # jp2的shape应为(188, 384)
                    # 188为Y axis shape, 384为 X axis shape
                    current_image.append(decode(stream))
                childShape = current_image[0].shape
                completeImage = np.zeros((childShape[0], childShape[1] * 6))
                # 合并图像
                for child_index in range(len(current_image)):
                    completeImage[:, child_index * childShape[1]: (child_index + 1) * childShape[1]] \
                        = current_image[child_index]
                # 构造header
                currentHeader = header.get_real_header(dict_list[index])
                fileWriteTime = currentHeader['STR_TIME']
                scanCount = currentHeader['SCN_NUM']
                frameCount = currentHeader['FRM_NUM']
                # 写入csv文件
                with open(csv_file_name, 'a', encoding='utf-8-sig') as write_csv:
                    writer = csv.writer(write_csv)
                    writer.writerow(head_list[index])
                # 输出文件
                currentHDUList = fits.HDUList(fits.PrimaryHDU(completeImage, currentHeader))
                currentHDUList.writeto(GLOBAL_OUTPUT_DIR + 'RSM' + fileWriteTime.replace('-', '') + '-'
                                       + str(scanCount).zfill(4) + '-' + str(frameCount).zfill(8) + '.fits', overwrite=True)
            queue.task_done()
        except pyQueue.Empty:
            util.log("队列为空...当前结束标识为: " + str(terminal_signal.value))
            time.sleep(2)
            if terminal_signal.value != 0:
                return
        except RuntimeError:
            util.log("解析文件出错, 帧内容有误, 已剔除")
            queue.task_done()
            continue


# 程序入口函数
def main():
    queue = Manager().Queue()
    consumer_list = []
    for j in range(GLOBAL_WRITER_COUNT):
        consumer_list.append(Process(target=conduct_output, args=(queue,)))
    for j in range(GLOBAL_WRITER_COUNT):
        consumer_list[j].start()
    worker_pool = Pool(processes=GLOBAL_MULTIPROCESS_COUNT)
    for index in GLOBAL_MULTIPROCESS_LIST:
        worker_pool.apply_async(process_file, (index, queue))
    worker_pool.close()
    worker_pool.join()
    util.log("生产者已全部生产完毕!")
    queue.join()
    util.log("当前队列已经为空, 且生产者已经全部生产完毕. 已将结束标志设为可停止")
    terminal_signal.value = 1


if __name__ == '__main__':
    main()
