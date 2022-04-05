from Django_APP.recom.locations import Location
class ParkingLots:

    def __init__(self, lot_id, lot_name,  longitude, latitude, lots_num, remaining_lots):
        self.id = int(lot_id)
        self.lot_name = lot_name
        self.lon_and_lat = Location(float(longitude), float(latitude))
        # 停车路段拥有停车位数量
        self.lots_num = int(lots_num)
        # 停车路段剩余停车位数量
        self.remaining_lots = int(remaining_lots)
        # 距离停车路段较近其他停车路段
        self.close_set = []
        self.regular_user_list = []
        self.virtual_recommendation_num = 0
        self.driving_time_to_close_lot = []
        self.walking_time_to_des = []

