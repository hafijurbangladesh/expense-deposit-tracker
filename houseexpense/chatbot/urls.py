from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('webhook/', views.webhook, name='webhook'),
]
