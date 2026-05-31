from django.urls import path, include
from django.views.generic import TemplateView
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
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),

    path('api/subcategories/', views.SearchViewSet.as_view({'get': 'get_subcategories'}), name='subcategories'),

    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('become-performer/', views.become_performer_view, name='become_performer'),

    path('', views.home, name='home'),

    path('create-order/', views.OrderViewSet.create_order_view, name='create_order'),
    path('my-orders/', views.OrderViewSet.my_orders_view, name='my_orders'),

    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),

    path('api/performer/<int:performer_id>/', views.SearchViewSet.as_view({'get': 'get_performer_profile'}), name='performer_profile'),

    path('api/categories/<slug:category_slug>/subcategories/', views.SearchViewSet.as_view({'get': 'get_subcategories'}), name='subcategories'),
]