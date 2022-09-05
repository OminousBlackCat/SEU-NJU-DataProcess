from openjpeg import decode
import numpy as np
from astropy.io import fits

'''
本py代码的主要用途为:
读取当前文件夹内的对应格式文件列表, 调用DataProcessTools.py内的解析函数获取分块图像
分块图像以file stream(object) list的形式传入
并对上述获得的图像进行拼接获得一张完整的fits文件, 最后将必须的头部信息写入fits完成帧数据处理
'''


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
    completeImage = np.array((childShape[0], childShape[1] * 6))
    for i in range(len(imageList)):
        completeImage[:, i * childShape[1]: (i + 1) * childShape[1] - 1] = imageList[i]
    return completeImage


# 创建fits文件, 将数据, 头部写入文件, 输出到指定目录
def createFits(image, header, outDir):
    tempHDUList = fits.HDUList(fits.PrimaryHDU(image, header))
    tempHDUList.writeto(outDir)


def main():
    with open('jp2/413310.jp2', 'rb') as jp2File:
        arr = decode(jp2File)
        print(arr.shape)


if __name__ == '__main__':
    main()
