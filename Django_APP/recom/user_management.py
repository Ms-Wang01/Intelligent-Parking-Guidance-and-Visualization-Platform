from Django_APP.recom.user import User
import csv
import datetime
from Django_APP.recom.methods import Methods
from Django_APP.recom.locations import Location


class UserManagement:

    def __init__(self, income_file, income_num_file, start_time):
        self.init_user_num = 30
        self.start_time = start_time
        # 还未到达停车位的用户，分成三组保存
        self.group_a = dict()
        self.group_b = dict()
        self.group_c = dict()

        self.a = dict()
        self.b = dict()
        self.c = dict()
        # 非新用户，但是未分配停车位或寻找停车位失败的regular和NG
        self.wait_group = dict()
        # 保存所有用户
        self.all_users_dict = dict()
        # 已到达但是尚未离开的用户
        self.arrived_users_dict = dict()
        # 已经离开停车位的用户
        self.departure_users_dict = dict()
        # 即将加入的新用户
        self.coming_users = []
        # 每个时隙新加入几个用户
        self.user_num_in_each_slot = []
        # 有哪些时隙会来新用户
        self.user_each_slot = []
        # 最终没找到停车位的用户
        self.failure_users = dict()
        self.system_user = 0
        self.total_user = 0
        # 成功停车的用户
        self.parked_users = []
        self.init_user_info(income_file, income_num_file)

    # 获取用户信息
    def init_user_info(self, income_file, income_num_file):
        income_info = csv.reader(open(income_file, 'r', encoding='utf-8'))
        income_num_info = csv.reader(open(income_num_file, 'r', encoding='utf-8'))
        # 读取所有用户信息
        for info in income_info:
            # "id","longitude","latitude","user_type","speed",
            # "max_driving","max_walking",
            # "des_longitude","des_latitude","current_time","occupy_time"
            info_temp = [info[0], float(info[1]), float(info[2]), info[3],
                         float(info[4]), float(info[5]), float(info[6]),
                         float(info[7]), float(info[8]),
                         datetime.datetime.strptime(info[9], '%Y-%m-%d %H:%M:%S'),
                         info[10], float(info[11]), float(info[12])]
            self.coming_users.append(info_temp)
        # 读取每个时隙来的用户数量和时隙
        count = []
        income_num_time_list = next(income_num_info)
        income_num_list = next(income_num_info)
        # 记录每个时隙新加入用户数量
        for num in income_num_list:
            count.append(int(num))
        income_time = []
        # 在哪些时隙有用户加入
        for item in income_num_time_list:
            income_time.append(datetime.datetime.strptime(item, '%Y-%m-%d %H:%M:%S'))
        self.user_num_in_each_slot = [0] * len(count)
        self.user_num_in_each_slot[0] = self.init_user_num
        min_diff = (self.start_time - income_time[0]).seconds / 60
        for i in range(len(income_time)):
            income_time[i] += datetime.timedelta(minutes=min_diff)
        self.user_each_slot = income_time

    def add_new_user_d(self, user_id, lon, lat, current_time, group):

        info = self.coming_users.pop(0)
        user_id = user_id
        lo = lon
        la = lat
        group = group
        driving_speed = info[4]
        walking_speed = 0.1
        des_lo = info[7]
        des_la = info[8]
        current_time = current_time
        occupy_time = info[10]
        lot_longitude = info[11]
        lot_latitude = info[12]
        new_user = User(user_id, lo, la, group, driving_speed, walking_speed,
                        des_lo, des_la, current_time, occupy_time, lot_longitude,
                        lot_latitude)
        self.all_users_dict[user_id] = new_user
        self.system_user += 1
        self.total_user += 1
        if new_user.group == "A":
            self.a[new_user.id] = new_user
        elif new_user.group == "B":
            self.b[new_user.id] = new_user
        else:
            self.c[new_user.id] = new_user

        return new_user

    def add_new_user(self):

        info = self.coming_users.pop(0)
        user_id = int(info[0])
        lo = info[1]
        la = info[2]
        group = "A"
        driving_speed = info[4]
        walking_speed = 0.1
        des_lo = info[7]
        des_la = info[8]
        current_time = info[9]
        occupy_time = info[10]
        lot_longitude = info[11]
        lot_latitude = info[12]
        new_user = User(user_id, lo, la, group, driving_speed, walking_speed,
                        des_lo, des_la, current_time, occupy_time, lot_longitude,
                        lot_latitude)
        self.all_users_dict[user_id] = new_user
        self.system_user += 1
        self.total_user += 1
        if new_user.group == "A":
            self.a[new_user.id] = new_user
        elif new_user.group == "B":
            self.b[new_user.id] = new_user
        else:
            self.c[new_user.id] = new_user

        return new_user

    def delete_user(self, user_item):
        
        self.system_user -= 1
        self.total_user -= 1
        
        del self.all_users_dict[user_item.id]
        if user_item.group == "A":
            del self.a[user_item.id]
        elif user_item.group == "B":
            del self.b[user_item.id]

    def total_user_num_variation(self, variation_num):
        self.total_user += variation_num

    def get_user_num_in_each_slot(self, current_time):
        if not self.user_each_slot:
            return None
        if current_time < self.user_each_slot[0]:
            return 0
        while current_time != self.user_each_slot[0]:
            self.user_each_slot.pop(0)
            user_num = self.user_num_in_each_slot.pop(0)
            for i in range(user_num):
                self.coming_users.pop(0)
        self.user_each_slot.pop(0)
        return self.user_num_in_each_slot.pop(0)

    def decision_point_recommendation_users(self):
        if self.wait_group:
            user_dict = {**self.wait_group, **self.group_a}
        else:
            user_dict = self.group_a.copy()
        self.wait_group.clear()
        user_list = []
        for item in user_dict.values():
            user_list.append(item)
        return user_list

    def decision_point_recommendation_users_T(self):
        if self.wait_group:
            user_dict = {**self.wait_group, **self.group_a, **self.group_b}
        else:
            user_dict = {**self.group_a, **self.group_b}
        self.wait_group.clear()
        user_list = []
        for item in user_dict.values():
            user_list.append(item)
        return user_list

    def system_user_portion(self):
        if self.total_user == 0:
            return 0
        return self.system_user / self.total_user

    @staticmethod
    def get_current_user_lon_lat(user):
        return user.current_lon_and_lat

    @staticmethod
    def get_des_lon_lat(user):
        return user.des_lon_and_lat

    def regular(self, user, lot, current_time, arrival_time):
        user.is_arrived = False
        user.parking_lot = lot
        user.current_time = current_time
        user.arrival_time = arrival_time
        if user.group == "A":
            self.group_a[user.id] = user
        elif user.group == "B":
            self.group_b[user.id] = user
        else:
            self.group_c[user.id] = user

    def reserved(self, user, lot, current_time, arriving_time):
        user.is_arrived = False
        user.parking_lot = lot
        user.current_time = current_time
        user.arrival_time = arriving_time
        user.searched_parking_list_id.append(lot.id)
        if user.group == "A":
            self.group_a[user.id] = user
        elif user.group == "B":
            self.group_b[user.id] = user
        else:
            self.group_c[user.id] = user

    def NG(self, user, lot, current_time, arriving_time):
        if user.group == "A":
            self.group_a[user.id] = user
        elif user.group == "B":
            self.group_b[user.id] = user
        else:
            self.group_c[user.id] = user
        user.parking_lot = lot
        user.current_time = current_time
        user.arrival_time = arriving_time




