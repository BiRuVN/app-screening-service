from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import status
from screening_app.models import *
import rest_framework
import ast
import json
import requests
from django.db import connection
import datetime
import base64

def check_token(token):
    token = token.split(' ')[1]
    payload = token.split('.')[1]
    payload += "=" * ((4 - len(payload) % 4) % 4)
    payload_byte = base64.b64decode(payload)
    x = ''.join(map(chr, list(payload_byte)))
    
    auth = {}
    for role in ['ROLE_EMPLOYEE', 'ROLE_GUEST', 'ROLE_ADMIN']:
        if role in x:
            auth['ROLE'] = role
            break
    for action in ['SCREENING.CREATE', 'SCREENING.READ', 'SCREENING.UPDATE', 'SCREENING.DELETE', 
                    'MOVIE.READ', 'MOVIE.UPDATE', 'MOVIE.CREATE', 
                    'GENRE.CREATE', 'GENRE.READ', 'GENRE.UPDATE']:
        auth[action] = True if action in x else False

    return auth

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
    print(data)

    missing_date = limit - len(data)
    print(missing_date)
    if missing_date > 0:
        for i in range(1, missing_date+1):
            # print()
            Date.objects.create(
                date=(datetime.datetime.today() + datetime.timedelta(days=len(data)+i)).strftime('%Y-%m-%d'),
                day=(datetime.datetime.today() + datetime.timedelta(days=len(data)+i)).strftime('%A')
                )

# ================= ROOM ======================
# Get ROOM
def get_room(request):
    if request.method == 'GET':
        # try:
        #     auth = check_token(request.headers['authorization'])
        # except:
        #     return JsonResponse({
        #         'message': 'Mising auth token'
        #     }, status=status.HTTP_400_BAD_REQUEST)

        # if not (auth['ROLE'] == 'ROLE_EMPLOYEE' or auth['ROLE'] == 'ROLE_ADMIN'):
        #     return JsonResponse({
        #         'message': 'Permission denied'
        #     }, status=status.HTTP_400_BAD_REQUEST)
        
        # if not auth['READ']:
        #     return JsonResponse({
        #         'message': 'READ permission denied'
        #     }, status=status.HTTP_400_BAD_REQUEST)

        data = get_all(['room_id', 'room_name'], "SELECT _id, name FROM screening_app_room")
        return JsonResponse({'data' : data}, status=status.HTTP_200_OK)

# ================== DATE ========================
# Get DATE
def get_date(request):
    if request.method == 'GET':
        # try:
        #     auth = check_token(request.headers['authorization'])
        # except:
        #     return JsonResponse({
        #         'message': 'Mising auth token'
        #     }, status=status.HTTP_400_BAD_REQUEST)

        # if auth['ROLE'] == 'ROLE_EMPLOYEE' or auth['ROLE'] == 'ROLE_ADMIN' or auth['ROLE'] == 'ROLE_GUEST':
        #     return JsonResponse({
        #         'message': 'Permission denied'
        #     }, status=status.HTTP_400_BAD_REQUEST)

        # if not auth['READ']:
        #     return JsonResponse({
        #         'message': 'READ permission denied'
        #     }, status=status.HTTP_400_BAD_REQUEST)
        
        update_date_range()

        fields = ['date', 'date_id', 'day']
        statement = "SELECT date, _id, day FROM screening_app_date WHERE DATE(date) >= DATE(NOW()) ORDER BY date LIMIT 6"

        data = get_all(fields, statement)

        return JsonResponse({'data' : data}, status=status.HTTP_200_OK)

