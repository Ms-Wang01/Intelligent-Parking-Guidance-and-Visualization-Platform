import csv
from Django_APP.recom.methods import Methods

lot_info_file = 'D:\\LearningMaterial\\数据\\停车数据\\有用的数据\\experiment\\lots.csv'
lot_info = csv.reader(open(lot_info_file, 'r', encoding='utf-8'))
lot_lon_lat = []

for item in lot_info:
    lot_lon_lat_temp = [float(item[1]), float(item[2])]
    lot_lon_lat.append(lot_lon_lat_temp)

user_file_main = 'D:\\LearningMaterial\\数据\\停车数据\\有用的数据\\' \
                 'experiment\\user_data_day1_4to6_allday0.csv'
user_info = csv.reader(open(user_file_main, 'r', encoding='utf-8'))

useful_lots = csv.reader(open('D:\\LearningMaterial\\数据'
                                      '\\停车数据\\有用的数据\\experiment\\'
                                      'useful_lots.csv', 'r', encoding='utf-8'))
useful_lon_lat = []
for item in useful_lots:
    temp = [float(item[0]), float(item[1])]
    useful_lon_lat.append(temp)
dis = 0
count = 0
for day in range(20):
    user_file_main = 'D:\\LearningMaterial\\数据\\停车数据\\有用的数据\\' \
                     'experiment\\user_data_day1_4to6_allday' + str(day) + '.csv'
    user_info = csv.reader(open(user_file_main, 'r', encoding='utf-8'))
    for item in user_info:
        is_useful = False
        for lon_lat in useful_lon_lat:
            if float(item[11]) == lon_lat[0] and float(item[12]) == lon_lat[1]:
                is_useful = True
                break
        if not is_useful:
            continue
        lon = float(item[7])
        lat = float(item[8])
        cloest_set = []
        for lot in lot_lon_lat:
            cloest_set.append(Methods.dis_cal(lon, lat, lot[0], lot[1]))
        cloest_set.sort()
        dis += cloest_set[0] / 0.1
        count += 1

print(dis / count)
