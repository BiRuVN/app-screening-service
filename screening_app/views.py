from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import status
from screening_app.models import *
from django.core import serializers
import rest_framework
import ast
import json
import requests
from django.db import connection

def serialize(querysetObject, fields=()):
    return ast.literal_eval(serializers.serialize('json', querysetObject, fields=fields))

def run_sql(statement):
    with connection.cursor() as cursor:
        cursor.execute(statement)
        if statement.startswith('SELECT'):
            row = cursor.fetchall()
            return row
        cursor.commit()

# ================= ROOM ======================
# Get ROOM
# def get_room(request):
#     if request.method == 'GET':
#         _id = request.GET.get('id', None)
#         rating = request.GET.get('rating', None)
#         print(_id, '---', rating)

#         if _id is None and rating is None:
#             all_movie = serialize(Movie.objects.all(), fields=('name', 'duration', 'rating'))
#             return JsonResponse({'data' : [x['fields'] for x in all_movie]})

#         if _id is not None:
#             movie = serialize(Movie.objects.filter(_id=_id), fields=('name', 'duration', 'rating'))
#         elif rating is not None:
#             movie = serialize(Movie.objects.filter(rating=rating), fields=('name', 'duration', 'rating'))
#         return JsonResponse({'data' : movie})
        
# ================== DATE ========================
# Get DATE
def get_date(request):
    if request.method == 'GET':
        fields = ['date', 'date_id', 'day']
        statement = "SELECT date, _id, day FROM screening_app_date WHERE DATE(date) >= DATE(NOW()) ORDER BY date LIMIT 7"

        all_date = run_sql(statement)

        missing_date = 7 - len(all_date)
        if missing_date > 0:
            for i in range(1, missing_date+1):
                run_sql("INSERT INTO screening_app_date (date, day) VALUES (DATE(NOW())+{}, To_Char(DATE(NOW())+{}, 'Day'))".format(str(missing_date)))

            all_date = run_sql(statement)

        data = []
        for date in all_date:
            data.append(dict(zip(fields, date)))
        return JsonResponse({'data' : data})

# Create DATE
def add_date(request):
    if request.method == 'POST':
        statement = "INSERT INTO screening_app_date (date) VALUES (NOW());"
        run_sql(statement)
        return JsonResponse({
            'message': 'Add date successfully'
        }, status=status.HTTP_201_CREATED) 

# ================== TIMESLOT ========================
# Get TIMESLOT
# def get_timeslot(request):
#     if request.method == 'GET':
#         _id = request.GET.get('id', None)
#         rating = request.GET.get('rating', None)
#         print(_id, '---', rating)

#         if _id is None and rating is None:
#             all_movie = serialize(Movie.objects.all(), fields=('name', 'duration', 'rating'))
#             return JsonResponse({'data' : [x['fields'] for x in all_movie]})

#         if _id is not None:
#             movie = serialize(Movie.objects.filter(_id=_id), fields=('name', 'duration', 'rating'))
#         elif rating is not None:
#             movie = serialize(Movie.objects.filter(rating=rating), fields=('name', 'duration', 'rating'))
#         return JsonResponse({'data' : movie})

# ================== SCREENING ========================
# Get SCREENING by DATE
def get_screening_by_date(request):
    if request.method == 'GET':
        date_id = request.GET.get('date_id', None)
        if date_id is None:
            return JsonResponse({
                'message': 'Missing date_id to get screening'
            }, status=status.HTTP_400_BAD_REQUEST)

        # GET MOVIE_IDs IN DATE
        statement = "SELECT movie_id \
                FROM screening_app_screening \
                    WHERE date_id_id={}\
            ".format(date_id)

        all_screening = run_sql(statement)
        movie_ids = list(set([s[0] for s in all_screening]))

        # GET SCREENING OF MOVIE ABOVE
        data = {
            "movie": [],
            "screening": []
        }
        screening_fields = ['screening_id', 'date_id', 'started_at', 'price', 'timeslot_id', 'movie_id']
        for movie_id in movie_ids:
            # GET MOVIE FROM MOVIE_ID
            movie = requests.get('https://app-movie-genre-service.herokuapp.com/movie?id={}'.format(movie_id)).json()
            data['movie'].append(movie)

            # GET SCREENING FROM MOVIE_ID
            statement = "SELECT screening_app_screening._id, date_id_id, screening_app_timeslot.started_at, screening_app_timeslot.price, timeslot_id_id, movie_id \
                FROM (screening_app_screening \
		                JOIN screening_app_timeslot ON screening_app_screening.timeslot_id_id = screening_app_timeslot._id) \
                    WHERE date_id_id={} AND movie_id={} \
            ".format(date_id, movie_id)

            all_screening = run_sql(statement)
            data_screening = []
            for screening in all_screening:
                data_screening.append(dict(zip(screening_fields, screening)))
            data['screening'].append(data_screening)

        return JsonResponse(data, status=status.HTTP_200_OK)

# Create SCREENING
def add_screening(request):
    if request.method == 'POST':
        
        body = json.loads(request.body)
        
        try:
            movie_id = body['movie_id']
            date_id = body['date_id']
            timeslot_id = body['timeslot_id']
            room_id = body['room_id']
        except:
            return JsonResponse({
                'message': "Missing key"
            }, status=status.HTTP_400_BAD_REQUEST)

        if date_id is None or timeslot_id is None or room_id is None or movie_id is None:
            return JsonResponse({
                'message': 'Missing key to create'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            movie = requests.get('https://app-movie-genre-service.herokuapp.com/movie?id={}'.format(movie_id)).json()
        except:
            return JsonResponse({
                'message': "get movie error"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(movie['data']) == 0:
            return JsonResponse({
                'message': "No movie available in database"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            Screening.objects.create(
                timeslot_id = Timeslot.objects.get(_id=timeslot_id),
                date_id = Date.objects.get(_id=date_id),
                room_id = Room.objects.get(_id=room_id),
                movie_id = movie_id
            )
        except:
            return JsonResponse({
                'message': 'Duplicate unique fields'
            }, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({
            'message': 'Add screening successfully'
        }, status=status.HTTP_201_CREATED)

# Delete SCREENING
def del_screening(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        _id = body['id']
        if _id is None:
            return JsonResponse({
                'message': 'Missing screening id, no screening deleted'
            }, status=status.HTTP_200_OK)
        
        del_status = Screening.objects.filter(_id=_id).delete()

        return JsonResponse({
            'message': '{} movie deleted'.format(del_status[0])
        }, status=status.HTTP_200_OK)

# Update SCREENING
def update_screening(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        _id = body['id']
        print(_id)
        if _id is None:
            return JsonResponse({
                'message': 'Missing screening id, no screening selected'
            }, status=status.HTTP_200_OK)
        
        screening = Screening.objects.get(_id=_id)
        screening.date_id = Date.objects.get(_id=body['date_id'])
        screening.timeslot_id = Timeslot.objects.get(_id=body['timeslot_id'])
        screening.room_id = Room.objects.get(_id=body['room_id'])
        screening.movie_id = body['movie_id']
        screening.save()

        return JsonResponse({
            'message': 'Update screening successfully'
        }, status=status.HTTP_200_OK)

    return JsonResponse({
            'message': 'POST method expected but receive {}'.format(request.method)
        }, status=status.HTTP_200_OK)
