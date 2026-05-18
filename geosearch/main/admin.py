from django.contrib import admin
from .models import Profile, Order, Review, ServiceCategory, Subcategory

# Register your models here.
@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price_modifier', 'estimated_time', 'is_popular']
    list_filter = ['category', 'is_popular']
    search_fields = ['name', 'description']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'rating']
    list_filter = ['role', 'is_available']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['title', 'client', 'performer', 'status', 'budget', 'created_at']
    list_filter = ['status', 'category']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['order', 'client', 'performer', 'rating', 'created_at']