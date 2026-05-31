from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from math import radians, sin, cos, sqrt, atan2
from .models import Profile, Order, Review
from .serializers import *
import requests
from django.contrib.auth.decorators import login_required
from django.conf import settings


class AuthViewSet(viewsets.ViewSet):
    """API для аутентификации"""
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Регистрация пользователя"""
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')
        phone = request.data.get('phone', '')
        role = request.data.get('role', 'client')

        if not username or not password:
            return Response({'error': 'Логин и пароль обязательны'}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Пользователь уже существует'}, status=400)

        try:
            user = User.objects.create_user(username=username, password=password, email=email)

            Profile.objects.create(
                user=user,
                phone=phone,
                role=role,
                is_available=True,
                rating=0,
                completed_orders=0
            )

            token, _ = Token.objects.get_or_create(user=user)

            return Response({
                'success': True,
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'role': role,
                'message': 'Регистрация успешна'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=False, methods=['post'])
    def login(self, request):
        """Вход пользователя"""
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Логин и пароль обязательны'}, status=400)

        user = authenticate(username=username, password=password)

        if not user:
            return Response({'error': 'Неверные учетные данные'}, status=401)

        try:
            profile = user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(
                user=user,
                role='client',
                is_available=True,
                rating=0,
                completed_orders=0
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'success': True,
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'role': profile.role,
            'message': f'Добро пожаловать, {user.username}!'
        })

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Выход пользователя"""
        if request.user.is_authenticated:
            Token.objects.filter(user=request.user).delete()
            return Response({'success': True, 'message': 'Вы вышли из системы'})
        return Response({'error': 'Вы не авторизованы'}, status=401)


class ProfileViewSet(viewsets.ModelViewSet):
    """Управление профилем"""
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get', 'put'])
    def me(self, request):
        """Получить или обновить свой профиль"""
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
        """Фильтрация заказов по параметрам"""
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
        """Создание заказа с текущим пользователем как клиентом"""
        serializer.save(client=self.request.user)

    @login_required
    def create_order_view(request):
        """Страница создания заказа"""
        performers = Profile.objects.filter(
            role='performer',
            is_available=True
        ).select_related('user')

        if request.method == 'POST':
            title = request.POST.get('title')
            description = request.POST.get('description')
            category = request.POST.get('category')
            subcategory = request.POST.get('subcategory')
            budget = request.POST.get('budget')
            deadline = request.POST.get('deadline')
            address = request.POST.get('address')
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            performer_id = request.POST.get('performer_id')

            if not all([title, description, category, budget]):
                messages.error(request, 'Заполните все обязательные поля')
                return redirect('create_order')

            full_description = description
            if subcategory:
                full_description = f"Услуга: {subcategory}\n\n{description}"

            order = Order.objects.create(
                client=request.user,
                title=title,
                description=full_description,
                category=category,
                budget=budget,
                address=address or 'По согласованию',
                latitude=float(latitude) if latitude else request.user.profile.latitude or 55.751244,
                longitude=float(longitude) if longitude else request.user.profile.longitude or 37.618423,
                status='pending'
            )

            if performer_id:
                try:
                    performer = User.objects.get(id=performer_id)
                    order.performer = performer
                    order.status = 'accepted'
                    order.save()
                    messages.success(request, f'Заказ "{title}" отправлен исполнителю!')
                except User.DoesNotExist:
                    messages.warning(request, 'Заказ создан, но исполнитель не найден')
            else:
                messages.success(request, f'Заказ "{title}" успешно создан! Ожидайте отклика исполнителей')

            return redirect('my_orders')

        categories = [
            ('cleaning', '🧹 Уборка'),
            ('repair', '🔧 Ремонт'),
            ('delivery', '🚚 Доставка'),
            ('construction', '🏗️ Строительство'),
            ('design', '🎨 Дизайн'),
            ('photography', '📸 Фотография'),
            ('it', '💻 IT'),
            ('education', '📚 Образование'),
            ('beauty', '💅 Красота'),
        ]

        subcategories_data = {
            'cleaning': ['Комплексная уборка', 'Уборка после ремонта', 'Мытье окон', 'Химчистка мебели',
                         'Уборка офисов'],
            'repair': ['Поклейка обоев', 'Укладка ламината', 'Установка дверей', 'Монтаж потолков', 'Сантехника',
                       'Электрика', 'Сборка мебели'],
            'delivery': ['Доставка продуктов', 'Доставка еды', 'Курьерская доставка', 'Грузоперевозки'],
            'construction': ['Отделка квартир', 'Перепланировка', 'Фасадные работы', 'Кровля'],
            'design': ['Дизайн интерьера', '3D визуализация', 'Ландшафтный дизайн', 'Веб-дизайн'],
            'photography': ['Свадебная съемка', 'Портретная съемка', 'Репортаж', 'Предметная съемка'],
            'it': ['Разработка сайтов', 'Мобильные приложения', 'Настройка серверов', 'IT-консалтинг'],
            'education': ['Репетиторство', 'Курсы', 'Изучение языков', 'Подготовка к экзаменам'],
            'beauty': ['Парикмахер', 'Маникюр', 'Косметология', 'Визаж', 'Массаж'],
        }

        context = {
            'performers': performers,
            'categories': categories,
            'subcategories_data': subcategories_data,
            'selected_performer_id': request.GET.get('performer_id'),
            'user_location': request.user.profile,
        }
        return render(request, 'create_order.html', context)

    @login_required
    def my_orders_view(request):
        """Страница моих заказов"""
        orders_as_client = Order.objects.filter(client=request.user).order_by('-created_at')
        orders_as_performer = Order.objects.filter(performer=request.user).order_by(
            '-created_at') if request.user.profile.role == 'performer' else []

        context = {
            'client_orders': orders_as_client,
            'performer_orders': orders_as_performer,
        }
        return render(request, 'my_orders.html', context)


