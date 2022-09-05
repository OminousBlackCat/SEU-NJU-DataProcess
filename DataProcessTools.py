import numpy as np
import struct
import io
import cv2

# 太阳空间望远镜科学载荷数据同步头[14,11,9,0,1,4,6,15]
# 图像帧同步头[5,5,10,10,5,5,10,10]
head_data = [14, 11, 9, 0, 1, 4, 6, 15]
head_pic = [5, 5, 10, 10, 5, 5, 10, 10, 1, 2, 3, 4, 5, 6, 7, 8]


# 0110 0100 0110 0100
# 获取下一个字节数据
def GetNext(fread):
    try:
        data_raw = fread.read(1)
        val_tuple = struct.unpack('B', data_raw)
        return int(val_tuple[0])
    except:
        print("文件已读完")
        return -1


# 获取连续多个字节数据
def GetData(fread, nums):
    data = []
    for i in range(nums):
        x = GetNext(fread)
        if x == -1:
            data.append(0)
        else:
            data.append(x)
    return data


# 写二进制文件
def FileWrite(data, filename):
    with open(filename, 'wb')as fp:
        for x in data:
            a = struct.pack('B', x)
            fp.write(a)


# 获取目标同步头对应数值
def GetTarget(target):
    ans = 0
    for i in target:
        ans = (ans << 4) + i
    return ans


# 获取目标list对应值，按字节转换
def GetResult(target):
    ans = 0
    for i in target:
        ans = (ans << 8) + i
    return ans


# 寻找数据帧的探头
def FindHead(fread, head_target):
    now = 0
    target = GetTarget(head_target)
    while now != target:
        now = now % (1 << (4 * (len(head_target) - 2)))
        X = GetNext(fread)
        if X == -1:
            return "Error"
        now = (now << 8) + X
    return 1


# 寻找图片帧的开头
# 输出图片帧开头所在的坐标
def FindPicHead(data):
    n = len(data)
    # print(n)
    index = 0
    now = 0
    target = GetTarget(head_pic)
    # print(target)
    while index < n:
        now = now % (1 << (4 * (len(head_pic) - 2)))
        now = (now << 8) + data[index]
        # if data[index] == 85 :
        #     print(index,data[index:index+8])
        index = index + 1
        if now == target:
            break

    if now == target:
        return index - 8
    return n - 7


# 对图片帧文件进行处理
def PicWork(data, num):
    index = 512
    while len(data) % 8 > 0:
        data.append(0)
    N = len(data)
    indexList = []
    target = GetTarget([15, 15, 4, 15, 15, 15, 5, 1])
    for i in range(N - 8):
        if target == GetResult(data[i:i + 4]):
            indexList.append(i)
    M = len(indexList)
    print(indexList)
    print(M)
    for i in range(M - 1):
        FileWrite(data[indexList[i]:indexList[i + 1]], str(num * 10 + i) + ".jp2")
    FileWrite(data[indexList[M - 1]:], str(num * 10 + M - 1) + ".jp2")
    return 1


def DataWork(fread):
    num = 0
    PicData = []
    Data = []
    while FindHead(fread, head_data) == 1:
        MainHead = GetData(fread, 8)
        Data = Data + GetData(fread, 2032)
        ErrorControl = GetData(fread, 4)
        index = FindPicHead(Data)
        if index < len(Data) - 7:
            PicData = PicData + Data[:index]
            Data = Data[index + 8:]
            if num > 41330:
                if num <= 41340:
                    PicWork(PicData, num)
            PicData = []
            num = num + 1
        else:
            PicData = PicData + Data[:index]
            Data = Data[index:]
    print(num)
    print("无数据头，解压结束")
    print("发现图片帧：" + str(num))
    return "Over"


if __name__ == '__main__':
    filename = 'SCSY1_KSC_HIS_20220808_004514.dat'
    f = open(filename, 'rb')
    s = 0
    DataWork(f)
    # image = cv2.imread('30402.jp2')
    # print(image)
    # cv2.imwrite('1.png', image)
