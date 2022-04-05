from math import floor, ceil
import datetime
import math
import random
from Django_APP.recom.cost_cal import CostCal
from Django_APP.recom.prediction_val import PreVal
from Django_APP.recom.lot_management import LotManagement
from Django_APP.recom.user_management import UserManagement
from Django_APP.recom.methods import Methods
from Django_APP.recom.locations import Location


class Initializer:
    
    def __init__(self, lot_file, user_file, user_num_file, check_in, check_out,
                 start_time):
        self.experiment_lots = LotManagement(lot_file, check_in, check_out,
                                             start_time, 0)
        self.experiment_users = UserManagement(user_file, user_num_file, start_time)
    
    def start(self, start_time, check_in_file, check_out_file, new_user, e_val):
        current_time = start_time
        PreVal.pre_val_update(check_in_file, check_out_file, start_time)
        
        for each_lot in self.experiment_lots.lot_index.values():
            each_lot.virtual_recommendation_num = 0
        if new_user is not None:
            new_user_list = new_user
            self.experiment_execute(current_time, new_user_list, 0)
        else:
            
            
            
            for user_item in self.experiment_users.group_a.values():
                if user_item.parking_lot.remaining_lots < user_item.parking_lot.lots_num:
                    user_item.parking_lot.remaining_lots += 1
            wait_and_reserved_group = self.experiment_users.decision_point_recommendation_users()
            user_variation_num = self.experiment_lots.flow_in_out_num(check_in_file, check_out_file, current_time)
            self.experiment_users.total_user_num_variation(user_variation_num)
            # 周期性进行分配
            self.experiment_execute(current_time, wait_and_reserved_group)
        # 当前时刻来的用户进行分配
        
        CostCal.status_update(self.experiment_users, current_time)
    
    def update(self, current_time, check_in_file, check_out_file):
        
        user_variation_num = self.experiment_lots.flow_in_out_num(check_in_file, check_out_file, current_time)
        self.experiment_users.total_user_num_variation(user_variation_num)
        wait_and_reserved_group = self.experiment_users.decision_point_recommendation_users()
        
        for user_item in self.experiment_users.group_a.values():
            if user_item.parking_lot.remaining_lots < user_item.parking_lot.lots_num:
                user_item.parking_lot.remaining_lots += 1
        # 周期性进行分配
        self.experiment_execute(current_time, wait_and_reserved_group)
        CostCal.status_update(self.experiment_users, current_time)
        
    def experiment_execute(self, current_time, new_user_list=None, e_val=0):
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
            user_lon_lat = self.experiment_users. \
                get_current_user_lon_lat(each_user)
    
            dis = Methods.dis_cal(lot_lon_lat.lon, lot_lon_lat.lat,
                                  user_lon_lat.lon, user_lon_lat.lat)
            arrival_time = current_time + datetime.timedelta(minutes=dis / 0.5)
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
            des_lon_lat = each_user.des_lon_and_lat
            dis_list = []
            for lot in self.experiment_lots.lot_index.values():
                dis = Methods.dis_cal(des_lon_lat.lon, des_lon_lat.lat,
                                      lot.lon_and_lat.lon, lot.lon_and_lat.lat)
                dis_list.append(dis)
            dis_sort = sorted(enumerate(dis_list), key=lambda x: x[1])
            close_lot = []
            for i in range(e_val):
                close_lot.append(dis_sort[i][0])
            user_list = []
            unreachable_lot = each_user.unreachable_lot
            for lot in self.experiment_lots.lot_index.values():
                if lot.id in unreachable_lot or lot.id in close_lot:
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
                arriving_time = current_time + datetime.timedelta \
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
            each_user.regular_list = result_lot_list
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
        

if __name__ == '__main__':
    a = 113.94242
    b = 22.523468
    print(a + 0.09)
    print(a - 0.09)
    print(b + 0.09)
    print(b - 0.09)
    exit()
    day = 0
    start_time_main = datetime.datetime(2018, 12, 11 + day, 19, 0, 0)
   
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
    experiment_launcher = Initializer(lot_file_main, user_file_main,
                                   user_num_file_main, check_in_main,
                                   check_out_main, start_time_main)
    APP_user = experiment_launcher.experiment_users.add_new_user()
    de_l_l = experiment_launcher.experiment_lots.lot_index[1].lon_and_lat
    de_l_l.lon += 0.00
    de_l_l.lat += 0.00
    des_l_l = de_l_l
    APP_user.des_lon_and_lat = des_l_l
    APP_user.group = "B"
    cu_l_l = Location(113.96728, 22.5246)
    APP_user.current_lon_and_lat = cu_l_l
    experiment_launcher.start(start_time_main, check_in_main,
                              check_out_main, APP_user,0)
    dis_sort = []
    for lot_item in experiment_launcher.experiment_lots.lot_index.values():
        dis = Methods.dis_cal(APP_user.des_lon_and_lat.lon, APP_user.des_lon_and_lat.lat,
                              lot_item.lon_and_lat.lon, lot_item.lon_and_lat.lat)
        dis_sort.append(dis)
    dis_sort = sorted(enumerate(dis_sort), key=lambda x: x[1])
    dis_out = []
    for item in dis_sort:
        dis_out.append(item[0])
    print(dis_out)
    print(APP_user.parking_lot.lot_name + str(APP_user.parking_lot.id))
    current_time = start_time_main + datetime.timedelta(minutes=5)
    while not APP_user.is_arrived:
        lot_remain  = []
        for lot_item in experiment_launcher.experiment_lots.lot_index.values():
            lot_remain.append(lot_item.remaining_lots)
        print(lot_remain)
        experiment_launcher.update(current_time, check_in_main, check_out_main)
        print(APP_user.parking_lot.lot_name + str(APP_user.parking_lot.id))