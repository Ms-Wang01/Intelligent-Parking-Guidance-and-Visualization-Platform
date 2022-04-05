from math import floor, ceil
import datetime
import math
import numpy as np
import csv
import random
from Django_APP.recom.cost_cal import CostCal
from Django_APP.recom.prediction_val import PreVal
from Django_APP.recom.lot_management import LotManagement
from Django_APP.recom.user_management import UserManagement
from Django_APP.recom.methods import Methods
from Django_APP.recom.locations import Location
import matplotlib.pyplot as plt
import time


class Launcher:

    def __init__(self, lot_file, user_file, user_num_file, check_in, check_out,
                 start_time, time, occ_por):
        self.id_path = []
        self.portion_A = 0
        self.portion_B = 0
        self.experiment_lots = LotManagement(lot_file, check_in, check_out,
                                             start_time, time)
        self.experiment_users = UserManagement(user_file, user_num_file, start_time)
        Methods.occ_por = occ_por
        occ_remain_list = []
        Methods.lot_occ_num_lim_list = []
        for each_lot in self.experiment_lots.lot_index.values():
            Methods.lot_occ_num_lim_list.append(int(each_lot.remaining_lots * occ_por))

    def start(self, start_time, end_time, check_in_file, check_out_file,
              experiment_type, time):
        current_time = start_time
        user_num = 0
        coming_num = 0
        occupy = []
        for i in range(76):
            occupy.append([])
        while current_time < end_time:

            new_user_list = []
            # 更新之后12个时隙的预测占用值
            PreVal.pre_val_update(check_in_file, check_out_file, start_time)

            # 获得每个时隙来的用户数量
            coming_user_num = self.experiment_users.\
                get_user_num_in_each_slot(current_time)
            if coming_user_num is None:
                break
            # 新加入用户为当前时隙与上一时隙间到达，因此应用上一时隙的占用信息
            for i in range(coming_user_num):
                new_user_list.append(self.experiment_users.add_new_user())

            if new_user_list:
                day = current_time.day
                random_seed = 19 * day * time
                user_len = len(new_user_list)
                len1 = int(user_len / 3)
                len2 = int(user_len / 3)

                len1 = 0
                len2 = 0
                #len1 = int(user_len / 2)
                len3 = user_len - len1 - len2
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
                    random.seed(random_seed)
                    random_seed += 1
                    new_user.current_time = current_time
                    des_index = random.randint(0, len(self.experiment_lots.des_lon_lat) - 1)
                    new_user.des_lon_and_lat = self.experiment_lots.des_lon_lat[des_index]
                    user_lon_lat = new_user.des_lon_and_lat
                    init_lon = user_lon_lat.lon + random.uniform(-70, 70) / 1000.0
                    init_lat = user_lon_lat.lat + random.uniform(-70, 70) / 1000.0
                    new_user.current_lon_and_lat = Location(init_lon, init_lat)
                    new_user.init_lon_and_lat = Location(init_lon, init_lat)

            for each_lot in self.experiment_lots.lot_index.values():
                each_lot.virtual_recommendation_num = 0

            self.experiment_execute(current_time, experiment_type,
                                    new_user_list)

            # user variation num储存了flow in out 用户变化的值
            user_variation_num = self.experiment_lots.\
                flow_in_out_num(check_in_file, check_out_file, current_time)
            # 更改用户总数量

            self.experiment_users.total_user_num_variation(user_variation_num)
            # 更新未到达停车位用户的位置，更新已到达停车位用户的占用情况（是否应该离开）
            if experiment_type == "TITS":
                [a, b] = CostCal.status_update(self.experiment_users, current_time, experiment_type)
                self.portion_A += a
                self.portion_B += b
            else:
                CostCal.status_update(self.experiment_users, current_time, experiment_type)
            # 周期更新

            if experiment_type == "D2":
                for user_item in self.experiment_users.group_a.values():
                    if user_item.parking_lot.remaining_lots < \
                            user_item.parking_lot.lots_num:
                        user_item.parking_lot.remaining_lots += 1
                wait_and_reserved_group = self.experiment_users. \
                    decision_point_recommendation_users()
                self.experiment_execute(current_time, experiment_type,
                                        wait_and_reserved_group)
            elif experiment_type == "TITS":
                for user_item in self.experiment_users.group_a.values():
                    if user_item.parking_lot.remaining_lots < \
                            user_item.parking_lot.lots_num:
                        user_item.parking_lot.remaining_lots += 1
                for user_item in self.experiment_users.group_b.values():
                    if user_item.parking_lot.remaining_lots < \
                            user_item.parking_lot.lots_num:
                        user_item.parking_lot.remaining_lots += 1
                wait_and_reserved_group = self.experiment_users. \
                    decision_point_recommendation_users_T()
                self.experiment_execute(current_time, experiment_type,
                                        wait_and_reserved_group)
            else:
                wait_group = []
                for user in self.experiment_users.wait_group.values():
                    wait_group.append(user)
                self.experiment_users.wait_group.clear()
                self.experiment_execute(current_time, experiment_type,
                                        wait_group)

            user_num += user_variation_num
            
            coming_num += coming_user_num

            current_time = current_time + datetime.timedelta(minutes=5)

            for i in range(len(self.experiment_lots.experiment_lots_index)):
                lot = self.experiment_lots.lot_index[i]
                lot_occ = lot.remaining_lots / lot.lots_num
                occupy[i].append(1-lot_occ)


        return []

    def experiment_execute(self, current_time, experiment_type,
                           new_user_list=None, e_val=0):

        if new_user_list is None:
            return
        # reserved, regular, NG
        new_group_a = []
        new_group_b = []
        new_group_c = []

        # 用户第一次进入系统，立即推荐车位
        for each_user in new_user_list:
            if each_user.group == "A":
                new_group_a.append(each_user)
            if each_user.group == "B":
                new_group_b.append(each_user)
            if each_user.group == "C":
                new_group_c.append(each_user)
        app_portion = self.experiment_users.system_user_portion()
        if experiment_type == "D2":

            # 先regular 再 reserved 再regular，最后NG

            # ###################
            # ###################
            # ###################
            # ###################
            # ###################
            # 虚拟分配regular
            # ###################
            # ###################
            # ###################
            # ###################
            # ###################
            time_ave = 0
            user_count = 0
            for each_user in new_group_b:

                result_lot_list = CostCal.regular_cost(each_user, self.experiment_lots,
                                                  self.experiment_users,
                                                  current_time, app_portion)
                result_lot = result_lot_list[0]
                if result_lot is None:
                    print(each_user.id)
                    continue

                lot_lon_lat = self.experiment_lots.lot_lon_lat(result_lot)
                user_lon_lat = self.experiment_users.\
                    get_current_user_lon_lat(each_user)

                dis = Methods.dis_cal(lot_lon_lat.lon, lot_lon_lat.lat,
                                      user_lon_lat.lon, user_lon_lat.lat)
                arrival_time = current_time + datetime.timedelta(minutes=dis/0.5)
                self.experiment_lots.regular(result_lot, each_user)


            # ###################
            # ###################
            # ###################
            # ###################
            # ###################
            # 分配reserved
            # ###################
            # ###################
            # ###################
            # ###################
            # ###################
            reserve_list = []

            # 计算到各个Lot的cost
            for each_user in new_group_a:
                
                
                user_list = []
                unreachable_lot = each_user.unreachable_lot
                for lot in self.experiment_lots.lot_index.values():
                    if lot.id in unreachable_lot:
                        values = [math.inf, 100, None]
                        user_list.append([each_user, values, lot.id])
                    else:
                        values = CostCal.reserved_cost(each_user, lot)
                        user_list.append([each_user, values, lot.id])
                is_lower = False
                for item in user_list:
                    cost = item[1][0]
                    if each_user.reserved_cost > cost:
                        is_lower = True
                if is_lower:
                    reserve_list.append(user_list)
                else:
                    if not each_user.parking_lot:
                        self.experiment_users.wait_group[each_user.id] = each_user
                    else:
                        each_user.parking_lot.remaining_lots -= 1
            lots_num = len(self.experiment_lots.lot_index.values())
            slice_num = ceil(len(reserve_list) / 5)
            slice_num_times = 0
            slice_count = 0
            for slice_num_times in range(slice_num - 1):
                slice_count += 1
                group_a_list_temp = reserve_list[slice_num_times * 5:
                                                 (slice_num_times + 1) * 5]
                result_temp = Methods.CPLEX_process(group_a_list_temp, True,
                                                    users_num=5, lots_num=lots_num,
                                                    lot_manager=self.experiment_lots)

                if user_count != 0:
                    print(time_ave / user_count)
                if not result_temp:
                    continue

                for j, item in enumerate(result_temp):
                    if item == []:
                        continue
                    user = item[0]
                    user_lon_lat = user.current_lon_and_lat
                    lot_index = item[1]
                    if lot_index == -1:
                        print("non")
                        continue
                    lot = self.experiment_lots.lot_index[lot_index]
                    lot_lon_lat = lot.lon_and_lat
                    dis = Methods.dis_cal(user_lon_lat.lon,
                                          user_lon_lat.lat,
                                          lot_lon_lat.lon,
                                          lot_lon_lat.lat)
                    # 调用实际时间
                    arriving_time = current_time + datetime.timedelta\
                        (minutes=floor(dis / user.driving_speed))
                    # lot.un_reserved(user)
                    self.experiment_users.reserved(user, lot, current_time,
                                                   arriving_time)
                    self.experiment_lots.reserved(lot)
            reserve_list_temp = reserve_list[slice_count * 5: len(reserve_list)]

            result_temp = Methods.CPLEX_process(reserve_list_temp, True,
                                                users_num=ceil(len(reserve_list_temp)),
                                                lots_num=lots_num,
                                                lot_manager=self.experiment_lots)


            if result_temp:
                for j, item in enumerate(result_temp):
                    if not item:
                        continue
                    user = item[0]
                    user_lon_lat = user.current_lon_and_lat
                    lot_index = item[1]
                    if lot_index == -1:
                        print("non")
                        continue
                    lot = self.experiment_lots.lot_index[lot_index]
                    lot_lon_lat = lot.lon_and_lat
                    dis = Methods.dis_cal(user_lon_lat.lon,
                                          user_lon_lat.lat,
                                          lot_lon_lat.lon,
                                          lot_lon_lat.lat)
                    # 调用实际时间
                    arriving_time = current_time + datetime.timedelta\
                        (minutes=floor(dis / user.driving_speed))
                    # lot.un_reserved(user)
                    self.experiment_users.reserved(user, lot, current_time,
                                                   arriving_time)
                    self.experiment_lots.reserved(lot)

            # ###################
            # ###################
            # ###################
            # ###################
            # ###################
            # 实际分配regular
            # ###################
            # ###################
            # ###################
            # ###################
            # ###################
            for each_user in new_group_b:
                result_lot_list = CostCal.regular_cost(each_user, self.experiment_lots,
                                                       self.experiment_users,
                                                       current_time, app_portion)
                if result_lot_list is None:
                    self.experiment_users.wait_group[each_user.id] = each_user
                    continue
                result_lot = result_lot_list[0]
                lot_lon_lat = result_lot.lon_and_lat
                user_lon_lat = self.experiment_users. \
                    get_current_user_lon_lat(each_user)

                dis = Methods.dis_cal(lot_lon_lat.lon, lot_lon_lat.lat,
                                      user_lon_lat.lon, user_lon_lat.lat)
                arrival_time = current_time + datetime.timedelta(minutes=dis / 0.5)
                self.experiment_lots.regular(result_lot, each_user)
                self.experiment_users.regular(each_user, result_lot, current_time,
                                              arrival_time)
            # ###################
            # ###################
            # ###################
            # ###################
            # ###################
            # 分配NG
            # ###################
            # ###################
            # ###################
            # ###################
            # ###################

                # ###################
                # ###################
                # ###################
                # ###################
                # ###################
                # 分配NG
                # ###################
                # ###################
                # ###################
                # ###################
                # ###################

                for each_user in new_group_c:
                    lot = CostCal.NG(current_time, each_user,
                                     self.experiment_lots.lot_index)
                    if lot is None:
                        self.experiment_users.wait_group[each_user.id] = each_user
                        continue
                    user_lon_lat = each_user.current_lon_and_lat
                    lot_lon_lat = lot.lon_and_lat
                    dis = Methods.dis_cal(user_lon_lat.lon,
                                          user_lon_lat.lat,
                                          lot_lon_lat.lon,
                                          lot_lon_lat.lat)
                    # 调用实际时间
                    arriving_time = current_time + datetime.timedelta \
                        (minutes=floor(dis / each_user.driving_speed))
                    self.experiment_users.NG(each_user, lot, current_time, arriving_time)

        if experiment_type == "Secon":
            # ###################
            # ###################
            # ###################
            # ###################
            # ###################
            # 实际分配regular
            # ###################
            # ###################
            # ###################
            # ###################
            # ###################
            new_group = new_group_a + new_group_b
            random.shuffle(new_group)
            for each_user in new_group:
                result_lot_list = CostCal.regular_cost(each_user, self.experiment_lots,
                                                       self.experiment_users,
                                                       current_time, app_portion)
                result_lot = result_lot_list[0]
                lot_lon_lat = result_lot.lon_and_lat
                user_lon_lat = self.experiment_users. \
                    get_current_user_lon_lat(each_user)

                dis = Methods.dis_cal(lot_lon_lat.lon, lot_lon_lat.lat,
                                      user_lon_lat.lon, user_lon_lat.lat)
                arrival_time = current_time + datetime.timedelta(minutes=dis / 0.5)
                self.experiment_lots.regular(result_lot, each_user)
                self.experiment_users.regular(each_user, result_lot, current_time,
                                              arrival_time)

            # ###################
            # ###################
            # ###################
            # ###################
            # ###################
            # 分配NG
            # ###################
            # ###################
            # ###################
            # ###################
            # ###################

            for each_user in new_group_c:
                lot = CostCal.NG(current_time, each_user,
                                 self.experiment_lots.lot_index)
                user_lon_lat = each_user.current_lon_and_lat
                lot_lon_lat = lot.lon_and_lat
                dis = Methods.dis_cal(user_lon_lat.lon,
                                      user_lon_lat.lat,
                                      lot_lon_lat.lon,
                                      lot_lon_lat.lat)
                # 调用实际时间
                arriving_time = current_time + datetime.timedelta \
                    (minutes=floor(dis / each_user.driving_speed))
                self.experiment_users.NG(each_user, lot, current_time, arriving_time)

        if experiment_type == "TITS":
            # ###################
            # ###################
            # ###################
            # ###################
            # ###################
            # 分配reserved
            # ###################
            # ###################
            # ###################
            # ###################
            # ###################
            new_group = new_group_a + new_group_b
            reserve_list = []
            # 计算到各个Lot的cost
            for each_user in new_group:
                user_list = []
                unreachable_lot = each_user.unreachable_lot
                has_closer = False
                for lot in self.experiment_lots.lot_index.values():
                    if lot.id in unreachable_lot:
                        values = [math.inf, 100, None]
                        user_list.append([each_user, values, lot.id])
                    else:
                        values = CostCal.reserved_cost(each_user, lot)
                        user_list.append([each_user, values, lot.id])

                    lot_lon_lat = lot.lon_and_lat
                    if each_user.parking_lot is not None:
                        former_lot_lat = each_user.parking_lot.lon_and_lat
                        des_lot_lat = each_user.des_lon_and_lat
                        former_dis = Methods.dis_cal(des_lot_lat.lon,
                                                     des_lot_lat.lat,
                                                     former_lot_lat.lon,
                                                     former_lot_lat.lat)
                        current_dis = Methods.dis_cal(des_lot_lat.lon,
                                                      des_lot_lat.lat,
                                                      lot_lon_lat.lon,
                                                      lot_lon_lat.lat)
                        if current_dis < former_dis:
                            has_closer = True
                if has_closer is True or each_user.parking_lot is None:
                    reserve_list.append(user_list)
                else:
                    each_user.parking_lot.remaining_lots -= 1
                    if each_user.group == "A":
                        self.experiment_users.group_a[each_user.id] = each_user
                    elif each_user.group == "B":
                        self.experiment_users.group_b[each_user.id] = each_user
                    else:
                        self.experiment_users.group_c[each_user.id] = each_user
            lots_num = len(self.experiment_lots.lot_index.values())
            slice_num = ceil(len(reserve_list) / 5)
            slice_num_times = 0
            slice_count = 0
            for slice_num_times in range(slice_num - 1):
                slice_count += 1
                group_list_temp = reserve_list[slice_num_times * 5:
                                                 (slice_num_times + 1) * 5]
                result_temp = Methods.CPLEX_process(group_list_temp, True,
                                                    users_num=5, lots_num=lots_num,
                                                    lot_manager=self.experiment_lots)
                if not result_temp:
                    continue

                for j, item in enumerate(result_temp):
                    if item == []:
                        continue
                    user = item[0]
                    user_lon_lat = user.current_lon_and_lat
                    lot_index = item[1]
                    if lot_index == -1:
                        print("non")
                        continue
                    lot = self.experiment_lots.lot_index[lot_index]
                    lot_lon_lat = lot.lon_and_lat
                    dis = Methods.dis_cal(user_lon_lat.lon,
                                          user_lon_lat.lat,
                                          lot_lon_lat.lon,
                                          lot_lon_lat.lat)
                    # 调用实际时间
                    arriving_time = current_time + datetime.timedelta \
                        (minutes=floor(dis / user.driving_speed))
                    # lot.un_reserved(user)
                    self.experiment_users.reserved(user, lot, current_time,
                                                   arriving_time)
                    self.experiment_lots.reserved(lot)

            reserve_list_temp = reserve_list[slice_count * 5: len(reserve_list)]
            result_temp = Methods.CPLEX_process(reserve_list_temp, True,
                                                users_num=len(reserve_list_temp),
                                                lots_num=lots_num,
                                                lot_manager=self.experiment_lots)
            if result_temp:
                for j, item in enumerate(result_temp):
                    if item == []:
                        continue

                    user = item[0]

                    user_lon_lat = user.current_lon_and_lat
                    lot_index = item[1]



                    if lot_index == -1:
                        print("non")
                        continue
                    lot = self.experiment_lots.lot_index[lot_index]
                    lot_lon_lat = lot.lon_and_lat

                    dis = Methods.dis_cal(user_lon_lat.lon,
                                          user_lon_lat.lat,
                                          lot_lon_lat.lon,
                                          lot_lon_lat.lat)
                    # 调用实际时间
                    arriving_time = current_time + datetime.timedelta \
                        (minutes=floor(dis / user.driving_speed))
                    # lot.un_reserved(user)
                    self.experiment_users.reserved(user, lot, current_time,
                                                   arriving_time)
                    self.experiment_lots.reserved(lot)

            # ###################
            # ###################
            # ###################
            # ###################
            # ###################
            # 分配NG
            # ###################
            # ###################
            # ###################
            # ###################
            # ###################
            for each_user in new_group_c:
                lot = CostCal.NG(current_time, each_user,
                                 self.experiment_lots.lot_index)
                user_lon_lat = each_user.current_lon_and_lat
                lot_lon_lat = lot.lon_and_lat
                dis = Methods.dis_cal(user_lon_lat.lon,
                                      user_lon_lat.lat,
                                      lot_lon_lat.lon,
                                      lot_lon_lat.lat)
                # 调用实际时间
                arriving_time = current_time + datetime.timedelta \
                    (minutes=floor(dis / each_user.driving_speed))
                self.experiment_users.NG(each_user, lot, current_time, arriving_time)

        if experiment_type == "NG":
            # ###################
            # ###################
            # ###################
            # ###################
            # ###################
            # 分配NG
            # ###################
            # ###################
            # ###################
            # ###################
            # ###################
            new_group = new_group_a + new_group_b + new_group_c
            random.shuffle(new_group)

            for each_user in new_group:
                lot = CostCal.NG(current_time, each_user,
                                 self.experiment_lots.lot_index)
                user_lon_lat = each_user.current_lon_and_lat
                lot_lon_lat = lot.lon_and_lat
                dis = Methods.dis_cal(user_lon_lat.lon,
                                      user_lon_lat.lat,
                                      lot_lon_lat.lon,
                                      lot_lon_lat.lat)
                # 调用实际时间
                arriving_time = current_time + datetime.timedelta \
                    (minutes=floor(dis / each_user.driving_speed))
                self.experiment_users.NG(each_user, lot, current_time, arriving_time)


