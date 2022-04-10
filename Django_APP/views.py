from django.http import HttpResponse
from django.shortcuts import render, redirect

from Django_APP.passwordCheck import simplePasswordCheck as passwordCheck, add_user, send_appointment_message, \
    find_history_order, find_road_name
from Django_APP.load_lot_pre_remain import LotsInfoAndRemain
from Django_APP.recom.recom_launcher import Initializer
from Django_APP.recom.user import User
from Django_APP.recom.locations import Location
from Django_APP.recom.methods import Methods
from Django_APP.recom.user_management import UserManagement
import json
import csv
import numpy as np
import datetime
import random

day = 4
total_user_list = []
first_time = True
result_list = []
start_time_main = datetime.datetime(2018, 12, 11 + day, 19, 0, 0)

lot_file_main = './data/filtered_block76.csv'

user_file_main = './data/user_data_day1_10to7_allday' + str(day) + '.csv'
user_num_file_main = './data/user_num_day1_10to7_allday' + str(day) + '.csv'
check_in_main = './data/76block_number_checkin_allday' + str(day) + '.csv'
check_out_main = './data/76block_number_checkout_allday' + str(day) + '.csv'

init_lon = 113.8911
init_lat = 22.5191
init_time = datetime.datetime.strptime('2018-12-11 19:00:00', '%Y-%m-%d %H:%M:%S')

current_lon = init_lon
current_lat = init_lat
system_time = datetime.datetime.strptime('2018-12-11 19:00:00', '%Y-%m-%d %H:%M:%S')
data_store = None

lot_pre_remain = LotsInfoAndRemain()


def user_init(lon, lat, current_time):
    global initializer
    global APP_user
    global system_time
    global current_lon
    global current_lat
    global first_time
    global total_user_list

    first_time = True

    current_lon = lon
    current_lat = lat

    current_time = current_time
    system_time = current_time
    day = current_time.day - 11
    start_time_main = datetime.datetime(2018, 12, 11 + day, 19, 0, 0)

    date_index = int(current_time.day - 11)
    time_index = int(current_time.minute / 5)
    lot_pre_remain.init_time(current_time)

    lot_file_main = './data/filtered_block76.csv'

    user_file_main = './data/user_data_day1_10to7_allday' + str(day) + '.csv'
    user_num_file_main = './data/user_num_day1_10to7_allday' + str(day) + '.csv'
    check_in_main = './data/76block_number_checkin_allday' + str(day) + '.csv'
    check_out_main = './data/76block_number_checkout_allday' + str(day) + '.csv'
    initializer = Initializer(lot_file_main, user_file_main, user_num_file_main,
                              check_in_main, check_out_main, start_time_main)
    new_user_list = []
    APP_user = initializer.experiment_users.add_new_user_d(65535, lon, lat, start_time_main, "A")
    # APP_user = initializer.experiment_users.all_users_dict[548]
    new_user_list.append(APP_user)
    # ########## add 30 users ############
    # ####################################
    # ####################################
    # ####################################
    # ####################################
    for i in range(30):
        new_user_list.append(initializer.experiment_users.add_new_user())
    total_user_list = new_user_list
    day = current_time.day - 11
    random_seed = 19 * day
    user_len = len(new_user_list)
    len1 = 10
    len2 = 10

    index_list = random.sample(range(user_len), user_len)

    for count, item in enumerate(index_list):
        if count < len1:
            new_user_list[item].group = "A"
        elif count < len1 + len2:
            new_user_list[item].group = "B"
        else:
            new_user_list[item].group = "C"

    random.shuffle(new_user_list)

    for new_user in new_user_list:
        if new_user.id == 65535:
            continue
        random.seed(random_seed)
        random_seed += 1
        new_user.current_time = current_time

        new_user.des_lon_and_lat = Location(lon, lat)
        user_lon_lat = new_user.des_lon_and_lat
        init_lon = user_lon_lat.lon + random.uniform(-70, 70) / 1000.0
        init_lat = user_lon_lat.lat + random.uniform(-70, 70) / 1000.0
        new_user.current_lon_and_lat = Location(init_lon, init_lat)
        new_user.init_lon_and_lat = Location(init_lon, init_lat)
    # ##########end#######################
    # ####################################
    # ####################################
    # ####################################
    # ####################################
    # ####################################

    lon = float(lon)
    lat = float(lat)
    current_lon = lon
    current_lat = lat


