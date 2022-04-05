import datetime
import math
from Django_APP.recom.locations import Location

class User:

    def __init__(self, user_id, longitude, latitude, group, driving_speed, walking_speed,
                 des_lon, des_lat, current_time, lasting_time, lot_lon, lot_lat):
        
        self.id = int(user_id)
        self.current_lon_and_lat = Location(float(longitude), float(latitude))
        self.group = group

        self.init_lon_and_lat = None
        self.lot_lon_and_lat = Location(float(lot_lon), float(lot_lat))
        self.des_lon_and_lat = Location(float(des_lon), float(des_lat))
        self.virtual_lon_and_lat = None

        self.driving_speed = float(driving_speed)
        self.walking_speed = float(walking_speed)

        self.current_time = current_time
        self.arrival_time = current_time + datetime.timedelta(hours=24)
        self.lasting_time = int(lasting_time)

        self.is_arrived = False
        # 寻找停车位的次数
        self.wandering_num = 0
        # 寻找停车位最大限制次数
        self.m = 3
        # 后续要遍历的停车位
        self.parking_lot = None
        self.departure_time = None
        self.unreachable_lot = []
        # 遍历过的停车位id
        self.searched_parking_list_id = []
        self.extra_driving_time = 0

        self.reserved_cost = math.inf
        self.regular_list = []
        self.reserve_list = []

