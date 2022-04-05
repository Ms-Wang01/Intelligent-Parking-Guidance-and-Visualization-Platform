from Django_APP.recom.prediction_val import PreVal
from math import radians, cos, sin, asin, sqrt, ceil, e, floor
from Django_APP.recom.locations import Location
import cplex
from cplex.exceptions import CplexError
import math
import csv
import datetime


class Methods:
    occ_por = 0
    lot_occ_num_lim_list = []

    @staticmethod
    def initial_occopy(in_file, out_file):
        in_info = csv.reader(open(in_file, 'r', encoding='utf-8'))
        next(in_info)
        out_info = csv.reader(open(out_file, 'r', encoding='utf-8'))
        next(out_info)
        lot_in = []
        lot_out = []
        for lot_in_num in in_info:
            lot_in_num = lot_in_num[1:len(lot_in_num)]
            lot_in_temp = 0
            for item in lot_in_num:
                lot_in_temp += int(item)
            lot_in.append(lot_in_temp)

        for lot_out_num in out_info:
            lot_out_num = lot_out_num[1:len(lot_out_num) - 1]
            lot_out_temp = 0
            for item in lot_out_num:
                lot_out_temp += int(item)
            lot_out.append(lot_out_temp)
        result = []

        for in_num, out_num in zip(lot_in, lot_out):
            result.append(in_num - out_num)
        return result

    @staticmethod
    def dis_cal(lng1, lat1, lng2, lat2):
        # 返回距离为km
        lng1, lat1, lng2, lat2 = map(radians, [float(lng1), float(lat1),
                                               float(lng2), float(lat2)])
        # 经纬度转换成弧度
        dlon = lng2 - lng1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2

        distance = 2 * asin(sqrt(a)) * 6371
        # distance = 2 * asin(sqrt(a)) * 6371 * 1000  # 地球平均半径，6371km
        distance = round(distance, 3) / 1.4 * 2
        # 曼哈顿距离
        return distance




    @staticmethod
    def CPLEX_process(u_l_vs_list, is_reserve, users_num, lots_num, lot_manager):

        my_rownames = []
        my_rhs = []
        my_obj = []
        my_ub = []
        my_lb = []
        my_ctype = ""
        my_sense = ""
        # X_ij for any i and j
        my_colnames = []
        # X_ij for any j
        x_row = []
        x_row_weight = []
        x_col = []
        x_col_weight = []
        # row num counter
        x_i = 0

        if len(u_l_vs_list) == 0:
            return []

        wait_num = 0
        rows = []
        x_row_wait = []
        x_row_wait_weight = []
        row_count = 0

        current_user = u_l_vs_list[0][0]
        user_lot_list = []
        # [user, values, lot.id]
        # values = c, delta_new / slot_num, lot

        for i, user_lot_list in enumerate(u_l_vs_list):

            x_row_temp = []
            x_row_weight_temp = []
            x_row_wait_temp = []
            x_row_wait_weight_temp = []
            for j, item in enumerate(user_lot_list):
                user = item[0]
                c = item[1][0]
                delta = item[1][1]
                lot = item[1][2]

                # lot = ParkingInformation.LOTS[lot_id]
                my_ctype += "I"
                x_index = "x_" + str(i) + "_" + str(j)
                my_colnames.append(x_index)

                # my_obj.append(float(lot.item))
                # wait队列中的用户
                if not user.parking_lot:
                    if math.isinf(c):
                        my_obj.append(100)
                    else:
                        # const -20
                        my_obj.append(c + delta - 2)
                    wait_num += 1
                    x_row_wait_temp.append(x_index)
                    x_row_wait_weight_temp.append(1)
                else:
                    if math.isinf(c):
                        my_obj.append(100)
                    else:
                        # const -20
                        my_obj.append(c + delta)

                    x_row_temp.append(x_index)
                    x_row_weight_temp.append(1)

            user_lot_list = []
            if x_row_temp and x_row_weight_temp:
                x_row.append(x_row_temp)
                x_row_weight.append(x_row_weight_temp)
            if x_row_wait_temp and x_row_wait_weight_temp:
                x_row_wait.append(x_row_wait_temp)
                x_row_wait_weight.append(x_row_wait_weight_temp)
        my_colnames.append("x_const")
        my_obj.append(wait_num)
        my_ctype += "I"

        # sum(x_ij(k)) = 1 reserved
        for variables, weights in zip(x_row, x_row_weight):
            constraints_row = [variables, weights]
            my_rownames.append("r_" + str(row_count))
            row_count += 1
            rows.append(constraints_row)
            my_rhs.append(1.0)
            my_sense += 'E'

        # sum(x_ij(k)) <= 1 waiting and new
        for variables, weights in zip(x_row_wait, x_row_wait_weight):
            constraints_row = [variables, weights]
            my_rownames.append("r_" + str(row_count))
            row_count += 1
            rows.append(constraints_row)
            my_rhs.append(1)
            my_sense += "E"

        # 定位每个停车位
        # lot_num_in_region = len(u_l_vs_list[0][0].region.lots)
        for i, user_lot in enumerate(u_l_vs_list):

            for j, item in enumerate(user_lot):
                if i == 0:
                    x_col.append(["x_" + str(int(i)) + "_" + str(j)])
                    x_col_weight.append([1])
                else:
                    x_col[j].append("x_" + str(int(i)) + "_" + str(j))
                    x_col_weight[j].append(1)
        """
        for col in range(len(u_l_vs_list[0][1])):
            # 获取每个停车位的用户信息
            list_each_col = []
            x_each_col = []
            x_each_col_weight = []
            for row in range(len(u_l_vs_list)):
                x_each_col.append("x_" + str(row) + "_" + str(col))
                x_each_col_weight.append(1)
                list_each_col_temp = u_l_vs_list[row][1][col][0]
                list_each_col.append(list_each_col_temp)
            x_col.append(x_each_col)
            x_col_weight.append(x_each_col_weight)
            """

        # sum(x_ij(k)) <= lot_num
        for index in range(len(x_col)):
            variables = x_col[index]
            weights = x_col_weight[index]
            constraints_row = [variables, weights]
            my_rownames.append("r_" + str(row_count))
            row_count += 1
            rows.append(constraints_row)
            # not right enough
            my_rhs.append(int(lot_manager.lot_index[index].remaining_lots))

            my_sense += "L"
        """
        # sum(x_ij(k)) <= occ_lot_num_limit
        for index in range(len(x_col)):
            variables = x_col[index]
            weights = x_col_weight[index]
            constraints_row = [variables, weights]
            my_rownames.append("r_" + str(row_count))
            row_count += 1
            rows.append(constraints_row)
            # not right enough
            my_rhs.append(int(lot_manager.lot_index[index].lots_num *
                              Methods.occ_por))

            my_sense += "L"
        """
        """
        # x_ij(k) * c_ij(k) <= c_ij(k-1)
        for outer_index in range(len(x_row)):
            for index in range(len(x_row[outer_index])):
                variables = [x_row[outer_index][index]]
                weight_value = u_l_vs_list[outer_index][index][1][0]
                if math.isinf(weight_value):
                    weights = [100]
                else:
                    weights = [weight_value]
                constraints_row = [variables, weights]
                my_rownames.append("r_" + str(row_count))
                row_count += 1
                rows.append(constraints_row)
                user = u_l_vs_list[outer_index][index][0]
                if math.isinf(user.reserved_cost):
                    my_rhs.append(9999)
                else:
                    my_rhs.append(user.reserved_cost * 1.1)

                my_sense += "L"
        """

        # upper bound and lower bound
        for index in range(len(my_colnames) - 1):
            if my_obj[index] == 100:
                my_ub.append(0.0)
            else:
                my_ub.append(1.0)
            my_lb.append(0.0)
        my_ub.append(1.0)
        my_lb.append(1.0)


        try:
            my_prob = cplex.Cplex()
            my_prob.set_results_stream(None)
            my_prob.objective.set_sense(my_prob.objective.sense.minimize)
            my_prob.variables.add(obj=my_obj, lb=my_lb, ub=my_ub, types=my_ctype,
                                  names=my_colnames)
            my_prob.linear_constraints.add(lin_expr=rows, senses=my_sense,
                                           rhs=my_rhs, names=my_rownames)
            my_prob.solve()
            x = my_prob.solution.get_values()
            # print('x: ')
            result_row = users_num

            result_col = lots_num
            if len(x) == 0:
                return []
            # print(x)
            # print(my_prob.solution.status[my_prob.solution.get_status()])
            # print("Solution value  = ", my_prob.solution.get_objective_value())
            result_count = 0
            for item in x:
                if item >= 1:
                    result_count += 1
            if is_reserve:
                if result_count < 2:
                    print("No Result")

                    return None
            else:
                if result_count < 1:
                    print("No result")
                    return None

            result = []
            lot_num_record = [0] * 76
            for i in range(result_row):
                result_temp = []
                for j in range(result_col):
                    # print(x[result_col * i + j], end=" ")
                    if is_reserve:
                        if int(x[(result_col) * i + j]) == 1.0:
                            user = u_l_vs_list[i][j][0]
                            lot_id = u_l_vs_list[i][j][2]
                            result_temp = [user, lot_id]
                            user.reserved_cost = u_l_vs_list[i][j][1][0]
                    else:
                        if int(x[(result_col) * i + j]) == 1.0:
                            result_temp = [u_l_vs_list[j][0], u_l_vs_list[j][2]]
                            u_l_vs_list[j][0].c = u_l_vs_list[j][1][0] - \
                                                  u_l_vs_list[j][0].wandering_num / 5
                result.append(result_temp)
            result_count = 0
            ##############################################
            # user_list.clear()
            # print(result)
            # print(result[0][0].id)\\
            result_count = 0
            return result
        except CplexError as exc:
            print("ERROR")
            print(exc)

