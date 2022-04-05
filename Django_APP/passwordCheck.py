from django.shortcuts import render  # 可以用来返回我们渲染的html文件
from django.http import HttpResponse  # 可以返回渲染的页面
from django.contrib.admin.models import CheckDB  # 导入我们的模型类


def simplePasswordCheck(user_name, user_password):
    # add_user
    try:
        user = CheckDB.objects.get(user_id=user_name)
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
    Check1 = CheckDB(user_id=user_name, user_password=user_password)
    Check1.save()


# 删除数据
def delete_user(user_name):
    CheckDB.objects.filter(user_id=user_name).delete()


# 查询
def search_user(user_name):
    # 查询表中的所有数据
    rs = CheckDB.objects.all()
    print(rs)
    # 根据筛选条件查询出表中的单条数据（注意如果条件查询出多条数据，使用该语句会报错）
    rs1 = CheckDB.objects.get(user_id=user_name)
    print(rs1)


# 更新数据
def update_user(user_name, user_password):
    check = CheckDB.objects.get(user_id=user_name)
    check.user_password = user_password
    check.save()
