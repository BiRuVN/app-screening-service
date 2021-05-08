from django.urls import path
from .views import *
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    # path('', ),
    path('date/', get_date),
    path('room/', get_room),
    path('screening-room/', get_screening_by_room),
    path('screening-date/', get_screening_by_date),
    path('screening/new', csrf_exempt(add_screening)),
    path('screening/del', csrf_exempt(del_screening)),
    path('screening/update', csrf_exempt(update_screening)),
]
