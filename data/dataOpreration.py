import pandas as pd
import numpy as np
import random


def dataProcess(dataDir):
    initData = pd.read_csv(dataDir)
    data = initData
    columnNum = data.shape[1]
    data = data[data.columns.values[columnNum - 2: columnNum]]
    dataList = [[float(data.columns.values[0]), float(data.columns.values[1])]] + data.values.tolist()
    dataList = [[round(item2, 5) for item2 in item1] for item1 in dataList]
    # print('dataList and its length:')
    # print(dataList)
    # print(len(dataList))
    # print()

    data = pd.read_csv('filtered_block76.csv')
    columnNum = data.shape[1]
    filterData = data[data.columns.values[columnNum - 3: columnNum - 1]].values.tolist()
    filterData = [[round(item2, 5) for item2 in item1] for item1 in filterData]
    # print('filterData and its length:')
    # print(filterData)
    # print(len(filterData))
    # print()

    # print('[the position found, the number of position, the random number to be added, the finial position that will '
    #       'be stored:]')
    result = []
    resultNum = []
    initResult = []
    for item in dataList:
        try:
            num = filterData.count(item)
            position = filterData.index(item)
            resultNum.append(num)
            printList = [position]
            initResult.append(position)
            randomNum = 0
            if num != 1:
                randomNum = random.randint(0, num)
                position = position + randomNum
            result.append(position)
            printList.extend([num, randomNum, position])
            # print(printList)

        except:
            result.append(-1)
            print('shit')

    # print()
    # print('The initial position that found:')
    # print(initResult)
    # print()
    # print('The finial result and its length:')
    # print(result)
    # print(len(result))
    indexName = result[0]
    newData = initData
    newData[indexName] = result[1:]
    # print(newData)
    newData.to_csv(dataDir)
    return dataDir


if __name__ == '__main__':
    # dataDirName1 = 'user_data_day1_4to6_allday'
    # dataDirName2 = '.csv'
    # for i in range(20):
    #     num = str(i)
    #     dataDirName = dataDirName1 + num + dataDirName2
    #     print(dataProcess(dataDirName))


    dataDirName1 = 'user_data_day1_10to7_allday'
    dataDirName2 = '.csv'
    for i in range(20):
        num = str(i)
        dataDirName = dataDirName1 + num + dataDirName2
        print(dataProcess(dataDirName))
