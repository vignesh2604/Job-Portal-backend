from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError
#User authorization
from users.permission import IsRecruiter, IsJobSeeker
#importing Model Serializers 
from .serializers import JobInfoSerializer, JobApplicationSerializer, JobSeekerSerializer
#importing Model classes
from .models import JobInfo, JobApplication
from users.models import Recruiter, JobSeeker, CustomUser
from django.db.models import Q
# Email modules
from django.core.mail import send_mail
from jobbackend.settings import EMAIL_HOST_USER
# NLP model
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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
        # if self.action == 'list':
        #     self.permission_classes = [IsJobSeeker|IsRecruiter]

        return super().get_permissions()
  
    def list(self, request):
        serializer = JobInfoSerializer(JobInfo.objects.all(), many=True)
        return Response(serializer.data)

    def create(self, request):
    # Recruiter creating the job post
        try:
            title = request.data.get('title')
            experience = request.data.get('experience')
            location = request.data.get('location').capitalize()  # Capitalize location
            company = request.data.get('company').capitalize()
            # Capitalize the skills and industry fields
            jobRequired_skills = request.data.get('skills_preferred', '')
            industry = request.data.get('industry', '')
            
            # Capitalize skills
            if jobRequired_skills:
                jobRequired_skills = jobRequired_skills.split(',') if ',' in jobRequired_skills else [jobRequired_skills]
                jobRequired_skills = [skill.strip().capitalize() for skill in jobRequired_skills]

            # Capitalize industry
            industry = industry.capitalize()

            # Check whether the data is already present in the db or not
            if JobInfo.objects.filter(title=title, experience=experience, location=location).exists():
                raise ValidationError({"detail": "A job posting with this info already exists.."})

            recruiter = Recruiter.objects.get(user_id=request.user.id)
            print(f"recruiter: {recruiter.id}")

            mutable_data = request.data.copy()
            mutable_data['location'] = location  # Updated location
            mutable_data['skills_preferred'] = ', '.join(jobRequired_skills)  # Join the skills back to a comma-separated string
            mutable_data['industry'] = industry  # Join the industry back to a comma-separated string
            mutable_data['recruiter'] = recruiter.id
            mutable_data['company'] = company

            serializer = JobInfoSerializer(data=mutable_data)

            if serializer.is_valid():
                # To send an email to job seekers who have matching skills given in job application
                queries = Q()
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
                            message=f"Hi {usernameList[i]}, \n We have found a new job posting matching your skillset. Please apply. \
                            \n Job title: {mutable_data['title']} posted by {request.user.username} a few moments ago",
                            from_email=EMAIL_HOST_USER,
                            recipient_list=[emailList[i]],
                            fail_silently=False)
                    print(f'Email sent to :: {usernameList[i]}')

                # Save the job creation information to the DB
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
            self.permission_classes = [IsRecruiter|IsJobSeeker]

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

        print(f"job application received: {mutable_data}")

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
        print(serializer.errors)
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
    
