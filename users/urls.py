from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'user', views.CustomUserViewSet, basename='user')

router.register(r'jobseeker', views.JobSeekerViewSet, basename='jobseeker')

router.register(r'recruiter', views.RecruiterViewSet, basename='recruiter')


urlpatterns = [
    path('', include(router.urls)),
    path('fetchUser/', views.fetchUserDetails.as_view(), name='fetchUser'),
    path('getJobseekers/', views.RetrieveJobSeekersList.as_view(), name="getJobseekers"),
    path('notify/', views.NotifyJobSeekers.as_view(), name="notify"),
]