def user_update(des_lon, des_lat, request_type):
    global initializer
    global APP_user
    global system_time
    global current_lon
    global current_lat
    global first_time
    global total_user_list
    global result_list

    price_info = '2 dollars per hour.'

    result_list = []

    if des_lon == '113.941351' and des_lat == '22.523518':
        # 麦当劳
        # centos
        des_lon = 113.941351
        des_lat = 22.523018
        # windows
        # des_lon = 113.941225
        # des_lat = 22.522041
    elif des_lon == '113.940008' and des_lat == '22.523612':
        # 正夫口腔
        des_lon = 113.938737
        des_lat = 22.523631
    elif des_lon == '113.944145' and des_lat == '22.523768':
        # 海岸城
        des_lon = 113.942236
        des_lat = 22.521139
    des_lon = float(des_lon)
    des_lat = float(des_lat)
    if first_time is True:
        first_time = False
        des_lon_lat = Location(float(des_lon), float(des_lat))
        change_user_list = initializer.experiment_users.all_users_dict.values()
        for each_user in change_user_list:
            if each_user.id == 65535:
                each_user.init_lon_and_lat = each_user.current_lon_and_lat
                continue
            each_user.des_lon_and_lat = des_lon_lat
            user_lon_lat = each_user.des_lon_and_lat
            init_lon = user_lon_lat.lon + random.uniform(-70, 70) / 1000.0
            init_lat = user_lon_lat.lat + random.uniform(-70, 70) / 1000.0
            each_user.current_lon_and_lat = Location(init_lon, init_lat)
            each_user.init_lon_and_lat = Location(init_lon, init_lat)

        APP_user.des_lon_and_lat = des_lon_lat
        if initializer.experiment_users.a:
            del initializer.experiment_users.a[APP_user.id]
        if initializer.experiment_users.b:
            del initializer.experiment_users.b[APP_user.id]
        if request_type == 'reserveType':
            APP_user.group = "A"
            initializer.experiment_users.a[APP_user.id] = APP_user
            initializer.start(system_time, check_in_main,
                              check_out_main, total_user_list, 0)
            parking_lot = APP_user.parking_lot
            remain = parking_lot.remaining_lots
            if remain <= 0:
                remain = 1
            lon_lat = parking_lot.lon_and_lat
            user_lon_lat = APP_user.current_lon_and_lat
            data = {'name': parking_lot.lot_name,
                    'capacity': parking_lot.lots_num,
                    'occupy': parking_lot.lots_num - remain,
                    'remain': remain,
                    'atitude': str(lon_lat.lat) + ',' + str(lon_lat.lon),
                    'current_atitude': str(user_lon_lat.lat) + ',' + str(user_lon_lat.lon),
                    'price_info': price_info,
                    'time_use': 1,
                    'distance': 1}
            json_data = json.dumps(data, ensure_ascii=False)
            result_list = json_data
            return 'change'
        else:
            APP_user.group = "B"
            initializer.experiment_users.b[APP_user.id] = APP_user
            initializer.start(system_time, check_in_main,
                              check_out_main, total_user_list, 0)
            data = []
            for parking_lot in APP_user.regular_list:
                lon_lat = parking_lot.lon_and_lat
                user_lon_lat = APP_user.current_lon_and_lat
                remain = parking_lot.remaining_lots
                if remain <= 0:
                    remain = 1
                data_item = {'name': parking_lot.lot_name,
                             'capacity': parking_lot.lots_num,
                             'occupy': parking_lot.lots_num - remain,
                             'remain': remain,
                             'atitude': str(lon_lat.lat) + ',' + str(lon_lat.lon),
                             'current_atitude': str(user_lon_lat.lat) + ',' + str(user_lon_lat.lon),
                             'price_info': price_info,
                             'time_use': 1,
                             'distance': 1}
                data.append(data_item)
            json_data = json.dumps(data, ensure_ascii=False)
            result_list = json_data
            return 'change'
    else:
        if APP_user.group == "A":
            last_parking = APP_user.parking_lot
            initializer.start(system_time, check_in_main,
                              check_out_main, None, 0)
            parking_lot = APP_user.parking_lot

            lon_lat = parking_lot.lon_and_lat
            user_lon_lat = APP_user.current_lon_and_lat

            remain = parking_lot.remaining_lots
            if remain <= 0:
                remain = 1
            data = {'name': parking_lot.lot_name,
                    'capacity': parking_lot.lots_num,
                    'occupy': parking_lot.lots_num - remain,
                    'remain': remain,
                    'atitude': str(lon_lat.lat) + ',' + str(lon_lat.lon),
                    'current_atitude': str(user_lon_lat.lat) + ',' + str(user_lon_lat.lon),
                    'price_info': price_info,
                    'time_use': 1,
                    'distance': 1}
            json_data = json.dumps(data, ensure_ascii=False)
            result_list = json_data
            if APP_user.id in initializer.experiment_users.arrived_users_dict.keys():
                return 'success'
            if last_parking.id == parking_lot.id:
                return 'unchange'
            return 'change'
        else:
            last_parking_num = APP_user.regular_list
            initializer.start(system_time, check_in_main,
                              check_out_main, None, 0)
            parking_lot_num = APP_user.regular_list

            data = []
            for parking_lot in APP_user.regular_list:
                lon_lat = parking_lot.lon_and_lat
                user_lon_lat = APP_user.current_lon_and_lat
                remain = parking_lot.remaining_lots
                if remain <= 0:
                    remain = 1
                data_item = {'name': parking_lot.lot_name,
                             'capacity': parking_lot.lots_num,
                             'occupy': parking_lot.lots_num - remain,
                             'remain': remain,
                             'current_atitude': str(user_lon_lat.lat) + ',' + str(user_lon_lat.lon),
                             'atitude': str(lon_lat.lat) + ',' + str(lon_lat.lon),
                             'price_info': price_info,
                             'time_use': 1,
                             'distance': 1}
                data.append(data_item)
            json_data = json.dumps(data, ensure_ascii=False)
            result_list = json_data
            if APP_user.id in initializer.experiment_users.arrived_users_dict.keys():
                return 'success'
            if parking_lot_num[0].id == last_parking_num[0].id:
                return 'unchange'
            return 'change'


