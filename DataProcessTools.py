import numpy as np
import struct
import io

#太阳空间望远镜科学载荷数据同步头[14,11,9,0,1,4,6,15]
#图像帧同步头[5,5,10,10,5,5,10,10]
head_data = [14,11,9,0,1,4,6,15]
head_pic = [5,5,10,10,5,5,10,10,1,2,3,4,5,6,7,8]


#0110 0100 0110 0100
#获取下一个字节数据
def GetNext(fread):
    try:
        data_raw = fread.read(1)
        val_tuple = struct.unpack('B', data_raw)
        return int(val_tuple[0])
    except:
        print("文件已读完")
        return -1

# 获取目标同步头对应数值
def GetTarget(target):
    ans = 0
    for i in target:
        ans=(ans<<4)+i
    return ans

#寻找探头
#太阳空间望远镜科学载荷数据同步头head_data
#图像帧同步头head_pic
def FindHead(fread,head_target):
    now = 0
    target = GetTarget(head_target)
    while now!=target:
        now = now % (1<<(4*(len(head_target)-2)))
        X = GetNext(fread)
        if X == -1:
            return "Error"
        now = (now<<8) + X
    return 1

#获取连续多个字节数据
def GetData(fread,nums):
    data = []
    for i in range(nums):
        x = GetNext(fread)
        if x==-1:
            data.append(0)
        else:
            data.append(x)
    return data
#464 340 1*16*16+2*16+4
def PicData(data):
    n = len(data)
    #print(n)
    index = 0
    now = 0
    target = GetTarget(head_pic)
    #print(target)
    while index < n:
        now = now%(1<<(4*(len(head_pic)-2)))
        now = (now<<8) + data[index]
        # if data[index] == 85 :
        #     print(index,data[index:index+8])
        index = index + 1
        if now == target:
            break
    #4+2+2
    if index!=n:
        Size = data[index:index+8]
        print("size",Size)




def DataWork(fread):
    if FindHead(fread,head_data)!=1:
        print("无数据头，解压结束")
        return "Error"
    MainHead = GetData(fread,8)
    Data = GetData(fread, 2032)
    # print(Data)
    PicData(Data)
    ErrorControl = GetData(fread,4)
    return 1

if __name__=='__main__':
    filename = 'SCSY1_KSC_HIS_20220808_004514.dat'
    f = open(filename, 'rb')
    s = 0
    DataWork(f)
    DataWork(f)
    DataWork(f)
    DataWork(f)
    DataWork(f)
    DataWork(f)
    DataWork(f)
    DataWork(f)
    DataWork(f)
    DataWork(f)
    DataWork(f)
    DataWork(f)
    # while DataWork(f)!="Error":
    #     s+=1
    # print(s)
