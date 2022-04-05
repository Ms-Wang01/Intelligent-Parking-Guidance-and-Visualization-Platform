import csv
import datetime
import random
import Django_APP.recom.locations
from Django_APP.recom.methods import Methods
from Django_APP.recom.parking_lot import ParkingLots
from Django_APP.recom.locations import Location

class LotManagement:

    def __init__(self, file_name, check_in, check_out, start_time, time):
        # 每个lot id对应Lot对象
        # 高
        self.experiment_lots_index = [24, 26, 27, 30, 34, 40, 41]
        # 中
        # self.experiment_lots_index = [57, 75, 45, 9, 18, 21, 15]
        # 低
        # self.experiment_lots_index = [47, 51, 52, 54, 59, 61, 64, 69]
        self.lot_index = dict()
        self.lot_dis_index = []
        self.each_lot_occupy = dict()
        self.des_lon_lat = []
        day = start_time.day
        self.init_lots_info(file_name, day, time)
        self.occupy_init(check_in, check_out, start_time)

    # 读取每条路段信息
    def init_lots_info(self, file_name, day, time):

        close_set = []
        random_seed = 3 * day * time

        lot_id_count = 0

        street_info = csv.reader(open(file_name, 'r', encoding='utf-8'))
        next(street_info)
        for info in street_info:
            new_lot = ParkingLots(lot_id=info[0], lot_name=info[2], longitude=info[5], latitude=info[6],
                                  lots_num=info[7], remaining_lots=info[7])
            # new_lot.close_set = close_set[new_lot.id]
            if new_lot.id in self.experiment_lots_index:
                new_lot.id = lot_id_count
                self.lot_index[lot_id_count] = new_lot
                lot_id_count += 1
        for lot_id in range(lot_id_count):
            lot_lon_lat = self.lot_index[lot_id].lon_and_lat
            closest_lot_list = []
            for neighbor_id in range(lot_id_count):
                if lot_id == neighbor_id:
                    closest_lot_list.append(9999)
                    continue
                neighbor_lon_lat = self.lot_index[neighbor_id].lon_and_lat
                dis = Methods.dis_cal(lot_lon_lat.lon, lot_lon_lat.lat,
                                      neighbor_lon_lat.lon, neighbor_lon_lat.lat)
                closest_lot_list.append(dis)
            closest_lot_list = sorted(enumerate(closest_lot_list), key=lambda x: x[1])
            for i in range(3):
                self.lot_index[lot_id].close_set.append(closest_lot_list[i][0])

            for i in range(0):

                while True:
                    random.seed(random_seed)
                    random_seed += 1
                    deslon = lot_lon_lat.lon + random.uniform(-3, 3) / 1000.0
                    deslat = lot_lon_lat.lat + random.uniform(-2, 2) / 1000.0
                    des_dis = Methods.dis_cal(deslon, deslat,
                                              lot_lon_lat.lon, lot_lon_lat.lat)
                    threshold1 = Methods.dis_cal(0, 0, 2 / 1000, 2 / 1000)
                    threshold2 = Methods.dis_cal(0, 0, 0 / 1000, 0 / 1000)
                    if threshold2 <= des_dis <= threshold1:
                        self.des_lon_lat.append(Location(deslon, deslat))
                        break
        while True:
            random.seed(random_seed)
            random_seed += 1
            # 高
            
            deslon = 113.9429 + random.uniform(-3, 3) / 1000.0
            deslat = 22.5233 + random.uniform(-2, 2) / 1000.0
            des_dis = Methods.dis_cal(deslon, deslat,
                                      113.9429, 22.5233)
            threshold1 = Methods.dis_cal(0, 0, 4 / 1000, 4 / 1000)
            threshold2 = Methods.dis_cal(0, 0, 0 / 1000, 0 / 1000)
            if threshold2 <= des_dis <= threshold1:
                self.des_lon_lat.append(Location(deslon, deslat))
                break
            
            # 中 113.933643,22.517125
            """
            deslon = 113.933643 + random.uniform(-2, 0.1) / 1000.0
            deslat = 22.517125 + random.uniform(-6, 3) / 1000.0
            des_dis = Methods.dis_cal(deslon, deslat,
                                      113.933643, 22.517125)
            threshold1 = Methods.dis_cal(0, 0, 4 / 1000, 4 / 1000)
            threshold2 = Methods.dis_cal(0, 0, 0 / 1000, 0 / 1000)
            if threshold2 <= des_dis <= threshold1:
                self.des_lon_lat.append(Location(deslon, deslat))
                break
            
            # 低
            deslon = 113.956302	+ random.uniform(-6, 7) / 1000.0
            deslat = 22.546269 + random.uniform(-6, 1) / 1000.0
            des_dis = Methods.dis_cal(deslon, deslat,
                                      113.956302, 22.546269)
            threshold1 = Methods.dis_cal(0, 0, 4 / 1000, 4 / 1000)
            threshold2 = Methods.dis_cal(0, 0, 0 / 1000, 0 / 1000)
            if threshold2 <= des_dis <= threshold1:
                self.des_lon_lat.append(Location(deslon, deslat))
                break
            """

    def occupy_init(self, check_in, check_out, start_time):
        start_time = start_time + datetime.timedelta(minutes=-5)
        check_in_info = csv.reader(open(check_in, 'r', encoding='utf-8'))
        in_time_list = next(check_in_info)
        in_time_list = in_time_list[1: len(in_time_list)]

        in_time = 0
        for item in in_time_list:
            item_date = datetime.datetime.strptime(item, '%Y-%m-%d %H:%M:%S')
            if start_time <= item_date:
                break
            in_time += 1

        check_out_info = csv.reader(open(check_out, 'r', encoding='utf-8'))
        out_time_list = next(check_out_info)
        out_time_list = out_time_list[1: len(out_time_list)]

        out_time = 0
        for item in out_time_list:
            item_date = datetime.datetime.strptime(item, '%Y-%m-%d %H:%M:%S')
            if start_time <= item_date:
                break
            out_time += 1

        lots_in_num = []
        for in_item_list in check_in_info:
            in_item_list = in_item_list[1:len(in_item_list)]
            each_lot_in_num = 0
            for in_item_index in range(in_time):
                each_lot_in_num += int(in_item_list[in_item_index])
            lots_in_num.append(each_lot_in_num)

        lots_out_num = []
        for out_item_list in check_out_info:
            out_item_list = out_item_list[1:len(out_item_list)]
            each_lot_out_num = 0
            for out_item_index in range(out_time):
                each_lot_out_num += int(out_item_list[out_item_index])
            lots_out_num.append(each_lot_out_num)

        lots_occupy = []
        for each_lot_in_num, each_lot_out_num in zip(lots_in_num, lots_out_num):
            lots_occupy.append((each_lot_in_num - each_lot_out_num))
        lot_id_count = 0
        for index, each_lot_occupy in enumerate(lots_occupy):
            if index in self.experiment_lots_index:
                self.lot_index[lot_id_count].remaining_lots = int(self.lot_index[lot_id_count].lots_num * 1)
                self.lot_index[lot_id_count].remaining_lots -= each_lot_occupy
                if self.lot_index[lot_id_count].remaining_lots < 0:
                    self.lot_index[lot_id_count].remaining_lots = 0
                lot_id_count += 1

    def flow_in_out_num(self, check_in, check_out, current_time):
        # 当前时刻不在记录的时间范围内时，设置76个0流入和流出
        street_segment_num = 76

        # #### check in #### #
        check_in_info = csv.reader(open(check_in, 'r', encoding='utf-8'))
        check_in_time_list = next(check_in_info)
        check_in_time_list = check_in_time_list[1:]
        in_index = 0
        current_date_time = None
        # 将时间定为到当前时间
        for time in check_in_time_list:
            current_date_time = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
            if current_time > current_date_time:
                in_index += 1
            elif current_time < current_date_time:
                in_index = len(check_in_time_list)
                break
            else:
                break
        # 读取当前时刻的流入
        if in_index >= len(check_in_time_list):
            # num_in_time_list = [0] * len(check_in_time_list)
            num_in_time_list = [0] * street_segment_num
        else:
            num_in_time_list = []
            while True:
                check_in_list = next(check_in_info, None)
                if check_in_list is None:
                    break
                check_in_list = check_in_list[1:]

                num_in_time = int(check_in_list[in_index])
                num_in_time_list.append(num_in_time)

        # #### check out #####
        check_out_info = csv.reader(open(check_out, 'r', encoding='utf-8'))
        check_out_time_list = next(check_out_info)
        check_out_time_list = check_out_time_list[1:]
        out_index = 0
        for time in check_out_time_list:
            current_date_time = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
            if current_time > current_date_time:
                out_index += 1
            elif current_time < current_date_time:
                out_index = len(check_out_time_list)
                break
            else:
                break

        if out_index == len(check_out_time_list):
            # num_out_time_list = [0] * len(check_out_time_list)
            num_out_time_list = [0] * street_segment_num
        elif current_time != current_date_time:
            num_out_time_list = [0] * street_segment_num
        else:
            num_out_time_list = []
            while True:
                check_out_list = next(check_out_info, None)
                if check_out_list is None:
                    break
                check_out_list = check_out_list[1:]

                num_out_time = int(check_out_list[out_index])
                num_out_time_list.append(num_out_time)
        # in - out 获得用户数量差值
        user_addition = 0

        lot_id_count = 0
        in_temp = []
        out_temp = []
        for i, [in_num, out_num] in enumerate(zip(num_in_time_list, num_out_time_list)):
            if i in self.experiment_lots_index:
                in_temp.append(in_num)
                out_temp.append(out_num)
        num_in_time_list = in_temp
        num_out_time_list = out_temp
        for lot_num, [in_num, out_num] in enumerate(zip(num_in_time_list, num_out_time_list)):
            lot = self.lot_index[lot_num]
            lot.remaining_lots -= int(in_num)

            user_addition += in_num

            lot.remaining_lots += out_num

            user_addition -= out_num

            if lot.remaining_lots < 0:
                diff = 0 - lot.remaining_lots
                lot.remaining_lots += diff
                user_addition -= diff
            if lot.remaining_lots > lot.lots_num:
                diff = lot.remaining_lots - lot.lots_num
                lot.remaining_lots -= diff
                user_addition += diff

        return user_addition

    def get_lot_index(self):
        return self.lot_index

    def regular(self, lot, user):
        lot.virtual_recommendation_num += 1
        lot.regular_user_list.append(user)

    def reserved(self, lot):
        lot.remaining_lots -= 1


    @staticmethod
    def lot_lon_lat(lot):
        return lot.lon_and_lat

    @staticmethod
    def get_regular_users(lot):
        return lot.regular_user_list


































