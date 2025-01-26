from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'jobs', views.JobInfoViewSet, basename='jobs')

router.register(r'apply', views.JobApplicationViewSet, basename='apply')

urlpatterns = [
    path('', include(router.urls)),
]