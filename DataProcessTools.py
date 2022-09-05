import numpy as np
import struct
import io
import cv2
from io import BytesIO

#太阳空间望远镜科学载荷数据同步头[14,11,9,0,1,4,6,15]
#图像帧同步头[5,5,10,10,5,5,10,10]
head_data = [14,11,9,0,1,4,6,15]
head_pic = [5,5,10,10,5,5,10,10,1,2,3,4,5,6,7,8]



#获取下一个字节数据
def GetNext(fread):
    try:
        # 读取一个字节的内容
        data_raw = fread.read(1)
        # 转换为数字
        val_tuple = struct.unpack('B', data_raw)
        # 输出结果
        return int(val_tuple[0])
    except:
        # 文件读完返回-1
        print("文件已读完")
        return -1

#获取连续多个字节数据
# 连续读取nums个字节
def GetData(fread,nums):
    data = []
    for i in range(nums):
        # 读取字符
        x = GetNext(fread)
        if x==-1:
            # 无内容用0补齐
            data.append(0)
            break
        else:
            # 输出提取内容
            data.append(x)
    # 不足补0
    # 返回内容
    return data

# 写二进制文件
# filename为文件名
def FileWrite(data,file):
    for x in data:
        # 打包回二进制
        a = struct.pack('B', x)
        # 写二进制文件
        file.write(a)


# 获取目标同步头对应数值
# 同步头一位代表四个二进制位
def GetTarget(target):
    ans = 0
    for i in target:
        ans = (ans << 4) + i
    return ans


# 获取目标list对应值，按字节转换
# list头代表八个二进制位
def GetResult(target):
    ans = 0
    for i in target:
        ans = (ans << 8) + i
    return ans


# 寻找数据帧的探头
def FindHead(fread, head_target):
    now = 0
    # 获取数据头的内容
    target = GetTarget(head_target)

    while now != target:
        # 计算当前头内容
        now = now % (1 << (4 * (len(head_target) - 2)))
        X = GetNext(fread)
        if X == -1:
            return "Error"
        now = (now << 8) + X
    return 1


# 寻找图片帧的开头
# 输出图片帧开头所在的坐标第一个位置
# 否则输出len(data)-7
def FindPicHead(data):
    n = len(data)
    # print(n)
    index = 0
    now = 0
    # 获取图片
    target = GetTarget(head_pic)
    # print(target)
    while index < n:

        now = now % (1 << (4 * (len(head_pic) - 2)))
        now = (now << 8) + data[index]
        index = index + 1
        if now == target:
            break

    if now == target:
        return index - 8
    return n - 7

#对图片帧文件进行处理
def PicWork(data,num):
    data =
    # 获取数据长度
    N = len(data)
    indexList = []
    target = GetTarget([15,15,4,15,15,15,5,1])
    # 不足8的倍数补0
    while len(data) % 8 > 0:
        data.append(0)
    # 统计所有头部分
    for i in range(N - 8):
        if target == GetResult(data[i:i + 4]):
            indexList.append(i)
    M = len(indexList)
    # print(indexList)
    # print(M)
    # 输出所有文件
    FileList = []
    for i in range(M-1):
        # 创建文件流
        FileList.append(BytesIO())
        # 写文件流
        FileWrite(data[indexList[i]:indexList[i+1]],FileList[i])
    # 创建文件流
    FileList.append(BytesIO())
    # 写文件流
    FileWrite(data[indexList[M-1]:], FileList[M-1])
    return FileList


# 输入文件流 对文件流工作
def DataWork(fread):
    # num统计读取文件数量
    num = 0
    # 记录图片帧内容
    PicData = []
    # 记录数据
    Data = []

    # 寻找数据帧的开头
    while FindHead(fread, head_data) == 1:
        # 记录头部份
        MainHead = GetData(fread, 8)
        # 提取数据部分
        Data = Data + GetData(fread, 2032)
        # 记录错误控制内容
        ErrorControl = GetData(fread, 4)
        # 在数据帧中寻找图像帧开头，如果有输出图像帧开头的index
        index = FindPicHead(Data)

        # 判断有无出现数据帧开头
        if index < len(Data) - 7:
            # 记录新图像帧之前的内容
            PicData = PicData + Data[:index]
            # 去除提取的内容
            Data = Data[index + 8:]
            # 无用内容不处理
            if num > 0:
                # 处理图像帧内容
                PicWork(PicData, num)
            # 情况图像帧
            PicData = []
            # 编号计数
            num = num + 1
        else:
            # 提取图像帧内容
            PicData = PicData + Data[:index]
            # 保留可能出现数据头的内容
            Data = Data[index:]
            # 无用内容不处理
    if num > 0:
        # 处理图像帧内容
        PicWork(PicData, num)
    # 输出处理信息
    print(num)
    print("无数据头，解压结束")
    print("发现图片帧：" + str(num))
    return "Over"


# 解析


if __name__ == '__main__':
    filename = 'sun_42697.dat'
    f = open(filename, 'rb')
    s = 0
    DataWork(f)
    # image = cv2.imread('30402.jp2')
    # print(image)
    # cv2.imwrite('1.png', image)

# 10.201.95.104
