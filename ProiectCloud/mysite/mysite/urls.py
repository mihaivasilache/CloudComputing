from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', include( ('polls.urls', "polls"), namespace="polls")),
    path('admin/', admin.site.urls),
    path('', include('social_django.urls', namespace='social')), 
]