from Django_APP.recom.user_management import UserManagement
from Django_APP.recom.lot_management import LotManagement
from Django_APP.recom.prediction_val import PreVal
from Django_APP.recom.locations import Location
from math import ceil, e, floor
import math
from Django_APP.recom.methods import Methods
import datetime
import random

eta_val = 0.7
lambda_value = 0.8
NG_threshold = 1


class CostCal:
    @staticmethod
    def reserved_cost(user, lot):
        if lot.remaining_lots == 0:
            return [math.inf, 100, None]
        user_lon_lat = UserManagement.get_current_user_lon_lat(user)
        des_lon_lat = UserManagement.get_des_lon_lat(user)
        lot_lon_lat = lot.lon_and_lat
        user_lon = user_lon_lat.lon
        user_lat = user_lon_lat.lat
        des_lon = des_lon_lat.lon
        des_lat = des_lon_lat.lat
        lot_lon = lot_lon_lat.lon
        lot_lat = lot_lon_lat.lat
        # 距离目的地的驾驶时间
        driving_dis = Methods.dis_cal(user_lon, user_lat, des_lon, des_lat)
        driving_minutes = driving_dis / user.driving_speed
        walking_dis = Methods.dis_cal(lot_lon, lot_lat, des_lon, des_lat)
        walking_minutes = walking_dis / user.walking_speed

        virtual_recom_num = lot.virtual_recommendation_num

        slot_num = ceil(driving_minutes / PreVal.TIME_SLOT)
        if slot_num > 11:
            slot_num = 11
        lot_pre = PreVal.LOT_OCCUPY_RATIO[lot.id]
        pre_val = []

        occupy_num = lot.lots_num - lot.remaining_lots

        for coming, leaving in zip(lot_pre[0], lot_pre[1]):
            pre_val_item = (virtual_recom_num + occupy_num +
                            int(coming - leaving)) / lot.lots_num
            if pre_val_item > 1:
                pre_val_item = pre_val_item
            pre_val.append(pre_val_item)
            occupy_num += int(coming - leaving)

        delta_new = 0

        if slot_num <= 1:
            slot_num = 1
            delta_new = 0
        else:
            for i in range(slot_num):
                delta_value = (e ** float(pre_val[i]) - 1)
                delta_new += delta_value
            # delta_new = 0

        # #############################
        # c = c / 30
        # #############################
        c = walking_minutes
        c = c / 10
        # #############################
        # #############################
        # #############################
        # #############################
        # 不应该是30
        # #############################
        # #############################
        # #############################
        # #############################
        """
        if c > 2:
            return [math.inf, 100, None]
        """
        delta_max = (e - 1) * slot_num

        # return [c, delta_new / delta_max, lot]

        #return [c, 0, lot]

        c = eta_val * c
        delta = (1 - eta_val) * (delta_new / delta_max)
        return [c, delta, lot]


    @staticmethod
    def regular_cost(user, lot_manager, user_manager, current_time, app_portion):
        # cost value 和推荐停车路段
        user.virtual_lon_and_lat = user.current_lon_and_lat
        candidate_result_set = []
        slot_num = 0
        searched_num = user.wandering_num
        for lot in lot_manager.lot_index.values():
            # 返回数值和lot序号 [[value, lot_index],...]
            lot_lon_lat = LotManagement.lot_lon_lat(lot)
            user_lon_lat = UserManagement.get_current_user_lon_lat(user)
            driving_dis = Methods.dis_cal(user_lon_lat.lon, user_lon_lat.lat,
                                          lot_lon_lat.lon, lot_lon_lat.lat)
            driving_time = ceil((driving_dis / user.driving_speed))

            current_time = current_time + datetime. \
                timedelta(minutes=int(driving_time))

            slot_num += ceil(driving_time / 5)

            # 无法完成m次推荐，则剪掉
            if slot_num > 11:
                slot_num = 11
                # return [None, 9999]
            # 计算到达下一目的地时的占用率
            lot_pre = PreVal.LOT_OCCUPY_RATIO[lot.id]
            coming = 0
            leaving = 0
            pre_set = []
            occupy_num = lot.lots_num - lot.remaining_lots
            early_user_num = 0
            # 比该用户先到达的用户数量
            for regular_user in LotManagement.get_regular_users(lot):
                other_user = user_manager.all_users_dict[regular_user.id]
                if other_user.arrival_time < current_time:
                    early_user_num += 1
            # 更正占用率
            app_portion = 1
            for i in range(12):
                coming += int(lot_pre[0][i])
                leaving += int(lot_pre[1][i])
                if user.group == "A":
                    pre_val = (occupy_num + coming - leaving) / lot.lots_num
                else:
                    if early_user_num > coming:
                        pre_val = (occupy_num + coming - leaving +
                                  (early_user_num - coming) * app_portion) \
                                  / lot.lots_num
                    else:
                        pre_val = (occupy_num + coming - leaving) / lot.lots_num

                if pre_val < 0:
                    pre_val = 0
                pre_set.append(pre_val)
            # 当前时刻占用率
            current_pre = pre_set[slot_num]
            if current_pre < 0.8:
                current_pre = 0.8
            init_cost = 0
            if user.wandering_num == 0:
                driving_time = 0
            exist_list = [lot.id]
            result = CostCal.recursion_step(user, lot, current_pre, searched_num,
                                            slot_num, current_time, app_portion,
                                            lot_manager, user_manager, driving_time, exist_list)
            result[1] += init_cost
            candidate_result_set.append(result)

        min_result = 9998
        min_lot = None
        for result in candidate_result_set:
            if min_result > result[1]:
                min_result = result[1]
                min_lot = result[0]
        return min_lot

    @staticmethod
    def recursion_step(user, lot, pre_occupy, searched_num, slot_num,
                       current_time, app_portion, lot_manager, user_manager,
                       driving_time, exist_list):
        searched_num += 1
        des_lon_lat = UserManagement.get_des_lon_lat(user)
        lot_lon_lat = LotManagement.lot_lon_lat(lot)
        walking_dis = Methods.dis_cal(des_lon_lat.lon, des_lon_lat.lat,
                                      lot_lon_lat.lon, lot_lon_lat.lat)
        walking_time = ceil((walking_dis / user.walking_speed))
        # 如果不能到达，则剪掉
        if lot.id in user.unreachable_lot:
            return [None, 9999]
        # 计算到达下一目的地时间

        current_time = current_time + datetime. \
            timedelta(minutes=int(driving_time))
        slot_num += ceil(driving_time / 5)
        # 无法完成m次推荐，则剪掉
        if slot_num > 11:
            slot_num = 11
            # return [None, 9999]
        # 计算到达下一目的地时的占用率
        lot_pre = PreVal.LOT_OCCUPY_RATIO[lot.id]
        coming = 0
        leaving = 0
        pre_set = []
        occupy_num = lot.lots_num - lot.remaining_lots
        early_user_num = 0
        # 比该用户先到达的用户数量
        for regular_user in LotManagement.get_regular_users(lot):
            other_user = user_manager.all_users_dict[regular_user.id]
            if other_user.arrival_time < current_time:
                early_user_num += 1
        # 更正占用率
        for i in range(12):
            current_coming = int(lot_pre[0][i])
            coming += int(lot_pre[0][i])
            leaving += int(lot_pre[1][i])
            
            if early_user_num > current_coming and user.group == "B":
                pre_val = (occupy_num + coming - leaving +
                           (early_user_num - current_coming) * app_portion)\
                          / lot.lots_num
            else:
                pre_val = (occupy_num + coming - leaving) / lot.lots_num
            if pre_val < 0:
                pre_val = 0
            pre_set.append(pre_val)
        # 当前时刻占用率
        current_pre = pre_set[slot_num]
        if current_pre < 0.8:
            current_pre = 0.8
        # driving walking cost

        driving_cost_pre = driving_time * pre_occupy * (1 - current_pre)
        walking_cost_pre = walking_time * pre_occupy * (1 - current_pre)
        if pre_occupy != 0:
            pre_occupy *= current_pre
        else:
            pre_occupy = current_pre

        # 当前层的消耗
        current_layer_cost_pre = lambda_value * driving_cost_pre + \
                                 (1 - lambda_value) * walking_cost_pre
        driving_cost_current = driving_time * pre_occupy
        walking_cost_current = walking_time * pre_occupy
        current_layer_cost_current = lambda_value * driving_cost_current +\
                                     (1 - lambda_value) * walking_cost_current

        if searched_num < user.m:
        #if False:
            next_lot_set = lot.close_set
            # next_lot_set.append(lot.id)
            lot_cost = 9999
            recom_lot = []
            # 开始递归
            for next_lot_index in next_lot_set:
                if next_lot_index in exist_list:
                    continue
                next_lot = lot_manager.lot_index[next_lot_index]
                lot_lon_lat = LotManagement.lot_lon_lat(next_lot)
                user_lon_lat = lot.lon_and_lat
                driving_dis = Methods.dis_cal(user_lon_lat.lon, user_lon_lat.lat,
                                              lot_lon_lat.lon, lot_lon_lat.lat)
                next_driving_time = ceil((driving_dis / user.driving_speed))
                #############
                #############
                #############
                # next_driving_time = lot_manger.lot_dis_index[lot.id][next_lot_index]
                exist_list.append(next_lot.id)
                current_lot_cost = CostCal.recursion_step(user, next_lot,
                                                          pre_occupy, searched_num,
                                                          slot_num, current_time,
                                                          app_portion, lot_manager,
                                                          user_manager,
                                                          next_driving_time, exist_list)
                
                if current_lot_cost[1] < lot_cost:
                    
                    lot_cost = current_lot_cost[1]
                    current_lot_cost[0].append(lot)
                    recom_lot = current_lot_cost[0]
            return [recom_lot, lot_cost + current_layer_cost_current + current_layer_cost_pre]
        else:
            return [[lot], current_layer_cost_current]

    @staticmethod
    def NG(current_time, new_user, lot_index_list):
        closest_lot_list = []
        for lot in lot_index_list.values():
            lot_id = lot.id
            lot_lon_lat = lot.lon_and_lat
            user_lon_lat = new_user.des_lon_and_lat

            closest_lot_list.append(Methods.dis_cal(lot_lon_lat.lon, lot_lon_lat.lat,
                                                    user_lon_lat.lon, user_lon_lat.lat)
                                    / new_user.walking_speed)
        closest_lot_list = sorted(enumerate(closest_lot_list), key=lambda x: x[1])
        lot_index = -1
        for item in closest_lot_list:
            if item[0] not in new_user.unreachable_lot:
                lot_index = item[0]
                break
        if lot_index == -1:
            print("No vacant parking spot")
            return
        lot = lot_index_list[lot_index]
        lot_lon_lat = lot.lon_and_lat
        user_current_lon_lat = new_user.current_lon_and_lat
        dis = Methods.dis_cal(user_current_lon_lat.lon, user_current_lon_lat.lat,
                              lot_lon_lat.lon, lot_lon_lat.lat)
        arrive_time = dis / new_user.driving_speed
        arrive_time = current_time + datetime.timedelta(minutes=floor(arrive_time))
        return lot
    # 不同试验方法，应该不同
    @staticmethod
    def status_update(user_manager, current_time):
        experiment_type = "D2"
        departure_user_list = []
        # 将已到达用户该离开的加入List
        for each_user in user_manager.arrived_users_dict.values():

            if current_time == each_user.departure_time:
                departure_user_list.append(each_user)
        for each_user in departure_user_list:
            user_id = each_user.id
            user_manager.arrived_users_dict.pop(user_id)
            user_manager.departure_users_dict[user_id] = each_user
            user_manager.total_user_num_variation(-1)
            lot = each_user.parking_lot
            if lot.remaining_lots != lot.lots_num:
                lot.remaining_lots += 1
        if experiment_type == "D2":
            # reserved用户是否到达
            arrived_user = []
            experiment_group = user_manager.group_a.copy()
            experiment_list = []
            for user in experiment_group.values():
                experiment_list.append(user)
            random.shuffle(experiment_list)
            for each_user in experiment_list:
                is_arrived = CostCal.location_update(each_user, current_time)
                if is_arrived:
                    each_user.is_arrived = True
                    arrived_user.append(each_user)
                    user_manager.parked_users.append(each_user)
            for each_user in arrived_user:
                user_manager.arrived_users_dict[each_user.id] = each_user
                if each_user.id in user_manager.group_a:
                    del user_manager.group_a[each_user.id]
                elif each_user.id in user_manager.group_b:
                    del user_manager.group_b[each_user.id]
                each_user.departure_time = current_time + datetime. \
                    timedelta(minutes=each_user.lasting_time)

            arrived_b_c = []
            full_b_c = []
            # regular用户是否到达
            for each_user in user_manager.group_b.values():
                is_arrived = CostCal.location_update(each_user, current_time)
                
                if is_arrived:
                    if each_user.id == 65535:
                        print(1)
                    if each_user in each_user.parking_lot.regular_user_list:
                        each_user.parking_lot.regular_user_list.remove(each_user)
                    # 到达后是否有空余停车位
                    lot = each_user.parking_lot
                    if lot.remaining_lots <= 0:
                        full_b_c.append(each_user)
                    else:
                        each_user.is_arrived = True
                        arrived_b_c.append(each_user)
                        lot.remaining_lots -= 1
            # NG用户是否到达
            for each_user in user_manager.group_c.values():
                is_arrived = CostCal.location_update(each_user, current_time)
                if is_arrived:
                    # 到达后是否有空余停车位

                    lot = each_user.parking_lot
                    portion = lot.remaining_lots / lot.lots_num
                    portion = 1 - portion
                    if portion >= NG_threshold:
                        # if True:
                        full_b_c.append(each_user)
                    else:
                        each_user.is_arrived = True
                        arrived_b_c.append(each_user)
                        lot.remaining_lots -= 1
            # 解决到达却没发现停车位的用户
            for each_user in full_b_c:
                if len(each_user.unreachable_lot) > 7:
                    each_user.unreachable_lot.pop(0)
                each_user.unreachable_lot.append(each_user.parking_lot.id)

                # 如果达到最大搜索次数
                each_user.wandering_num += 1
                each_user.searched_parking_list_id.append(each_user.parking_lot.id)

                user_manager.wait_group[each_user.id] = each_user
                if each_user.id in user_manager.group_a:
                    del user_manager.group_a[each_user.id]
                elif each_user.id in user_manager.group_b:
                    each_user.parking_lot.regular_user_list.append(each_user)
                    del user_manager.group_b[each_user.id]
                else:
                    del user_manager.group_c[each_user.id]
                # 有空余停车位的用户
            for each_user in arrived_b_c:
                user_manager.arrived_users_dict[each_user.id] = each_user
                user_manager.parked_users.append(each_user)
                if each_user.id in user_manager.group_a:
                    del user_manager.group_a[each_user.id]
                elif each_user.id in user_manager.group_b:
                    del user_manager.group_b[each_user.id]
                else:
                    del user_manager.group_c[each_user.id]
                lot = each_user.parking_lot

                each_user.searched_parking_list_id.append(lot.id)
                each_user.departure_time = current_time + datetime. \
                    timedelta(minutes=each_user.lasting_time)

        elif experiment_type == "Secon":
            experiment_group = {**user_manager.group_a, **user_manager.group_b}
            experiment_list = []
            for user in experiment_group.values():
                experiment_list.append(user)
            random.shuffle(experiment_list)

            full_exp = []
            arrived_exp = []
            for each_user in experiment_list:
                is_arrived = CostCal.location_update(each_user, current_time)
                if is_arrived:
                    if each_user in each_user.parking_lot.regular_user_list:
                        each_user.parking_lot.regular_user_list.remove(each_user)
                    # 到达后是否有空余停车位
                    lot = each_user.parking_lot
                    if lot.remaining_lots <= 0:
                        full_exp.append(each_user)
                    else:
                        each_user.is_arrived = True
                        arrived_exp.append(each_user)
                        lot.remaining_lots -= 1
            # NG用户是否到达
            for each_user in user_manager.group_c.values():
                is_arrived = CostCal.location_update(each_user, current_time)
                if is_arrived:
                    # 到达后是否有空余停车位
                    lot = each_user.parking_lot
                    portion = lot.remaining_lots / lot.lots_num
                    portion = 1 - portion
                    if portion >= NG_threshold:
                        # if True:
                        full_exp.append(each_user)
                    else:
                        each_user.is_arrived = True
                        arrived_exp.append(each_user)
                        lot.remaining_lots -= 1
            # 解决到达却没发现停车位的用户
            for each_user in full_exp:
                if len(each_user.unreachable_lot) > 7:
                    each_user.unreachable_lot.pop(0)
                each_user.unreachable_lot.append(each_user.parking_lot.id)

                # 如果达到最大搜索次数
                each_user.wandering_num += 1
                # if each_user.wandering_num == each_user.m and each_user.group != "C":
                if each_user.wandering_num > 5 and each_user not in user_manager.group_c:
                    user_manager.failure_users[each_user.id] = each_user
                else:

                    each_user.searched_parking_list_id.append(each_user.parking_lot.id)

                    user_manager.wait_group[each_user.id] = each_user
                if each_user.id in user_manager.group_a:
                    del user_manager.group_a[each_user.id]
                elif each_user.id in user_manager.group_b:
                    del user_manager.group_b[each_user.id]
                else:
                    del user_manager.group_c[each_user.id]
            # 有空余停车位的用户
            for each_user in arrived_exp:
                user_manager.arrived_users_dict[each_user.id] = each_user
                user_manager.parked_users.append(each_user)
                if each_user.id in user_manager.group_a:
                    each_user.parking_lot.regular_user_list.append(each_user)
                    del user_manager.group_a[each_user.id]
                elif each_user.id in user_manager.group_b:
                    each_user.parking_lot.regular_user_list.append(each_user)
                    del user_manager.group_b[each_user.id]
                else:
                    del user_manager.group_c[each_user.id]
                lot = each_user.parking_lot
                each_user.searched_parking_list_id.append(lot.id)
                each_user.departure_time = current_time + datetime. \
                    timedelta(minutes=each_user.lasting_time)

        elif experiment_type == "TITS":
            # reserved用户是否到达
            arrived_user = []
            experiment_group = {**user_manager.group_a, **user_manager.group_b}
            experiment_list = []
            for user in experiment_group.values():
                experiment_list.append(user)
            random.shuffle(experiment_list)
            for each_user in experiment_list:

                is_arrived = CostCal.location_update(each_user, current_time)
                if is_arrived:
                    each_user.is_arrived = True
                    arrived_user.append(each_user)
                    user_manager.parked_users.append(each_user)
            for each_user in arrived_user:
                user_manager.arrived_users_dict[each_user.id] = each_user
                if each_user.id in user_manager.group_a:
                    del user_manager.group_a[each_user.id]
                elif each_user.id in user_manager.group_b:
                    del user_manager.group_b[each_user.id]
                each_user.departure_time = current_time + datetime. \
                    timedelta(minutes=each_user.lasting_time)
            # NG用户是否到达

            experiment_group = {**user_manager.group_c}

            arrived_exp = []
            full_ng = []
            for each_user in experiment_group.values():
                is_arrived = CostCal.location_update(each_user, current_time)
                if is_arrived:
                    # 到达后是否有空余停车位

                    lot = each_user.parking_lot
                    portion = lot.remaining_lots / lot.lots_num
                    portion = 1 - portion
                    if portion >= NG_threshold:
                        # if True:
                        full_ng.append(each_user)
                    else:
                        each_user.is_arrived = True
                        arrived_exp.append(each_user)
                        lot.remaining_lots -= 1
                # 解决到达却没发现停车位的用户
            group_a = 0
            group_b = 0
            for each_user in full_ng:
                if len(each_user.unreachable_lot) > 7:
                    each_user.unreachable_lot.pop(0)
                each_user.unreachable_lot.append(each_user.parking_lot.id)
                if each_user.group == "C":

                    for occ_user in user_manager.all_users_dict.values():
                        if occ_user.is_arrived is False and occ_user.parking_lot == each_user.parking_lot:
                            if occ_user.group == "A" and occ_user.is_arrived is False:
                                group_a += 1
                            if occ_user.group == "B" and occ_user.is_arrived is False:
                                group_b += 1
                # 如果达到最大搜索次数
                each_user.wandering_num += 1
                # if each_user.wandering_num == each_user.m and each_user.group != "C":
                each_user.searched_parking_list_id.append(each_user.parking_lot.id)

                user_manager.wait_group[each_user.id] = each_user
                if each_user.id in user_manager.group_a:
                    del user_manager.group_a[each_user.id]
                elif each_user.id in user_manager.group_b:
                    del user_manager.group_b[each_user.id]
                else:
                    del user_manager.group_c[each_user.id]
                # 有空余停车位的用户
            for each_user in arrived_exp:
                user_manager.arrived_users_dict[each_user.id] = each_user
                user_manager.parked_users.append(each_user)
                if each_user.id in user_manager.group_a:
                    del user_manager.group_a[each_user.id]
                elif each_user.id in user_manager.group_b:
                    del user_manager.group_b[each_user.id]
                else:
                    del user_manager.group_c[each_user.id]
                lot = each_user.parking_lot

                each_user.searched_parking_list_id.append(lot.id)
                each_user.departure_time = current_time + datetime. \
                    timedelta(minutes=each_user.lasting_time)

            return [group_a, group_b]

        elif experiment_type == "NG":
            # reserved用户是否到达
            experiment_group = {**user_manager.group_a, **user_manager.group_b,
                                **user_manager.group_c}
            experiment_list = []
            for user in experiment_group.values():
                experiment_list.append(user)
            random.shuffle(experiment_list)

            arrived_exp = []
            full_ng = []
            for each_user in experiment_list:
                is_arrived = CostCal.location_update(each_user, current_time)
                if is_arrived:
                    # 到达后是否有空余停车位

                    lot = each_user.parking_lot
                    portion = lot.remaining_lots / lot.lots_num
                    portion = 1 - portion
                    if portion >= NG_threshold:
                        # if True:
                        full_ng.append(each_user)
                    else:
                        each_user.is_arrived = True
                        arrived_exp.append(each_user)
                        lot.remaining_lots -= 1
                # 解决到达却没发现停车位的用户
            for each_user in full_ng:
                if len(each_user.unreachable_lot) > 7:
                    each_user.unreachable_lot.pop(0)
                each_user.unreachable_lot.append(each_user.parking_lot.id)

                # 如果达到最大搜索次数
                each_user.wandering_num += 1
                each_user.searched_parking_list_id.append(each_user.parking_lot.id)

                user_manager.wait_group[each_user.id] = each_user
                if each_user.id in user_manager.group_a:
                    del user_manager.group_a[each_user.id]
                elif each_user.id in user_manager.group_b:
                    del user_manager.group_b[each_user.id]
                else:
                    del user_manager.group_c[each_user.id]
                # 有空余停车位的用户
            for each_user in arrived_exp:
                user_manager.arrived_users_dict[each_user.id] = each_user
                user_manager.parked_users.append(each_user)
                if each_user.id in user_manager.group_a:
                    del user_manager.group_a[each_user.id]
                elif each_user.id in user_manager.group_b:
                    del user_manager.group_b[each_user.id]
                else:
                    del user_manager.group_c[each_user.id]
                lot = each_user.parking_lot

                each_user.searched_parking_list_id.append(lot.id)
                each_user.departure_time = current_time + datetime. \
                    timedelta(minutes=each_user.lasting_time)





    @staticmethod
    def location_update(target_user, current_time):
        speed = target_user.driving_speed
        lot = target_user.parking_lot
        lot_lon_lat = lot.lon_and_lat
        user_lon_lat = target_user.current_lon_and_lat
        time_diff = 5
        driving_dis = speed * time_diff
        dis_between_loc = Methods.dis_cal(user_lon_lat.lon, user_lon_lat.lat,
                                          lot_lon_lat.lon, lot_lon_lat.lat)
        if driving_dis >= dis_between_loc:
            if target_user.group == "C":
                target_user.current_lon_and_lat = lot_lon_lat
            return True
        portion = driving_dis / dis_between_loc
        lon_diff = lot_lon_lat.lon - user_lon_lat.lon
        lat_diff = lot_lon_lat.lat - user_lon_lat.lat
        updated_lon = user_lon_lat.lon + lon_diff * portion
        updated_lat = user_lon_lat.lat + lat_diff * portion
        dis_between_loc = Methods.dis_cal(updated_lon, updated_lat,
                                          lot_lon_lat.lon, lot_lon_lat.lat)
        target_user.current_lon_and_lat = Location(updated_lon, updated_lat)
        target_user.current_time = current_time
        arriving_time_diff = (dis_between_loc - driving_dis) / speed
        target_user.arrival_time = current_time + datetime.timedelta\
            (minutes=arriving_time_diff)
        return False

