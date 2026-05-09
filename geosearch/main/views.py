from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db.models import Q
from math import radians, sin, cos, sqrt, atan2
from .models import Profile, Order, Review
from .serializers import *
import requests

# Create your views here.
class AuthViewSet(viewsets.ViewSet):
    """API для аутентификации"""
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Регистрация пользователя"""
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        role = request.data.get('role', 'client')

        if not username or not password:
            return Response({'error': 'Логин и пароль обязательны'}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Пользователь уже существует'}, status=400)

        user = User.objects.create_user(username=username, password=password, email=email)
        user.profile.role = role
        user.profile.save()

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'role': role
        })

    @action(detail=False, methods=['post'])
    def login(self, request):
        """Вход пользователю"""
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            return Response({'error': 'Неверные учетные данные'}, status=401)

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'role': user.profile.role
        })

class ProfileViewSet(viewsets.ModelViewSet):
    """Управление профилем"""
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get', 'put'])
    def me(self, request):
        """Обновить свой профиль"""
        if not request.user.is_authenticated:
            return Response({'error': 'Требуется авторизация'}, status=401)

        profile = request.user.profile

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=400)

    @action(detail=False, methods=['post'])
    def update_location(self, request):
        """Обновление геолокации"""
        if not request.user.is_authenticated:
            return Response({'error': 'Требуется авторизация'}, status=401)

        lat = request.data.get('latitude')
        lng = request.data.get('longitude')
        address = request.data.get('address', '')

        profile = request.user.profile
        profile.latitude = float(lat)
        profile.longitude = float(lng)
        profile.address = address
        profile.save()

        return Response({'status': 'ok', 'latitude': lat, 'longitude': lng})

class OrderViewSet(viewsets.ModelViewSet):
    """Управление заказами"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Order.objects.all()

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        if self.request.user.is_authenticated:
            user_type = self.request.query_params.get('as')
            if user_type == 'client':
                queryset = queryset.filter(client=self.request.user)
            elif user_type == 'performer':
                queryset = queryset.filter(performer=self.request.user)

        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

class SearchViewSet(viewsets.ViewSet):
    """Поиск исполнителей"""
    permission_classes = [AllowAny]

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        R = 6373.0

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon/2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    @action(detail=False, methods=['get'])
    def find_performers(self, request):
        """Поиск исполнителей по геолокации"""
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = float(request.query_params.get('radius', 10))
        category = request.query_params.get('category', '')

        lat = float(lat)
        lng = float(lng)

        performers = Profile.objects.filter(
            role='performer',
            latitude__isnull=False,
            longitude__isnull=False,
            is_available=True,
        )

        if category:
            performers = performers.filter(category=category)

        results = []

        for performer in performers:
            distance = self.calculate_distance(
                lat, lng,
                performer.latitude, performer.longitude
            )

            if distance <= radius:
                performer_data = ProfileSerializer(performer).data
                performer_data['distance_km'] = round(distance, 2)
                results.append(performer_data)
        results.sort(key=lambda x: x['distance_km'])

        return Response({
            'count': len(results),
            'results': results[:50],
            'search_params': {
                'latitude': lat,
                'longitude': lng,
                'radius': radius,
                'category': category,
            }
        })

    @action(detail=False, methods=['get'])
    def geocode(self, request):
        """Преобразование адреса в координаты"""
        address = request.query_params.get('address')
        if not address:
            return Response({'error': 'Адрес обязатателен'}, status=400)

        try:
            responce = requests.get(
                'https://nominatim.openstreetmap.org/search',
                params={
                    'q': address,
                    'format': 'json',
                    'limit': 1,
                },
                headers={'User-Agent': 'GeoFindApp/1.0'}
            )

            if responce.status_code == 200:
                data = responce.json()
                if data:
                    return Response({
                        'latitude': float(data[0]['lat']),
                        'longitude': float(data[0]['lon']),
                        'display_name': data[0]['display_name'],
                    })
            return Response({'error': 'Адрес не найден'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['get'])
    def reverse_geocode(self, request):
        """Преобразование координат в адресс"""
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')

        try:
            responce = requests.get(
                'https://nominatim.openstreetmap.org/reverse',
                params={
                    'lat': lat,
                    'lng': lng,
                    'format': 'json',
                },
                headers={'User-Agent': 'GeoFindApp/1.0'}
            )

            if responce.status_code == 200:
                data = responce.json()
                return Response({
                    'address': data.get('display_name', ''),
                })
            return Response({'error': 'Не удалось определить адресс'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)