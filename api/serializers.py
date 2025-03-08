from .models import JobInfo, JobApplication
from users.models import Recruiter, JobSeeker, CustomUser
from rest_framework import serializers
# Send email using django
from django.core.mail import send_mail
from jobbackend.settings import EMAIL_HOST_USER

# Utility function to send email
def _sendEmail(sender, receiver, jobdetails):
    jobname, jobseekerName, jobseekerEmail = jobdetails['jobname'], jobdetails['jobseekerName'], jobdetails['jobseekerEmail']
    send_mail(subject=f"New applicant for the job: {jobname}",
              message=f"Hi, \n A new applicant {jobseekerName} with contact {jobseekerEmail} \
              has applied for the job {jobname} \
              you've posted..",
              from_email=sender,
              recipient_list=[receiver],
              fail_silently=False)

class JobInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobInfo
        fields = "__all__"
        read_only_fields = ['recruiter']
    
    def create(self, validated_data):
        recruiter = self.initial_data.get('recruiter', None)
        print(f'recruiter: {recruiter}')
        validated_data['recruiter'] = Recruiter.objects.get(id=recruiter)

        job = JobInfo.objects.create(**validated_data)
        
        return job


class JobApplicationSerializer(serializers.ModelSerializer):
    
    resume = serializers.FileField(required=False, allow_null=True, allow_empty_file=True)

    class Meta:
        model = JobApplication
        fields = "__all__"
        read_only_fields = ['jobseeker', 'recruiter_id']
    
    def create(self, validated_data):
        jobseeker = self.initial_data.get('jobseeker', None)
        jobinfo_id = self.initial_data.get('jobinfo', None)
        print(f'jobseeker user-id: {jobseeker.id}')
        print(f'jobinfo in serialzier: {jobinfo_id}')
        validated_data['jobseeker'] = JobSeeker.objects.get(user_id=jobseeker.id)
        # Add recruiter instance as well
        recruiter_id_from_job_info = JobInfo.objects.get(id=jobinfo_id).recruiter_id
        validated_data['recruiter_id'] = Recruiter.objects.get(id=recruiter_id_from_job_info)
        recruiter_user_id = Recruiter.objects.get(id=recruiter_id_from_job_info).user_id
        print(f"Recruiter user id: {recruiter_user_id}")
        recruiter_email = CustomUser.objects.get(id=recruiter_user_id).email
        jobdetails = {}
        jobdetails['jobname'] = JobInfo.objects.get(id=jobinfo_id).title
        jobdetails['jobseekerName'] = jobseeker.username
        jobdetails['jobseekerEmail'] = jobseeker.email
        _sendEmail(sender=EMAIL_HOST_USER, receiver=recruiter_email, jobdetails=jobdetails)
        print(f"Email alert sent to {recruiter_email}")
        applied_job = JobApplication.objects.create(**validated_data)

        return applied_job

class JobSeekerSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobSeeker
        fields = "__all__"
        