if __name__ == '__main__':
    # 实验种类
    start_time = datetime.datetime(2018, 12, 11, 19, 0, 0)
    end_time = datetime.datetime(2018, 12, 11, 20, 0, 0)

    occ_por = 1

    first_start_time = start_time

    eval_data = []
    eval_itera = 10
    stop = 1
    type_list = [0, 2, 3]
    while stop < 1.1:
        stop += 1
        print(occ_por)
        eval_data_item = [occ_por]
        eval_itera += 1

        experiment_type_list = ["D2", "Secon", "TITS", "NG"]
        experiment_type_main = experiment_type_list[3]

        experiment_days = 20
        experiment_time = 10
        experiment_duration_start = first_start_time
        experiment_duration_end = first_start_time + datetime.timedelta(hours=1)
        first_start_time = experiment_duration_end

        path = []
        for day in range(experiment_days):
            for times in range(experiment_time):
                start_time_main = experiment_duration_start + datetime.timedelta(days=day)
                end_time_main = experiment_duration_end + datetime.timedelta(days=day)

                lot_file_main = 'D:\\LearningMaterial\\数据\\停车数据\\有用的数据\\' \
                                'experiment\\filtered_block76.csv'

                user_file_main = 'D:\\LearningMaterial\\数据\\停车数据\\有用的数据\\' \
                                 'experiment\\20day\\user_data_day1_10to7_allday' + str(day) + '.csv'
                user_num_file_main = 'D:\\LearningMaterial\\数据\\停车数据\\有用的数据\\' \
                                     'experiment\\20day\\user_num_day1_10to7_allday' + str(day) + \
                                     '.csv'
                check_in_main = 'D:\\LearningMaterial\\数据\\停车数据\\有用的数据\\' \
                                'experiment\\20day\\76block_number_checkin_allday' + str(day) + '.csv'
                check_out_main = 'D:\\LearningMaterial\\数据\\停车数据\\有用的数据\\' \
                                 'experiment\\20day\\76block_number_checkout_allday' + str(day) + '.csv'
                experiment_launcher = Launcher(lot_file_main, user_file_main,
                                               user_num_file_main, check_in_main,
                                               check_out_main, start_time_main, times, occ_por)
                experiment_launcher.start(start_time_main, end_time_main, check_in_main,
                                          check_out_main, experiment_type_main, times)
        total_experiment_times = experiment_days * experiment_time






