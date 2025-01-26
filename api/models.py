from django.db import models
from django.contrib.auth.models import AbstractUser
from users.models import Recruiter, JobSeeker
# Create your models here.

# Creating a model for Job information

class JobInfo(models.Model):
    recruiter = models.ForeignKey(Recruiter, on_delete=models.CASCADE)
    title = models.CharField(max_length=50, null=False)
    experience = models.CharField(max_length=10, null=False)
    company = models.CharField(max_length=100, null=False)
    location = models.CharField(max_length=100, null=False)
    job_description = models.TextField(null=True, blank=True)
    job_type = models.CharField(max_length=50, null=False, default='Full-time')
    skills_preferred = models.TextField(null=True, blank=True)
    education_preferred = models.TextField(null=True, blank=True)
    created_ts = models.DateTimeField(auto_now_add=True)
    salary = models.FloatField(null=True, blank=True)

    # To describe uniqueness in the data being created
    class Meta:
        unique_together = ('title', 'company', 'experience', 
                            'location', 'salary', 'job_description')

    def __str__(self):
        return self.title

class JobApplication(models.Model):
    # Foreign Key to allow multiple job seekers to apply for multiple jobs
    jobseeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE)
    jobinfo = models.ForeignKey(JobInfo, on_delete=models.CASCADE)
    recruiter_id = models.OneToOneField(Recruiter, on_delete=models.CASCADE)
    # Job seeker application form
    resume = models.FileField(upload_to='resume/')
    email = models.EmailField(max_length=100)
    experience = models.IntegerField(default=0)
    current_company = models.TextField(null=True, blank=True)
    current_location = models.CharField(null=True, blank=True, max_length=100)
    current_job_title = models.CharField(null=True, blank=True, max_length=50)
    current_education = models.TextField(null=True, blank=True)
    created_ts = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email