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

def get_all(fields, statement):
    all_record = run_sql(statement)
    data = []
    for record in all_record:
        data.append(dict(zip(fields, record)))
    return data

def update_date_range(limit=6):
    fields = ['date']
    statement = "SELECT date FROM screening_app_date WHERE DATE(date) >= DATE(NOW()) ORDER BY date LIMIT {}".format(str(limit))

    data = get_all(fields, statement)

    missing_date = limit - len(data)
    if missing_date > 0:
        for i in range(1, missing_date+1):
            run_sql("INSERT INTO screening_app_date (date, day) VALUES (DATE(NOW())+{}, To_Char(DATE(NOW())+{}, 'Day'))".format(str(missing_date)))

# ================= ROOM ======================
# Get ROOM
def get_room(request):
    if request.method == 'GET':
        data = get_all(['room_id', 'room_name'], "SELECT _id, name FROM screening_app_room")
        return JsonResponse({'data' : data}, status=status.HTTP_200_OK)

# ================== DATE ========================
# Get DATE
def get_date(request):
    if request.method == 'GET':
        update_date_range()

        fields = ['date', 'date_id', 'day']
        statement = "SELECT date, _id, day FROM screening_app_date WHERE DATE(date) >= DATE(NOW()) ORDER BY date LIMIT 6"

        data = get_all(fields, statement)

        return JsonResponse({'data' : data}, status=status.HTTP_200_OK)

# Create DATE
# def add_date(request):
#     if request.method == 'POST':
#         statement = "INSERT INTO screening_app_date (date) VALUES (NOW());"
#         run_sql(statement)
#         return JsonResponse({
#             'message': 'Add date successfully'
#         }, status=status.HTTP_201_CREATED) 

# ================== TIMESLOT ========================
# Get TIMESLOT
# def get_timeslot(request):
#     if request.method == 'GET':
#         fields = ['_id', 'started_at', 'price']
#         data = get_all(fields, "SELECT * FROM screening_app_timeslot")

#         return JsonResponse({'data' : data}, status=status.HTTP_200_OK)

# ================== SCREENING ========================
# Get SCREENING by ROOM
def get_screening_by_room(request):
    if request.method == 'GET':
        # Get room_id
        room_id = request.GET.get('room_id', None)

        if room_id is None:
            return JsonResponse({
                'message': 'Missing room_id to get screening'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get all timeslot
        try:
            timeslot_fields = ['timeslot_id', 'started_at', 'price']
            data_timeslot = get_all(timeslot_fields, "SELECT _id, started_at, price FROM screening_app_timeslot")
        except:
            return JsonResponse({
                'message': 'Fail when get timeslot'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update and get 6 dates ahead
        try:
            update_date_range()
        except:
            return JsonResponse({
                'message': 'Fail when update date range'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            date_fields = ['date', 'date_id', 'day']
            data_date = get_all(date_fields, "SELECT date, _id, day FROM screening_app_date WHERE DATE(date) >= DATE(NOW()) ORDER BY date LIMIT 6")
        except:
            return JsonResponse({
                'message': 'Fail when get date'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get all Screening in room
        try:
            screening_fields = ['screening_id', 'date_id', 'room_id', 'timeslot_id', 'movie_id', 'price']
            statement = "SELECT screening_app_screening._id, date_id_id, room_id_id, timeslot_id_id, movie_id, price \
                        FROM ((screening_app_screening \
                            JOIN screening_app_date ON screening_app_screening.date_id_id = screening_app_date._id) \
                                JOIN screening_app_timeslot ON screening_app_screening.timeslot_id_id = screening_app_timeslot._id) \
                            WHERE room_id_id = 1 \
                                    AND DATE(date) >= DATE(NOW()) AND DATE(date) <= DATE(NOW())+6"
            data_screening = get_all(screening_fields, statement)
        except:
            return JsonResponse({
                'message': 'Fail when get screening'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get movie_id from data_screening
        try:
            movie_ids = []
            for sc in data_screening:
                movie_ids.append(sc['movie_id'])
            movie_ids = list(set(movie_ids))
        except:
            return JsonResponse({
                'message': 'Fail when get movie_ids'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get movie from movie_ids
        try:
            data_movie = []
            for m_id in movie_ids:
                movie = dict(requests.get('https://app-movie-genre-service.herokuapp.com/movie?id={}'.format(str(m_id))).json()['data'][0])
                data_movie.append(dict((k, v) for k, v in movie.items() if k in ['movie_id', 'movie_name', 'duration']))
        except:
            return JsonResponse({
                'message': 'Fail when get movie from movie_ids'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = {'data': dict()}
            data['data']['date'] = data_date
            data['data']['timeslot'] = data_timeslot
            data['data']['movie'] = data_movie
            data['data']['screening'] = data_screening
        except:
            return JsonResponse({
                'message': 'Fail when make data'
            }, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({'data' : data}, status=status.HTTP_200_OK)

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
