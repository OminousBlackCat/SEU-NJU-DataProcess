from copy import deepcopy
import util
from io import BytesIO
import struct

# 太阳空间望远镜科学载荷数据同步头[14,11,9,0,1,4,6,15]
# 图像帧同步头[5,5,10,10,5,5,10,10]
head_data = [14, 11, 9, 0, 1, 4, 6, 15]
head_pic = [5, 5, 10, 10, 5, 5, 10, 10, 1, 2, 3, 4, 5, 6, 7, 8]


# 寻找数据帧的探头
def findFrameHead(fread, head_target):
    now = 0
    # 获取数据头的内容
    target = util.getTarget(head_target)

    while now != target:
        # 计算当前头内容
        now = now % (1 << (4 * (len(head_target) - 2)))
        X = util.getNext(fread)
        if X == -1:
            return "Error"
        now = (now << 8) + X
    return 1


# 寻找图片帧的开头
# 输出图片帧开头所在的坐标第一个位置
# 否则输出len(data)-7
def findPicHead(data):
    n = len(data)
    # print(n)
    index = 0
    now = 0
    # 获取图片
    target = util.getTarget(head_pic)
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


# 解析辅助数据并构造header(字典)
def processHeader(stream):
    headDic = {}
    # stream代表输入的辅助数据流
    # 辅助数据格式    0~5(6)    时间码
    #               6~69(64)    定位数据
    #               70~127(58)  定轨数据
    #               128~183(56) 载荷仓数据
    #               184~211(28) 平台仓数据
    #               212~213(2)  温度量信息
    #               214~277(64) 望远镜工作参数
    #               278~493(216)填充数据



    # 定轨数据(58)
    data_raw = stream.read(58)


    # 载荷舱姿态数据（56）
    # 0~7（8） 载荷舱惯性四元数Q0（8字节双精度）
    val_tuple = struct.unpack('d', stream.read(8))
    headDic["Q0"] = val_tuple[0]
    # 8~15（8） 载荷舱惯性四元数Q1（8字节双精度）
    data_raw = stream.read(8)
    val_tuple = struct.unpack('d', stream.read(8))
    headDic["Q1"] = val_tuple[0]
    # 16~23（8） 载荷舱惯性四元数Q2（8字节双精度）
    data_raw = stream.read(8)
    val_tuple = struct.unpack('d', stream.read(8))
    headDic["Q2"] = val_tuple[0]
    # 24~31（8） 载荷舱惯性四元数Q3（8字节双精度）
    data_raw = stream.read(8)
    val_tuple = struct.unpack('d', stream.read(8))
    headDic["Q3"] = val_tuple[0]
    # 角速率32~55(24)
    data_raw = stream.read(24)


    # 平台舱姿态数据（28）
    data_raw = stream.read(28)

    # 温度数据（2）
    data_raw = stream.read(2)

    # 望远镜工作参数（64）
    #0~12（13） 电机1参数
    data_raw = stream.read(13)
    #13~25（13）   电机2参数
    data_raw = stream.read(13)
    #26~29（4）    成像帧计数（无符号整型4位）
    val_tuple = struct.unpack('I', stream.read(4))
    headDic["picframeCount"]=val_tuple[0]
    #30~33(4)      帧内计数
    data_raw = stream.read(4)
    val_tuple = struct.unpack('I', stream.read(4))
    headDic["frameCount"]=val_tuple[0]
    return headDic


# 对图片帧文件进行处理
def processPicStream(data, num):
    # 提取自定义数据区
    dataHead = data[8: 8 + 280]
    headStream = BytesIO()
    # 文件流回到开头
    util.fileWrite(dataHead, headStream)
    headStream.seek(0)
    # 去除自定义数据区
    data = data[8 + 278:]
    # 获取数据长度
    N = len(data)
    indexList = []
    target = util.getTarget([15, 15, 4, 15, 15, 15, 5, 1])
    # 统计所有头部分
    for i in range(N - 8):
        # 找图片的开头
        if target == util.getResult(data[i:i + 4]):
            indexList.append(i)
    M = len(indexList)
    # print(indexList)
    # print(M)
    # 不足8的倍数补0
    while len(data) % 8 > 0:
        data.append(0)
    # 输出所有文件
    FileList = []
    for i in range(M - 1):
        # 创建文件流
        FileList.append(BytesIO())
        # 写文件流
        util.fileWrite(data[indexList[i]:indexList[i + 1]], FileList[i])
        # 文件流回到开头
        FileList[i].seek(0)
    # 创建文件流
    FileList.append(BytesIO())
    # 写文件流
    util.fileWrite(data[indexList[M - 1]:], FileList[M - 1])
    # 文件流回到开头
    FileList[M - 1].seek(0)
    headData = processHeader(headStream)
    return headData, FileList


# 输入文件流 对文件流工作
# 输出List
# 格式 每个元素为一个文件流和一个list
# 文件流为头文件信息 list为所有子图片的文件流
def dataWork(fread):
    # num统计读取文件数量
    num = 0
    # 记录图片帧内容
    PicData = []
    # 记录数据
    Data = []
    # 存储所有图片信息
    allData = []

    # 寻找数据帧的开头
    while findFrameHead(fread, head_data) == 1:
        # 记录头部份
        MainHead = util.getData(fread, 8)
        # 提取数据部分
        Data = Data + util.getData(fread, 2032)
        # 记录错误控制内容
        ErrorControl = util.getData(fread, 4)
        # 在数据帧中寻找图像帧开头，如果有输出图像帧开头的index
        index = findPicHead(Data)
        # 最终输出的头部信息 应该是个字典
        headerData = None
        # 需要拼接图像list
        picList = None

        # 判断有无出现数据帧开头
        if index < len(Data) - 7:
            # 记录新图像帧之前的内容
            PicData = PicData + Data[:index]
            # 去除提取的内容
            Data = Data[index + 8:]
            # 无用内容不处理
            if num > 0:
                # 处理图像帧内容
                headerData, picList = processPicStream(PicData, num)
                # 存储图片信息
                allData.append([deepcopy(headerData), deepcopy(picList)])
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
        headerData, picList = processPicStream(PicData, num)
        # 存储图片信息
        allData.append([deepcopy(headerData), deepcopy(picList)])
    # 输出处理信息
    print("无数据头，解压结束")
    print("发现图片帧：" + str(num))
    # 输出所有图片信息
    return allData


if __name__ == '__main__':
    f = BytesIO()
    util.fileWrite([1, 2, 3, 4, 5, 6], f)
    f.seek(0)
    print(util.getData(f, 6))
    # filename = 'sun_42697.dat'
    # f = open(filename, 'rb')
    # s = 0
    # DataWork(f)
    # image = cv2.imread('30402.jp2')
    # print(image)
    # cv2.imwrite('1.png', image)

# 10.201.95.104
