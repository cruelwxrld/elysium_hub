from django.contrib import admin
from .models import Category, Subcategory, Profile, Order, Review, Notification


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'order']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order']


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'order']
    list_filter = ['category']
    ordering = ['category', 'order']
    search_fields = ['name']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'rating', 'is_available']
    list_filter = ['role', 'is_available']
    search_fields = ['user__username', 'phone']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'client', 'performer', 'status', 'budget', 'created_at']
    list_filter = ['status', 'category']
    search_fields = ['title', 'client__username', 'performer__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['order', 'client', 'performer', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['client__username', 'performer__username']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'type', 'is_read', 'created_at']
    list_filter = ['type', 'is_read']
    search_fields = ['user__username', 'title']
    readonly_fields = ['created_at']