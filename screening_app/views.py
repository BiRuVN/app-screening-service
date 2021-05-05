from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import status
from screening_app.models import *
from django.core import serializers
import rest_framework
import ast
import json

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
# def get_date(request):
#     if request.method == 'GET':
#         if _id is None and rating is None:
#             all_movie = serialize(Movie.objects.all(), fields=('name', 'duration', 'rating'))
#             return JsonResponse({'data' : [x['fields'] for x in all_movie]})

#         if _id is not None:
#             movie = serialize(Movie.objects.filter(_id=_id), fields=('name', 'duration', 'rating'))
#         elif rating is not None:
#             movie = serialize(Movie.objects.filter(rating=rating), fields=('name', 'duration', 'rating'))
#         return JsonResponse({'data' : movie})

# Create DATE
def add_date(request):
    if request.method == 'POST':
        statement = "INSERT INTO public.screening_app_date (date) VALUES (NOW());"
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
def get_screening_by_room(request):
    if request.method == 'GET':
        room_id = request.GET.get('date_id', None)
        if room_id is None:
            return JsonResponse({
                'message': 'Missing room_id to get screening'
            }, status=status.HTTP_400_BAD_REQUEST)

        statement = "\
            \
            "


# Create SCREENING
def add_screening(request):
    if request.method == 'POST':
        body = json.loads(request.body)

        movie_name = body['movie_name']
        date = body['date']
        timeslot = body['timeslot']
        room = body['room']

        if movie_name is None or date is None or timeslot is None or room is None:
            return JsonResponse({
                'message': 'Missing key to create'
            }, status=status.HTTP_400_BAD_REQUEST)
        


        try:
            movie = Movie.objects.create(name=body['name'], duration=body['duration'], rating=body['rating'])
        except KeyError:
            return JsonResponse({
                'message': 'Missing key to create'
            }, status=status.HTTP_400_BAD_REQUEST)

        if movie is None:
            return JsonResponse({
                'message': 'Add movie unsuccessfully'
            }, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({
            'message': 'Add movie successfully'
        }, status=status.HTTP_201_CREATED)

# Delete movie
def del_movie(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        _id = body['id']
        print(_id)
        if _id is None:
            return JsonResponse({
                'message': 'No movie deleted'
            }, status=status.HTTP_200_OK)
        
        del_status = Movie.objects.filter(_id=_id).delete()

        return JsonResponse({
            'message': '{} movie deleted'.format(del_status[0])
        }, status=status.HTTP_200_OK)

# Update movie
def update_movie(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        _id = body['id']
        print(_id)
        if _id is None:
            return JsonResponse({
                'message': 'No movie selected'
            }, status=status.HTTP_200_OK)
        
        movie = Movie.objects.get(_id=_id)
        movie.name = body['name']
        movie.duration = body['duration']
        movie.rating = body['rating']
        movie.save()

        return JsonResponse({
            'message': 'Update movie successfully'
        }, status=status.HTTP_200_OK)

# Get gerne
def get_gerne(request):
    if request.method == 'GET':
        all_gerne = serialize(Gerne.objects.all(), fields=('name'))
        return JsonResponse({'data' : [x['fields'] for x in all_gerne]})

# Create gerne
def add_gerne(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        try:
            gerne = Gerne.objects.create(name=body['name'])
        except KeyError:
            return JsonResponse({
                'message': 'Missing key to create gerne'
            }, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({
            'message': 'Add successfully gerne'
        }, status=status.HTTP_201_CREATED)

# Update gerne
def update_gerne(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        _id = body['id']
        print(_id)
        if _id is None:
            return JsonResponse({
                'message': 'No gerne selected'
            }, status=status.HTTP_200_OK)
        
        gerne = Gerne.objects.get(_id=_id)
        gerne.name = body['name']
        gerne.save()

        return JsonResponse({
            'message': 'Update gerne successfully'
        }, status=status.HTTP_200_OK)

# Create movie_gerne
def create_movie_gerne(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        try:
            id_movie = body['id_movie']
            id_gerne = body['id_gerne']
        except KeyError:
            return JsonResponse({
                'message': 'Missing key to create movie_gerne'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        movie_gerne = Movie_Gerne.objects.create(movie_id=id_movie, gerne_id=id_gerne)

        return JsonResponse({
            'message': 'Add movie_gerne successfully'
        }, status=status.HTTP_201_CREATED)
        