class SearchViewSet(viewsets.ViewSet):
    """Поиск исполнителей"""
    permission_classes = [AllowAny]

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Расчет расстояния между двумя точками в километрах"""
        R = 6373.0

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon/2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    @action(detail=False, methods=['get'], url_path='performer/(?P<performer_id>[^/.]+)')
    def get_performer_profile_api(self, request, performer_id=None):
        """Получение профиля исполнителя по API"""
        if not performer_id:
            return Response({'error': 'performer_id обязателен'}, status=400)

        try:
            from django.contrib.auth.models import User
            user = User.objects.get(id=performer_id)
            profile = user.profile

            if profile.role != 'performer':
                return JsonResponse({'error': 'Пользователь не является исполнителем'}, status=400)

            services_list = []
            if profile.services:
                services_list = [s.strip() for s in profile.services.split(',') if s.strip()]

            if not services_list and profile.category:
                default_services = {
                    'cleaning': ['Комплексная уборка', 'Уборка после ремонта', 'Мытье окон'],
                    'repair': ['Поклейка обоев', 'Укладка ламината', 'Сантехника', 'Электрика'],
                    'delivery': ['Доставка продуктов', 'Доставка еды', 'Курьерская доставка'],
                    'it': ['Разработка сайтов', 'Настройка серверов', 'IT-консалтинг'],
                }
                services_list = default_services.get(profile.category, [])

            return JsonResponse({
                'id': user.id,
                'username': user.username,
                'category': profile.category,
                'price': float(profile.price) if profile.price else None,
                'services': services_list,
                'description': profile.description,
                'rating': profile.rating,
                'phone': profile.phone,
                'completed_orders': profile.completed_orders
            })
        except User.DoesNotExist:
            return JsonResponse({'error': 'Исполнитель не найден'}, status=404)

    @action(detail=False, methods=['get'])
    def find_performers(self, request):
        """Поиск исполнителей по геолокации и услугам"""
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = float(request.query_params.get('radius', 10))
        category = request.query_params.get('category', '')
        service = request.query_params.get('service', '')  # Конкретная услуга

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

        if service:
            performers = performers.filter(services__icontains=service)

        results = []
        for performer in performers:
            distance = self.calculate_distance(
                lat, lng,
                performer.latitude, performer.longitude
            )

            if distance <= radius:
                performer_data = ProfileSerializer(performer).data
                performer_data['distance_km'] = round(distance, 2)
                performer_data['services_list'] = performer.get_services_list() if hasattr(performer,
                                                                                           'get_services_list') else []
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
                'service': service,
            }
        })

    @action(detail=False, methods=['get'])
    def geocode(self, request):
        """Преобразование адреса в координаты через Яндекс.Геокодер"""
        address = request.query_params.get('address')
        if not address:
            return Response({'error': 'Адрес обязателен'}, status=400)

        try:
            response = requests.get(
                'https://geocode-maps.yandex.ru/1.x/',
                params={
                    'apikey': settings.YANDEX_GEOCODER_API_KEY,
                    'geocode': address,
                    'format': 'json',
                    'limit': 1,
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                try:
                    geo_object = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
                    pos = geo_object['Point']['pos'].split()
                    longitude, latitude = float(pos[0]), float(pos[1])

                    return Response({
                        'latitude': latitude,
                        'longitude': longitude,
                        'display_name': geo_object.get('name', address),
                        'address': geo_object.get('description', address),
                    })
                except (IndexError, KeyError):
                    return Response({'error': 'Адрес не найден'}, status=404)
            return Response({'error': 'Ошибка геокодирования'}, status=500)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['get'])
    def reverse_geocode(self, request):
        """Преобразование координат в адрес через Яндекс.Геокодер"""
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')

        if not lat or not lng:
            return Response({'error': 'lat и lng обязательны'}, status=400)

        try:
            response = requests.get(
                'https://geocode-maps.yandex.ru/1.x/',
                params={
                    'apikey': settings.YANDEX_GEOCODER_API_KEY,
                    'geocode': f"{lng},{lat}",
                    'format': 'json',
                    'lang': 'ru_RU'
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                try:
                    geo_object = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
                    address = geo_object['metaDataProperty']['GeocoderMetaData']['text']

                    return Response({
                        'address': address,
                        'display_name': address
                    })
                except (IndexError, KeyError):
                    return Response({'error': 'Адрес не найден'}, status=404)
            return Response({'error': 'Ошибка геокодирования'}, status=500)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['get'])
    def get_subcategories(self, request):
        """Получение подкатегорий для выбранной категории"""
        category_slug = request.query_params.get('category')

        if not category_slug:
            return Response({'error': 'Категория не указана'}, status=400)

        try:
            from .models import ServiceCategory, Subcategory

            category_map = {
                'cleaning': 'cleaning',
                'repair': 'repair',
                'delivery': 'delivery',
                'construction': 'construction',
                'design': 'design',
                'photography': 'photography',
                'it': 'it',
                'education': 'education',
                'beauty': 'beauty',
            }

            category_name = category_map.get(category_slug, category_slug)

            category = ServiceCategory.objects.filter(slug=category_slug).first()

            if not category:
                default_subcategories = {
                    'cleaning': ['Комплексная уборка', 'Уборка после ремонта', 'Мытье окон', 'Химчистка мебели'],
                    'repair': ['Поклейка обоев', 'Укладка ламината', 'Установка дверей', 'Монтаж потолков',
                               'Сантехника', 'Электрика'],
                    'delivery': ['Доставка продуктов', 'Доставка еды', 'Курьерская доставка', 'Грузоперевозки'],
                    'construction': ['Отделка квартир', 'Перепланировка', 'Фасадные работы', 'Кровля'],
                    'design': ['Дизайн интерьера', '3D визуализация', 'Ландшафтный дизайн', 'Веб-дизайн'],
                    'photography': ['Свадебная съемка', 'Портретная съемка', 'Репортаж', 'Предметная съемка'],
                    'it': ['Разработка сайтов', 'Мобильные приложения', 'Настройка серверов', 'IT-консалтинг'],
                    'education': ['Репетиторство', 'Курсы', 'Языки', 'Подготовка к экзаменам'],
                    'beauty': ['Парикмахер', 'Маникюр', 'Косметология', 'Визаж', 'Массаж'],
                }

                sub_names = default_subcategories.get(category_slug, [])
                subcategories = [{'id': i, 'name': name, 'description': ''} for i, name in enumerate(sub_names)]
            else:
                subcategories = list(category.subcategories.values('id', 'name', 'description', 'estimated_time'))

            return Response({
                'success': True,
                'category': category_slug,
                'subcategories': subcategories
            })

        except Exception as e:
            return Response({'error': str(e)}, status=500)


def home(request):
    """Главная страница"""
    return render(request, 'index.html')


@login_required
def profile_view(request):
    """Личный кабинет пользователя"""
    profile = request.user.profile

    if request.method == 'POST':
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if phone:
            profile.phone = phone
        if address:
            profile.address = address
        if latitude and longitude:
            profile.latitude = float(latitude)
            profile.longitude = float(longitude)

        if profile.role == 'performer':
            category = request.POST.get('category')
            price = request.POST.get('price')
            description = request.POST.get('description')

            if category:
                profile.category = category
            if price:
                profile.price = float(price)
            if description:
                profile.description = description

        profile.save()
        messages.success(request, 'Профиль обновлен')
        return redirect('profile')

    orders_as_client = Order.objects.filter(client=request.user).order_by('-created_at')[:10]
    orders_as_performer = Order.objects.filter(performer=request.user).order_by('-created_at')[
        :10] if profile.role == 'performer' else []

    context = {
        'profile': profile,
        'orders_as_client': orders_as_client,
        'orders_as_performer': orders_as_performer,
        'categories': Profile.ROLE_CHOICES if hasattr(Profile, 'ROLE_CHOICES') else [],
    }
    return render(request, 'profile.html', context)


@login_required
def edit_profile_view(request):
    """Редактирование профиля"""
    profile = request.user.profile

    if request.method == 'POST':
        profile.phone = request.POST.get('phone', profile.phone)
        profile.address = request.POST.get('address', profile.address)

        if profile.role == 'performer':
            profile.category = request.POST.get('category', profile.category)
            price_value = request.POST.get('price', '')
            profile.price = float(price_value) if price_value and price_value.strip() else None

            profile.description = request.POST.get('description', profile.description)
            profile.is_available = request.POST.get('is_available') == 'on'
            services = request.POST.get('services', '')
            profile.services = services

        profile.save()
        messages.success(request, 'Профиль успешно обновлен')
        return redirect('profile')

    categories = [
        ('cleaning', '🧹 Уборка'),
        ('repair', '🔧 Ремонт'),
        ('delivery', '🚚 Доставка'),
        ('construction', '🏗️ Строительство'),
        ('design', '🎨 Дизайн'),
        ('photography', '📸 Фотография'),
        ('it', '💻 IT'),
        ('education', '📚 Образование'),
        ('beauty', '💅 Красота'),
    ]

    context = {
        'profile': profile,
        'categories': categories,
    }
    return render(request, 'edit_profile.html', context)


@login_required
def become_performer_view(request):
    """Стать исполнителем"""
    profile = request.user.profile

    if request.method == 'POST':
        profile.role = 'performer'
        profile.category = request.POST.get('category')
        price_value = request.POST.get('price', '')
        profile.price = float(price_value) if price_value and price_value.strip() else None

        profile.description = request.POST.get('description', '')
        profile.is_available = True
        profile.save()
        messages.success(request, 'Поздравляем! Теперь вы исполнитель')
        return redirect('profile')

    categories = [
        ('cleaning', '🧹 Уборка'),
        ('repair', '🔧 Ремонт'),
        ('delivery', '🚚 Доставка'),
        ('construction', '🏗️ Строительство'),
        ('design', '🎨 Дизайн'),
        ('photography', '📸 Фотография'),
        ('it', '💻 IT'),
        ('education', '📚 Образование'),
        ('beauty', '💅 Красота'),
    ]

    context = {
        'categories': categories,
    }
    return render(request, 'become_performer.html', context)