from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError
#User authorization
from users.permission import IsRecruiter, IsJobSeeker
#importing Model Serializers 
from .serializers import JobInfoSerializer, JobApplicationSerializer
#importing Model classes
from .models import JobInfo, JobApplication
from users.models import Recruiter, JobSeeker
from django.db.models import Q
# Email modules
from django.core.mail import send_mail
from jobbackend.settings import EMAIL_HOST_USER

# Create your views here.

# JobInfoViewSet Endpoint

# End point to display all jobs posted -> for job seekers
# End point to display and create job by recruiters -> for recruiter

# List -> of all jobs created by the recruiter can be seen by both js and recruiter(only jobs created by them)
# Create -> Only recruiter can create jobs and job seeker can be notifiled in email whose profile matches the job skillset

class JobInfoViewSet(viewsets.ModelViewSet):
    serializer_class = JobInfoSerializer

    def get_permissions(self):
        print(self.action)
        if self.action == 'create':
            self.permission_classes = [IsRecruiter]
        if self.action == 'list':
            self.permission_classes = [IsJobSeeker|IsRecruiter]

        return super().get_permissions()
  
    def list(self, request):
        serializer = JobInfoSerializer(JobInfo.objects.all(), many=True)
        return Response(serializer.data)

    def create(self, request):
        # Recruiter creating the job post
        try:
            title = request.data.get('title')
            experience = request.data.get('experience')
            location = request.data.get('location')

            # check whether the data is already present in the db or not
            if JobInfo.objects.filter(title=title, experience=experience, location=location).exists():
                raise ValidationError({"detail": "A job posting with this info already exists.."})

            recruiter = Recruiter.objects.get(user_id=request.user.id)
            print(f"recruiter: {recruiter.id}")
            mutable_data = request.data.copy()
            mutable_data['recruiter'] = recruiter.id
            serializer = JobInfoSerializer(data = mutable_data)

            if serializer.is_valid():
                # To send an email to job seekers who has matching skills given in job application
                queries = Q()
                jobRequired_skills = mutable_data['skills_preferred']
                jobRequired_skills = jobRequired_skills.split(',') if ',' in jobRequired_skills else [jobRequired_skills]
                for skill in jobRequired_skills:
                    print(skill)
                    queries |= Q(skills__icontains=skill)
                print(f"Queries: {queries}")
                queryset = JobSeeker.objects.filter(queries)
                emailList = []
                usernameList = []
                for id in queryset:
                    print(f"Job seeker with matching skillset:: {id.user.username}")
                    usernameList.append(id.user.username)
                    emailList.append(id.user.email)
                # Send email
                for i in range(len(emailList)):
                    send_mail(subject="New job Alert",
                    message=f"Hi {usernameList[i]}, \n We have found new job posting matching your skillset Please apply. \
                    \n Job title:{mutable_data['title']} posted by {request.user.username} few moments ago",
                    from_email=EMAIL_HOST_USER,
                    recipient_list=[emailList[i]],
                    fail_silently=False)
                    print(f'Email sent to :: {usernameList[i]}')
                # Save the job creation informtaion to dB
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f'Error in Job creation: {e}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# JobApplicationViewSet

# End point to apply for jobs -> for job seekers
# End point to display jobs that has applicants seen by recruiters -> for recruiter
# List -> list only jobs created by the recruiter (can be removed as it's already covered in JobInfo List)
# Create -> Apply for specific job with job id by job seeker

class JobApplicationViewSet(viewsets.ModelViewSet):
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer

    def get_permissions(self):
        print(self.action)
        if self.action == 'create':
            self.permission_classes = [IsJobSeeker]
        if self.action == 'list':
            self.permission_classes = [IsRecruiter]

        return super().get_permissions()

    def list(self, request):
        # Display only jobs created by the respective recruiter
        print(f'user id: {request.user.id}')

        recruiter_id = Recruiter.objects.get(user_id=request.user.id).id

        jobs = JobApplication.objects.filter(recruiter_id_id = recruiter_id)
        serializer = JobApplicationSerializer(jobs, many=True)
        return Response(serializer.data)

    def create(self, request):
        # Job seeker applying for the job
        jobseeker = request.user
        mutable_data = request.data.copy()
        mutable_data['jobseeker'] = jobseeker

        # check whether the data is already present in the db or not
        jobseeker_id = JobSeeker.objects.get(user_id=request.user.id)
        if JobApplication.objects.filter(jobinfo_id=mutable_data['jobinfo'], \
                                  jobseeker_id = jobseeker_id).exists():
            raise ValidationError({"detail": "You have already applied for the job.."})
        print(f"job info: {mutable_data['jobinfo']}")
        serializer = JobApplicationSerializer(data = mutable_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Preference based job suggestion (Based on skill matching from job seeker's skills and job required skill)

class JobPreferenceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsJobSeeker]
    def list(self, request):
        # Query builder
        queries = Q()

        jobseeker_skills = JobSeeker.objects.get(user_id=request.user.id).skills
        jobseeker_skills = jobseeker_skills.split(',') if ',' in jobseeker_skills else [jobseeker_skills]
        print(jobseeker_skills)
        for skill in jobseeker_skills:
            print(skill)
            #Preparing the queries to filter models next
            queries |= Q(skills_preferred__icontains=skill)
        jobs = JobInfo.objects.filter(queries)
        serializer = JobInfoSerializer(jobs, many=True)
        print(serializer.data)
        return Response(serializer.data)
    