#Cosine similarity and TF-IDF Based job recommendation
class JobRecommendationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsJobSeeker]
    def list(self, request):
        try:
            # Get the current job seeker
            jobseeker = JobSeeker.objects.get(user=request.user)
            jobseeker_skills = jobseeker.skills  # Example: "Python, Django, Machine Learning"
            
            print(f'Job seeker skills: {jobseeker_skills}')

            # Get all jobs from the database
            jobs = JobInfo.objects.all()
            job_descriptions = [job.skills_preferred for job in jobs]  # Extract skills from job listings
            
            # Add jobseeker's skills to the list for similarity calculation
            job_descriptions.append(jobseeker_skills)  

            # Compute TF-IDF matrix
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(job_descriptions)
            
            # Compute cosine similarity (last row is the jobseeker's skills)
            similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]

            # Sort jobs by similarity score (higher means better match)
            job_scores = sorted(zip(jobs, similarity_scores), key=lambda x: x[1], reverse=True)

            print(f"Job scores: {job_scores}")

            # Select top 10 matching jobs
            top_jobs = [{"title": job.title,
                         "id": job.id,
                         "experience": job.experience,
                         "company": job.company,
                         "industry": job.industry,
                         "location": job.location,
                         "job_description": job.job_description,
                         "skills_preferred":job.skills_preferred,
                         "education_preferred": job.education_preferred,
                         "salary": job.salary,
                         "created_ts": job.created_ts,
                         "similarity_score": round(score, 2)} for job, score in job_scores[:5]]

            print(f"Top jobs: {top_jobs}")

            return Response({"recommended_jobs": top_jobs}, status=200)

        except Exception as e:
            print(f"Error : {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Display the list of jobs applied by the jobseeker
class AppliedJobs(viewsets.ModelViewSet):
    permission_classes = [IsJobSeeker]

    def list(self, request):
        jobseeker = JobSeeker.objects.get(user_id=request.user.id)
        job_applications = JobApplication.objects.filter(jobseeker_id=jobseeker.id)
        jobinfo_ids = job_applications.values_list('jobinfo_id', flat=True)
        jobinfo = JobInfo.objects.filter(id__in=jobinfo_ids)
        
        # Serialize job data along with applied_ts (created_ts from JobApplication)
        serialized_jobs = []
        for job in jobinfo:
            # Find the associated JobApplication entry for the job
            job_application = job_applications.filter(jobinfo_id=job.id).first()
            if job_application:
                # Add created_ts as applied_ts to the job data
                job_data = {
                    **JobInfoSerializer(job).data,
                    'applied_ts': job_application.created_ts
                }
                serialized_jobs.append(job_data)

        print(f"Applied job info: {job_data}")
        return Response(serialized_jobs)

#Display the list of jobs posted by the recruiter
#Along with the recruiters who has posted for it
class CreatedJobByRecruiters(viewsets.ModelViewSet):
    permission_classes = [IsRecruiter]

    def list(self, request):
        try:
            # Fetch the recruiter ID based on the logged-in user
            recruiter_id = Recruiter.objects.get(user_id=request.user.id).id
            
            # Get all the jobs created by the recruiter
            jobList = JobInfo.objects.filter(recruiter_id=recruiter_id)
            
            # Fetch job applications related to each job along with jobseeker details
            job_list_with_jobseekers = []
            for job in jobList:
                # Get all applications for this job
                applications = JobApplication.objects.filter(jobinfo_id=job.id)

                # Fetch job seeker details for each application
                jobseekers = []
                for application in applications:
                    jobseeker = JobSeeker.objects.get(id=application.jobseeker_id)
                    jobseeker_data = JobSeekerSerializer(jobseeker).data
                    # Adding the user email and name
                    custom_user = CustomUser.objects.get(id=jobseeker.user_id)
                    jobseeker_data['name'] = custom_user.username
                    jobseeker_data['email'] = custom_user.email

                    # print(f"Jobseeker Data: {jobseeker_data}")
                    if jobseeker_data['photo']:
                        jobseeker_data['photo'] = request.build_absolute_uri(jobseeker.photo.url)
                    else:
                        jobseeker_data['photo'] = None  # Handle case where no photo exists

                    jobseekers.append(jobseeker_data)

                # Serialize the job details
                job_data = JobInfoSerializer(job).data
                job_data['jobseekers'] = jobseekers  # Add job seeker details to the job data
                
                job_list_with_jobseekers.append(job_data)

                # print(job_data)
            # Return the jobs with their respective job seekers
            return Response(job_list_with_jobseekers, status=status.HTTP_200_OK)
        
        except Recruiter.DoesNotExist:
            return Response({"message": "No such recruiter is present."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error: {e}")
            return Response({"message": "An error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
# Job filters
class JobFilters(viewsets.ModelViewSet):
    def list(self, request):
        try:
            job_types = JobInfo.objects.values_list('job_type', flat=True).distinct()
            locations = JobInfo.objects.values_list('location', flat=True).distinct()
            industries = JobInfo.objects.values_list('industry', flat=True).distinct()
            
            print(f"Industries: {industries}")

            salary_min = JobInfo.objects.order_by('salary').values_list('salary', flat=True).first() or 0
            salary_max = JobInfo.objects.order_by('-salary').values_list('salary', flat=True).first() or 100000

            salary_ranges = [
                {"label": "0 - 3 LPA", "min": 0, "max": 300000},
                {"label": "3 - 6 LPA", "min": 300000, "max": 600000},
                {"label": "6 - 10 LPA", "min": 600000, "max": 1000000},
                {"label": "10+ LPA", "min": 1000000, "max": salary_max}
            ]

            return Response({
                "jobTypes": list(job_types),
                "locations": list(locations),
                "industries": list(industries),
                "salaryRanges": salary_ranges
            })
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

