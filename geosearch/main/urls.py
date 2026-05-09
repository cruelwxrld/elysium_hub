from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'profile', views.ProfileViewSet)
router.register(r'orders', views.OrderViewSet)

router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'search', views.SearchViewSet, basename='search')

urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth/', views.ObtainAuthToken.as_view()),
]