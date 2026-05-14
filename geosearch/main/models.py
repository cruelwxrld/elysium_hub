from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    """Профиль пользователя"""
    ROLE_CHOICES = [
        ('client', 'Заказчик'),
        ('performer', 'Исполнитель'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')

    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    address = models.CharField(max_length=500, blank=True)

    category = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    rating = models.FloatField(default=0)
    completed_orders = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    def update_rating(self):
        """Обновление рейтинга"""
        from .models import Review
        reviews = Review.objects.filter(performer=self.user)
        if reviews.exists():
            avg = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.rating = round(avg, 1)
            self.save()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создает профиль при создании пользователя"""
    if created:
        Profile.objects.create(user=instance)
        print(f"✅ Профиль создан для пользователя: {instance.username}")

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сохраняет профиль при сохранении пользователя"""
    instance.profile.save()

class Order(models.Model):
    """Заказ услуги"""
    STATUS_CHOICES = [
        ('pending', 'Ожидание'),
        ('accepted', 'Принят исполнителем'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ]

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client')
    performer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='performer')

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50)

    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.CharField(max_length=500)

    budget = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Review(models.Model):
    """Отзыв на исполнителя"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    performer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if hasattr(self.performer, 'profile'):
            self.performer.profile.update_rating()
