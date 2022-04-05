import numpy as np
import csv
import datetime
import Django_APP.recom.cost_cal

class LotsInfoAndRemain:
    def __init__(self):
        self.lot_remain_truth_info_list = []
        self.lot_remain_pre_info_list = []
        self.lot_basic_info_list = []
        self.name_to_id_dict = {}
        self.unique_lots = [1, 3, 4, 6, 9, 11, 13, 15, 17, 18, 20, 21, 23, 24, 26,
                            27, 30, 32, 34, 35, 38, 40, 41, 43, 44, 45, 47, 51,
                            52, 54, 57, 58, 59, 61, 62, 64, 65, 67, 69, 74, 75]

        lots_num = len(self.unique_lots)
        in_num = np.load("./data/outcao_remain.npz")
        in_data = in_num['data']
        truth_data = in_num['truth']
        day_num = 21
        time_slot = 12
        days_list = []
        truth_list = []

        for i in range(day_num):
            each_day_list = []
            for j in range(time_slot):
                lot_list = []
                for k in self.unique_lots:
                    each_lot_list = []
                    for l in range(time_slot):
                        each_lot_list.append(int(in_data[i * 12 + j][k][l] + 0.5))
                    lot_list.append(each_lot_list)
                each_day_list.append(lot_list)
            days_list.append(each_day_list)

        for i in range(day_num):
            each_day_list = []
            for j in self.unique_lots:
                each_lot_list = []
                for k in range(time_slot):
                    each_lot_list.append(int(truth_data[i * 12][j][k]))
                each_day_list.append(each_lot_list)
            truth_list.append(each_day_list)

        self.lot_remain_truth_info_list = truth_list
        self.lot_remain_pre_info_list = days_list
        self.lot_basic_info_list = []
        street_info = csv.reader(open("./data/filtered_block76.csv", 'r', encoding='utf-8'))
        next(street_info)
        lot_count = 0
        for info in street_info:
            lot_id = int(info[0])
            if lot_id not in self.unique_lots:
                continue
            
            lot_name = info[2]
            longitude = float(info[5])
            latitude = float(info[6])
            lots_num = int(info[7])
            self.name_to_id_dict[lot_name] = lot_id
            info_dict = {"lot_id": lot_count, "lot_name": lot_name,
                         "longitude": longitude, "latitude": latitude,
                         "lots_num": lots_num, "pre_val_list": [],
                         "current_slot": 0, "pre_val": [],
                         "truth_val_list": [], "truth_val": [],
                         "lot_real_id": lot_id}
            self.lot_basic_info_list.append(info_dict)
            lot_count += 1
        init_time = datetime.datetime.strptime('2018-12-11 19:00:00', '%Y-%m-%d %H:%M:%S')
        self.init_time(init_time)

    def init_time(self, current_time):
        date_index = int(current_time.day - 11)
        time_index = int(current_time.minute / 5)
        day_pre_val_list = self.lot_remain_pre_info_list[date_index]
        day_truth_val_list = self.lot_remain_truth_info_list[date_index]
        for each_lot in self.lot_basic_info_list:
            lot_id = each_lot['lot_id']
            lot_pre_val_list = []
            for each_slot in range(time_index, 12):
                lot_pre_val_list.append(day_pre_val_list[each_slot][lot_id])

            lot_truth_val_list = []
            for each_slot in range(time_index, 12):
                lot_truth_val_list.append(day_truth_val_list[lot_id][each_slot])

            each_lot["pre_val_list"] = lot_pre_val_list
            each_lot["truth_val_list"] = lot_truth_val_list
            each_lot["current_slot"] = 0
            each_lot["pre_val"] = lot_pre_val_list[0]
            each_lot["truth_val"] = lot_truth_val_list[0]

    def update_time(self):
        for each_lot in self.lot_basic_info_list:
            if each_lot["current_slot"] < 11:
                 each_lot["current_slot"] += 1
            each_lot["pre_val"] = each_lot["pre_val_list"][each_lot["current_slot"]]
            each_lot["truth_val"] = each_lot["real_val_list"][each_lot["current_slot"]]

