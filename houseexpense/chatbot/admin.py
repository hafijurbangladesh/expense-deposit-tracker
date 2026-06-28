from django.contrib import admin
from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'direction', 'message', 'created_at')
    list_filter = ('direction', 'created_at')
    search_fields = ('phone_number', 'message')
    readonly_fields = ('created_at',)
