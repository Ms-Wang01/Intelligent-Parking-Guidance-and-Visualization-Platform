from django.shortcuts import render  # 可以用来返回我们渲染的html文件
from django.http import HttpResponse  # 可以返回渲染的页面
from .models import Admin, BerthInfo, Parkingdata, RoadSegmentInfo, User  # 导入我们的模型类

def simplePasswordCheck(user_name, user_password):
    try:
        user = User.objects.get(user_name=user_name)
        if user:
            if user.user_password == user_password:
                judgement = 1
            else:
                judgement = 0
        else:
            judgement = 0
    except:
        judgement = 0
    return judgement


# 添加数据方法
def add_user(user_name, user_password):
    user = User(user_name=user_name, user_password=user_password)
    user.save()


# 删除数据
def delete_user(user_name):
    User.objects.filter(user_name=user_name).delete()


# 查询
def search_user(user_name):
    # 查询表中的所有数据
    rs = User.objects.all()
    print(rs)
    # 根据筛选条件查询出表中的单条数据（注意如果条件查询出多条数据，使用该语句会报错）
    rs1 = User.objects.get(user_name=user_name)
    print(rs1)


# 更新数据
def update_user(user_name, user_password):
    check = User.objects.get(user_name=user_name)
    check.user_password = user_password
    check.save()