def init_setting(request):
    global initializer
    global APP_user
    global system_time
    global init_lon
    global init_lat

    user_init(init_lon, init_lat, system_time)
    date_change = init_time
    date_index = date_change.day - 11
    time_index = int(date_change.minute / 5)
    lot_pre_remain.init_time(system_time)
    return render(request, "init_setting.html", {"data": "Done!"})


def park_data(request):
    output_data = []
    for item in lot_pre_remain.lot_basic_info_list:
        data_item = {"name": item["lot_name"],
                     "id": item["lot_id"],
                     "capacity": item["lots_num"],
                     "occupy": item["lots_num"] - item["truth_val"],
                     "remain": item["truth_val"],
                     "atitude": (str(item["latitude"]) + "," + str(item["longitude"]))}
        output_data.append(data_item)
    data = json.dumps(output_data, ensure_ascii=False)
    return render(request, "park_data.html", {"data": data})


def renew(request):
    global system_time
    global init_lon
    global init_lat
    user_init(init_lon, init_lat, system_time)
    return render(request, "renew.html", {"data": 'done'})


def logIn_check(request, user_name, user_password):
    judgement = passwordCheck(user_name, user_password)
    return render(request, "logInCheck.html", {"data": judgement})


def register(request, user_name, user_password):
    add_user(user_name, user_password)
    return render(request, "register.html", {"data": "/logInCheck/" + user_name + "/" + user_password})


def normal_type(request, des_lon, des_lat):
    # des_lon = float(des_lon)
    # des_lat = float(des_lat)
    return_type = user_update(des_lon, des_lat, 'normalType')
    return render(request, 'normalType.html', {"data": return_type})


def reserve_type(request, des_lon, des_lat):
    # des_lon = float(des_lon)
    # des_lat = float(des_lat)
    return_type = user_update(des_lon, des_lat, 'reserveType')
    return render(request, 'reserveType.html', {"data": return_type})


