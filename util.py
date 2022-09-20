import struct
import datetime


# 获取下一个字节数据
def getNext(fread):
    try:
        # 读取一个字节的内容
        data_raw = fread.read(1)
        # 转换为数字
        val_tuple = struct.unpack('B', data_raw)
        # 输出结果
        return int(val_tuple[0])
    except BaseException as exception:
        print(exception)
        # 文件读完返回-1
        print("文件已读完")
        return -1


# 获取连续多个字节数据
# 连续读取nums个字节
def getData(fread, nums):
    data = []
    error = True
    for i in range(nums):
        # 读取字符
        x = getNext(fread)
        if x == -1:
            # 无内容用0补齐
            error = False
            data.append(0)
            break
        else:
            # 输出提取内容
            data.append(x)
    # 不足补0
    while len(data) < nums:
        data.append(0)
    # 返回内容
    return data,error


# 写二进制文件
# filename为文件名
def fileWrite(data, file):
    for x in data:
        # 打包回二进制
        a = struct.pack('B', x)
        # 写二进制文件
        file.write(a)


# 获取目标同步头对应数值
# 同步头一位代表四个二进制位
def getTarget(target):
    ans = 0
    for i in target:
        ans = (ans << 4) + i
    return ans


# 获取目标list对应值，按字节转换
# list头代表八个二进制位
def getResult(target):
    ans = 0
    for i in target:
        ans = (ans << 8) + i
    return ans


# 输出辅助函数
def log(text: str):
    print(datetime.datetime.now().strftime("[YYYY-mm-dd-hh:MM:ss]") + text)

