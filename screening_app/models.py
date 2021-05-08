from django.db import models

# Create your models here.
class Room(models.Model):
    _id = models.AutoField(primary_key=True, null=False)
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

class Timeslot(models.Model):
    _id = models.AutoField(primary_key=True, null=False)
    started_at = models.TimeField(unique=True, null=False)
    price = models.IntegerField(default=45000)

    def __str__(self):
        return self.started_at

class Date(models.Model):
    _id = models.AutoField(primary_key=True, null=False)
    date = models.DateField(auto_created=True, unique=True, null=False)
    day = models.CharField(max_length=10, null=False)

    def __str__(self):
        return self.date
    
    class Meta:
        unique_together = ('date', 'day')

class Screening(models.Model):
    _id = models.AutoField(primary_key=True, null=False)
    timeslot_id = models.ForeignKey(Timeslot, on_delete=models.CASCADE)
    room_id = models.ForeignKey(Room, on_delete=models.CASCADE)
    date_id = models.ForeignKey(Date, on_delete=models.CASCADE)
    movie_id = models.IntegerField()
    

    class Meta:
        unique_together = ('timeslot_id', 'room_id', 'date_id')