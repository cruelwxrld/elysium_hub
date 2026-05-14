from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views

router = DefaultRouter()
router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'profiles', views.ProfileViewSet, basename='profile')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'search', views.SearchViewSet, basename='search')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api-token-auth/', obtain_auth_token),
    path('', views.home, name='home'),
]