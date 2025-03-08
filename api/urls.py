from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'jobs', views.JobInfoViewSet, basename='jobs')

router.register(r'apply', views.JobApplicationViewSet, basename='apply')

router.register(r'preferences', views.JobPreferenceViewSet, basename='preferences')

router.register(r'jobrecommendation', views.JobRecommendationViewSet, basename='jobrecommendation')

router.register(r'displayappliedjobs', views.AppliedJobs, basename='displayappliedjobs')

router.register(r'filters', views.JobFilters, basename='filters')

router.register(r'jobsbyrecruiter', views.CreatedJobByRecruiters, basename='jobsbyrecruiter')

urlpatterns = [
    path('', include(router.urls)),

]