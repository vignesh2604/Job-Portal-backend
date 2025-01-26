from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


# Create your models here.

class CustomUser(AbstractUser):
    is_jobseeker = models.BooleanField(default=False)
    is_recruiter = models.BooleanField(default=False)
    is_logged_in = models.BooleanField(default=False)

class JobSeeker(models.Model):
    # Foreign Key
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    # Job seeker profile information
    resume = models.FileField(upload_to='resume/')
    photo = models.ImageField(upload_to='profile/')
    experience = models.IntegerField(default=0)
    company = models.TextField(null=True, blank=True)
    location = models.CharField(null=True, blank=True, max_length=100)
    job_title = models.CharField(null=True, blank=True, max_length=50)
    education = models.TextField(null=True, blank=True)
    skills = models.TextField(default='', max_length=200)
    created_ts = models.DateTimeField(auto_now_add=True)
    updated_ts = models.DateTimeField(auto_now=True)

class Recruiter(models.Model):
    # Foreign Key
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    # Recruiter profile information
    resume = models.FileField(upload_to='resume/')
    photo = models.ImageField(upload_to='profile/')
    experience = models.IntegerField(default=0)
    company = models.TextField(null=True, blank=True)
    location = models.CharField(null=True, blank=True, max_length=100)
    job_title = models.CharField(null=True, blank=True, max_length=50)
    education = models.TextField(null=True, blank=True)
    skills = models.TextField(default='', max_length=200)
    created_ts = models.DateTimeField(auto_now_add=True)
    updated_ts = models.DateTimeField(auto_now=True)

