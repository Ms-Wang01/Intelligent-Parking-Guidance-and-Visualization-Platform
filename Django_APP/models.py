# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Admin(models.Model):
    adminid = models.IntegerField(db_column='AdminId', primary_key=True)  # Field name made lowercase.
    admin_phone_number = models.CharField(db_column='Admin_phone_number', max_length=45)  # Field name made lowercase.
    adminname = models.CharField(db_column='AdminName', max_length=45, blank=True,
                                 null=True)  # Field name made lowercase.
    admin_password = models.CharField(db_column='Admin_password', max_length=45)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'admin'


class BerthInfo(models.Model):
    berth_id = models.IntegerField(primary_key=True)
    status = models.IntegerField(blank=True, null=True)
    road_segment_info_segment = models.ForeignKey('RoadSegmentInfo', models.DO_NOTHING,
                                                  db_column='Road_segment_info_segment_id')

    # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'berth_info'
        unique_together = (('berth_id', 'road_segment_info_segment'),)


class Parkingdata(models.Model):
    parkingdata_id = models.IntegerField(db_column='ParkingData_id', primary_key=True)  # Field name made lowercase.
    user_lon = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    user_lat = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    service_type = models.CharField(max_length=1, blank=True, null=True)
    speed = models.IntegerField(blank=True, null=True)
    longest_drive_time = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    longest_walk_time = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    dest_lon = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    dest_lat = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    service_init_time = models.DateTimeField(db_column='Service_init_time', blank=True,
                                             null=True)  # Field name made lowercase.
    parking_duration = models.IntegerField(blank=True, null=True)
    user_uid = models.ForeignKey('User', models.DO_NOTHING, db_column='User_Uid')  # Field name made lowercase.
    road_segment = models.ForeignKey('RoadSegmentInfo', models.DO_NOTHING,
                                     db_column='Road_segment_id')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'parkingdata'


class RoadSegmentInfo(models.Model):
    segment_id = models.IntegerField(primary_key=True)
    road_segment_name = models.CharField(max_length=45, blank=True, null=True)
    road_free_space_amount = models.IntegerField(db_column='Road_free_space_amount')  # Field name made lowercase.
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'road_segment_info'


class User(models.Model):
    uid = models.AutoField(db_column='Uid', primary_key=True)  # Field name made lowercase.
    user_name = models.CharField(max_length=45, blank=True, null=True)
    user_password = models.CharField(db_column='User_password', max_length=45)  # Field name made lowercase.
    user_phone_number = models.CharField(db_column='User_phone_number', max_length=45)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'user'
