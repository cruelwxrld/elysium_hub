from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet, ProfileViewSet, OrderViewSet, SearchViewSet

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'profile', ProfileViewSet)
router.register(r'order', OrderViewSet)
router.register(r'search', SearchViewSet, basename='search')

urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth/', include('rest_framework.urls')),
]