def predict(request, data_name):
    data_item = None
    for lot_item in lot_pre_remain.lot_basic_info_list:
        if data_name == lot_item["lot_name"]:
            data_item = lot_item
            break
    output_data = {"name": data_item["lot_name"],
                   "capacity": data_item["lots_num"],
                   "occupy": data_item["lots_num"] - data_item["truth_val"],
                   "remain": data_item["truth_val"],
                   "atitude": (str(data_item["latitude"]) + "," + str(data_item["longitude"])),
                   "predict": data_item['pre_val']}
    data = json.dumps(output_data, ensure_ascii=False)
    return render(request, "predict.html", {"data": data})


def new_user(request, lon, lat, current_time):
    lon = float(lon)
    lat = float(lat)
    current_time = datetime.datetime.strptime(current_time, '%Y-%m-%d-%H:%M:%S')
    user_init(lon, lat, current_time)
    print(current_time)
    return render(request, "set.html")


def start(request, des_lon, des_lat, request_type):
    global APP_user
    global system_time
    global initializer
    global data_store
    global result_list
    if request_type != "change":

        if request_type == 'reserve':
            json_data = result_list
            return render(request, "reserve.html", {'data': json_data})
        elif request_type == 'normal':
            json_data = result_list
            return render(request, "normal.html", {'data': json_data})
    elif request_type == "change":
        if APP_user.group == "A":
            json_data = result_list
            return render(request, "reserve.html", {'data': json_data})

        else:
            json_data = result_list
            return render(request, "normal.html", {'data': json_data})


def second_change(request):
    global data_store
    return render(request, "changeDisplay.html", {'data': data_store})


def baidu(request):
    in_num = np.load("./data/outcao_remain.npz")
    truth_data = in_num['truth']

    each_day_list = []
    for j in range(76):
        each_lot_list = []
        for k in range(12):
            each_lot_list.append(int(truth_data[12][j][k]))
        each_day_list.append(each_lot_list)

    street_info = csv.reader(open("./data/filtered_block76.csv", 'r', encoding='utf-8'))
    next(street_info)
    lots_num = []
    lot_name = []
    lot_id = []
    for info in street_info:
        lots_num.append(int(info[7]))
        lot_name.append(info[2])
        lot_id.append(info[0])

    ave_list = []
    for i, lots_remain_list in enumerate(each_day_list):
        ave_item = 0
        for remain_item in lots_remain_list:
            ave_item += (lots_num[i] - int(remain_item)) / lots_num[i]
        ave_item /= len(lots_remain_list)
        ave_list.append(ave_item)

    street_info = csv.reader(open("./data/filtered_block76.csv", 'r', encoding='utf-8'))
    next(street_info)

    data = []
    for i, item in enumerate(street_info):
        lot_name = item[2]
        longitude = float(item[5])
        latitude = float(item[6])
        data_item = [lot_name + ":" + str(ave_list[i]), str(longitude), str(latitude)]
        data.append(data_item)

    return render(request, "baidu.html", {"data": json.dumps(data)})


def login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username, password)
        return redirect('/index/')
    return render(request, 'login/login.html')


# def logIn_check(request, user_name, user_password):
#     judgement = passwordCheck(user_name, user_password)
#     return render(request, "logInCheck.html", {"data": judgement})
def appointment(request, user_name, des_lon, des_lat, reserve_time):
    send_appointment_message(user_name, des_lon, des_lat, reserve_time)
    return render(request, "appointment.html")


def querySet_to_list(qs):
    return [dict(q) for q in qs]


# 没写完
def orderhistory(request, user_name):
    orderData = find_history_order(user_name)
    if orderData == 0:
        data = 0
    else:
        for orderDataList in querySet_to_list(orderData.values()):
            pass
        print(orderDataList)
        output_data = []
        for item in querySet_to_list(orderData.values()):
            roadName = find_road_name(item["Road_segment_id_id"])
            data_item = {"订单编号": item["Parkingdata_id"],
                         "订单时间": str(item["service_init_time"]),
                         "停车路段名字": roadName,
                         "停车时间": item["parking_duration"],
                         "收费": item["parking_duration"]
                         }
            output_data.append(data_item)
        # data = json.dumps(output_data, ensure_ascii=False)
    return render(request, "park_data.html", {"data": output_data})
    # return None


def wallet(request):
    return None
