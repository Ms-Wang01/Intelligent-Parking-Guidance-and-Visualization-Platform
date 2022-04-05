import csv
import datetime
import numpy as np
from math import ceil, floor

class PreVal:
    LOT_OCCUPY_RATIO = dict()
    TIME_SLOT = 5
    # COMING_UN_RESERVE = [0] * 12
    @staticmethod
    def pre_val_update_new(check_in, remain, current_time):
        useful_lot_index = [11, 24, 26, 27, 30, 34, 40, 41, 46]
        ##### check in #####

        check_in_npz = np.load(check_in)
        check_in_data = check_in_npz['data'].tolist()
        remain_npz = np.load(check_in)
        remain_data = remain_npz['data'].tolist()

        start_date = '2018-12-11'
        start_day = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        day_diff = int(current_time.day - start_day.day)
        time_diff = int(current_time.minute / 5)

        check_in_info = check_in_data[day_diff * time_diff + time_diff]
        remain_info = remain_data[day_diff * time_diff + time_diff]

        PreVal.LOT_OCCUPY_RATIO.clear()
        for lot_index, [total_in_lsit, total_remain_list] in enumerate(zip(check_in_info, remain_info)):
            individual_in_list = []
            individual_out_list = []
            last_remain = 0
            for in_val, remain_val in zip(total_in_lsit, total_remain_list):
                int_in_val = ceil(in_val)
                int_remain_val = ceil(remain_val)
                last_remain = int_remain_val
                int_out = int_remain_val - last_remain - int_in_val
                if int_out < 0:
                    int_out = 0
                #individual_in_list.append(int_in_val)
                #individual_out_list.append(int_out)
                individual_in_list.append(0)
                individual_out_list.append(0)
            future_coming_user = individual_in_list
            future_leaving_user = individual_out_list
            PreVal.LOT_OCCUPY_RATIO[lot_index] = [future_coming_user, future_leaving_user]


    @staticmethod
    def pre_val_update(check_in, check_out, current_time):
        useful_lot_index = [11, 24, 26, 27, 30, 34, 40, 41, 46]
        #useful_lot_index = [25, 30, 32, 33, 35, 39, 41]
        ##### check in #####
        check_in_info = csv.reader(open(check_in, 'r', encoding='utf-8'))
        check_in_time_list = next(check_in_info)
        check_in_time_list = check_in_time_list[1:]
        in_index = 0
        for time in check_in_time_list:
            date_time = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
            if date_time < current_time:
                in_index += 1
            else:
                break

        pre_in_time_list = []
        if in_index == len(check_in_time_list):
            pre_in_time_list = [[0 for i in range(12)]for j in range(76)]
        else:
            while True:
                check_in_list = next(check_in_info, None)
                if check_in_list is None:
                    break
                check_in_list = check_in_list[1:]
                pre_in_time = []
                date_time = datetime.datetime.strptime(check_in_time_list[in_index], '%Y-%m-%d %H:%M:%S')
                current_time_add = current_time
                offset = 0
                for pre_time_index in range(12):
                    if date_time > current_time_add:
                        current_time_add = current_time_add + datetime.timedelta(minutes=5)
                        pre_in_time.append(0)
                        offset += 1
                    else:
                        target_index = in_index + pre_time_index - offset
                        if target_index < len(check_in_list):
                            pre_in_time.append(int(check_in_list[target_index]))
                        else:
                            pre_in_time.append(0)
                pre_in_time_list.append(pre_in_time)


        ##### check out #####
        check_out_info = csv.reader(open(check_out, 'r', encoding='utf-8'))
        check_out_time_list = next(check_out_info)
        check_out_time_list = check_out_time_list[1:]
        out_index = 0
        for time in check_out_time_list:
            date_time = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
            if date_time < current_time:
                out_index += 1
            else:
                break
        pre_out_time_list = []
        if out_index == len(check_out_time_list):
            pre_out_time_list = [[0 for i in range(12)]for j in range(76)]
        else:
            while True:
                check_out_list = next(check_out_info, None)
                if check_out_list is None:
                    break
                check_out_list = check_out_list[1:]
                pre_out_time = []
                date_time = datetime.datetime.strptime(check_out_time_list[out_index], '%Y-%m-%d %H:%M:%S')
                current_time_add = current_time
                offset = 0
                for pre_time_index in range(12):
                    if date_time > current_time_add:
                        current_time_add = current_time_add + datetime.timedelta(minutes=5)
                        pre_out_time.append(0)
                        offset += 1
                    else:
                        target_index = out_index + pre_time_index - offset
                        if target_index < len(check_out_list):
                            pre_out_time.append(int(check_out_list[target_index]))
                        else:
                            pre_out_time.append(0)
                pre_out_time_list.append(pre_out_time)

        PreVal.LOT_OCCUPY_RATIO.clear()
        lot_id_count = 0
        for lot_index, [in_value, out_value] in enumerate(zip(pre_in_time_list, pre_out_time_list)):
            if lot_index not in useful_lot_index:
                continue
            future_coming_user = in_value
            future_leaving_user = out_value
            PreVal.LOT_OCCUPY_RATIO[lot_id_count] = [future_coming_user, future_leaving_user]
            lot_id_count += 1
