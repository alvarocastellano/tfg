from django.db import models
from django.conf import settings

class Event(models.Model):
    city = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255)
    start = models.DateTimeField()
    end = models.DateTimeField()
    price = models.FloatField()
    dresscode = models.CharField(max_length=100, blank=True)
    associated_chat = models.ForeignKey('community.GroupChat', on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    tickets_link = models.URLField(blank=True, null=True)
    max_people = models.PositiveIntegerField(null=True, blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_events')

    def __str__(self):
        return f"{self.title} - {self.city}"
