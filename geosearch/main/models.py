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

    services = models.TextField(blank=True, help_text="Услуги, которые предоставляет исполнитель (через запятую)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    def get_services_list(self):
        """Возвращает список услуг исполнителя"""
        if self.services:
            return [s.strip() for s in self.services.split(',')]
        return []

    def update_rating(self):
        """Обновление рейтинга исполнителя на основе всех отзывов"""
        from .models import Review
        reviews = Review.objects.filter(performer=self.user)
        if reviews.exists():
            avg = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.rating = round(avg, 1)
            self.save()
        else:
            self.rating = 0
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
        ('pending', 'Ожидает исполнителя'),
        ('accepted', 'Принят исполнителем'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
        ('waiting_confirmation', 'Ожидает подтверждения'),
    ]

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_as_client')
    performer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders_as_performer')

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50)
    subcategory = models.CharField(max_length=200, blank=True, null=True)  # Добавьте это поле
    subcategory_details = models.TextField(blank=True, null=True)  # Дополнительные детали

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


class ServiceCategory(models.Model):
    """Основная категория услуг"""
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)
    slug = models.SlugField(unique=True)
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Категория услуг'
        verbose_name_plural = 'Категории услуг'
        ordering = ['order']

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    """Подкатегория услуг (детализация)"""
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price_modifier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, help_text="Множитель цены")
    estimated_time = models.IntegerField(default=60, help_text="Примерное время выполнения в минутах")
    is_popular = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Подкатегория'
        verbose_name_plural = 'Подкатегории'
        ordering = ['category', 'order']

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('new_order', 'Новый заказ'),
        ('order_accepted', 'Заказ принят'),
        ('order_completed', 'Заказ завершен'),
        ('order_cancelled', 'Заказ отменен'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    order = models.ForeignKey('Order', on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"