# ================== SCREENING ========================
# Get SCREENING by ID
def get_screening_by_id(request):
    if request.method == 'GET':
        sc_id = request.GET.get('screening_id', None)

        if sc_id is None:
            return JsonResponse({
                'message': 'Missing screening_id to get screening'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            sc = Screening.objects.get(_id=sc_id)
        except:
            return JsonResponse({
                'message': 'No existed screening id'
            }, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({
                'data': {
                    'screening_id': sc._id,
                    'date': sc.date_id.date,
                    'timeslot': sc.timeslot_id.started_at,
                    'room': sc.room_id.name
                }
            }, status=status.HTTP_200_OK)


# Get SCREENING by ROOM
def get_screening_by_room(request):
    if request.method == 'GET':
        try:
            auth = check_token(request.headers['authorization'])
        except:
            return JsonResponse({
                'message': 'Mising auth token'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not (auth['ROLE'] == 'ROLE_EMPLOYEE' or auth['ROLE'] == 'ROLE_ADMIN'):
            return JsonResponse({
                'message': 'Permission denied'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not auth['SCREENING.READ']:
            return JsonResponse({
                'message': 'READ permission denied'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get room_id
        room_id = request.GET.get('room_id', None)

        if room_id is None:
            return JsonResponse({
                'message': 'Missing room_id to get screening'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update and get 7 dates ahead
        try:
            update_date_range(limit=7)
        except:
            return JsonResponse({
                'message': 'Fail when update date range'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get all Screening in room
        try:
            screening_fields = ['screening_id', 'date_id', 'room_id', 'date', 'timeslot_id', 'started_at', 'movie_id', 'price']
            statement = "SELECT screening_app_screening._id, date_id_id, room_id_id, date, timeslot_id_id, started_at, movie_id, price \
                        FROM ((screening_app_screening \
                            JOIN screening_app_date ON screening_app_screening.date_id_id = screening_app_date._id) \
                                JOIN screening_app_timeslot ON screening_app_screening.timeslot_id_id = screening_app_timeslot._id) \
                            WHERE room_id_id = {} \
                                    AND DATE(date) >= DATE(NOW()) AND DATE(date) <= DATE(NOW())+6".format(str(room_id))
            data_screening = get_all(screening_fields, statement)
        except:
            return JsonResponse({
                'message': 'Fail when get screening'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Megre movie into screening data
        try:
            for i in range(len(data_screening)):
                movie = dict(requests.get('https://app-movie-genre-service.herokuapp.com/movie?id={}'.format(str(data_screening[i]['movie_id']))).json()['data'][0])
                data_screening[i]['movie'] = dict((k, v) for k, v in movie.items() if k in ['movie_id', 'movie_name', 'duration'])
                del(data_screening[i]['movie_id'])
        except:
            return JsonResponse({
                'message': 'Fail when merge movie into screening'
            }, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({'data': data_screening}, status=status.HTTP_200_OK)

# Get SCREENING by DATE
def get_screening_by_date(request):
    if request.method == 'GET':
        # try:
        #     auth = check_token(request.headers['authorization'])
        # except:
        #     return JsonResponse({
        #         'message': 'Mising auth token'
        #     }, status=status.HTTP_400_BAD_REQUEST)

        # if auth['ROLE'] == 'ROLE_EMPLOYEE' or auth['ROLE'] == 'ROLE_ADMIN' or auth['ROLE'] == 'ROLE_GUEST':
        #     return JsonResponse({
        #         'message': 'Permission denied'
        #     }, status=status.HTTP_400_BAD_REQUEST)

        # if not auth['READ']:
        #     return JsonResponse({
        #         'message': 'READ permission denied'
        #     }, status=status.HTTP_400_BAD_REQUEST)

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
        try:
            auth = check_token(request.headers['authorization'])
        except:
            return JsonResponse({
                'message': 'Mising auth token'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not (auth['ROLE'] == 'ROLE_EMPLOYEE' or auth['ROLE'] == 'ROLE_ADMIN'):
            return JsonResponse({
                'message': 'Permission denied'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not auth['SCREENING.CREATE']:
            return JsonResponse({
                'message': 'CREATE permission denied'
            }, status=status.HTTP_400_BAD_REQUEST)

        body = json.loads(request.body)
        
        try:
            movie_id = body['movie_id']
            date = body['date']
            started_at = body['started_at']
            room_id = body['room_id']
        except:
            return JsonResponse({
                'message': "Missing key"
            }, status=status.HTTP_400_BAD_REQUEST)

        if date is None or started_at is None or room_id is None or movie_id is None:
            return JsonResponse({
                'message': 'Key get None'
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
            sc = Screening.objects.create(
                timeslot_id = Timeslot.objects.get(started_at=started_at),
                date_id = Date.objects.get(date=date),
                room_id = Room.objects.get(_id=room_id),
                movie_id = movie_id
            )
        except:
            return JsonResponse({
                'message': 'Duplicate unique fields'
            }, status=status.HTTP_400_BAD_REQUEST)        

        return JsonResponse({
            'data': {
                'screening_id': sc._id,
                'date_id': Date.objects.filter(date=date).values()[0]['_id'],
                'room_id': room_id,
                'date': date,
                'timeslot_id': Timeslot.objects.filter(started_at=started_at).values()[0]['_id'],
                'started_at': started_at,
                'price': Timeslot.objects.filter(started_at=started_at).values()[0]['price'],
                'movie': {
                    'movie_id': movie_id,
                    'movie_name': movie['data'][0]['movie_name'],
                    'duration': movie['data'][0]['duration']
                }
            }
        }, status=status.HTTP_201_CREATED)

# Delete SCREENING
def del_screening(request):
    if request.method == 'POST':
        try:
            auth = check_token(request.headers['authorization'])
        except:
            return JsonResponse({
                'message': 'Mising auth token'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not (auth['ROLE'] == 'ROLE_EMPLOYEE' or auth['ROLE'] == 'ROLE_ADMIN'):
            return JsonResponse({
                'message': 'Permission denied'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not auth['SCREENING.DELETE']:
            return JsonResponse({
                'message': 'DELETE permission denied'
            }, status=status.HTTP_400_BAD_REQUEST)

        body = json.loads(request.body)
        _id = body['id']
        if _id is None:
            return JsonResponse({
                'message': 'Missing screening id, no screening deleted'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        del_status = Screening.objects.filter(_id=_id).delete()

        return JsonResponse({
            'message': 'Screening deleted'
        }, status=status.HTTP_200_OK)

# Update SCREENING
def update_screening(request):
    if request.method == 'POST':
        try:
            auth = check_token(request.headers['authorization'])
        except:
            return JsonResponse({
                'message': 'Mising auth token'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not (auth['ROLE'] == 'ROLE_EMPLOYEE' or auth['ROLE'] == 'ROLE_ADMIN'):
            return JsonResponse({
                'message': 'Permission denied'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not auth['SCREENING.UPDATE']:
            return JsonResponse({
                'message': 'UPDATE permission denied'
            }, status=status.HTTP_400_BAD_REQUEST)

        body = json.loads(request.body)
        _id = body['id']

        if _id is None:
            return JsonResponse({
                'message': 'Missing screening id, no screening selected'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        screening = Screening.objects.get(_id=_id)
        screening.date_id = Date.objects.get(date=body['date'])
        screening.timeslot_id = Timeslot.objects.get(started_at=body['started_at'])
        screening.room_id = Room.objects.get(_id=body['room_id'])
        screening.movie_id = body['movie_id']
        screening.save()

        return JsonResponse({
            'message': 'Update screening successfully'
        }, status=status.HTTP_200_OK)

    return JsonResponse({
            'message': 'POST method expected but receive {}'.format(request.method)
        }, status=status.HTTP_400_BAD_REQUEST)
