"""
URL configuration for houseexpense project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('houseexpense.accounts.urls')),
    path('dashboard/', include('houseexpense.dashboard.urls')),
    path('reports/', include('houseexpense.reports.urls')),
    path('chatbot/', include('houseexpense.chatbot.urls')),
    path('', include('houseexpense.core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
