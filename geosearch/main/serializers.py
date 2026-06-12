from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Order, Review, Notification

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Profile
        fields = '__all__'
        read_only_fields = ['rating', 'completed_orders', 'created_at', 'updated_at']

class OrderSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.username', read_only=True)
    performer_name = serializers.CharField(source='performer.username', read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['client', 'created_at', 'updated_at', 'status']

class ReviewSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.username', read_only=True)
    performer_name = serializers.CharField(source='performer.username', read_only=True)

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['client', 'created_at']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'