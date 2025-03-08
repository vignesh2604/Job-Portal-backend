from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, status
from rest_framework.views import APIView
# from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from .permission import IsJobSeeker, IsRecruiter
from .models import CustomUser, JobSeeker, Recruiter
from api.models import JobInfo, JobApplication
from.serializers import CustomUserSerializer, JobSeekerSerializer, RecruiterSerializer
from django.core.mail import send_mail
from jobbackend.settings import EMAIL_HOST_USER
# Create your views here.

class CustomUserViewSet(viewsets.ViewSet):

    serializer_class = CustomUserSerializer

    def list(self, request):
        queryset = CustomUser.objects.all()
        serializer = CustomUserSerializer(queryset, many=True) 
        print(serializer.data) 
        return Response(serializer.data)

    def create(self, request):
        print(request.data)
        serializer = CustomUserSerializer(data=request.data)

        if serializer.is_valid():
            send_mail(subject="User Registration at Job Portal",
                message=f"Hi {request.data.get('username')}, \
                \n Welcome to the Job portal application \
                \n Please go ahead and complete your profile to let us find the best jobs for you..",
                from_email=EMAIL_HOST_USER,
                recipient_list=[request.data.get('email')],
                fail_silently=False)
            print("Email sent..")
            serializer.save()
            return Response({
                'message': 'User data submitted successfully',
                'user': request.data
            },
                status = status.HTTP_201_CREATED    
            )
        else:
            # Return errors if validation fails
            print(serializer.errors)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

class JobSeekerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsJobSeeker, IsAuthenticated]
    serializer_class =  JobSeekerSerializer
    parser_classes = (MultiPartParser, FormParser)

    def list(self, request):
        # Retrive the current user Details
        queryset = JobSeeker.objects.filter(user_id=request.user.id)
        serializer = JobSeekerSerializer(queryset, many=True)
        print(f"user Data: {serializer.data}")
        if serializer.data:
            updated_data = serializer.data[0]
            updated_data.pop('id')
            updated_data.pop('created_ts')
            updated_data.pop('updated_ts')
            updated_data.pop('user')
            if updated_data.get('photo'):
                updated_data['photo'] = request.build_absolute_uri(updated_data['photo'])
            if updated_data.get('resume'):
                updated_data['resume'] = request.build_absolute_uri(updated_data['resume'])
            print(f" Response: {updated_data}")
            return Response(updated_data)
        else:
            updated_data = {}
            print(f" Response: {updated_data}")
            return Response(updated_data, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        
        dupuser = request.user.username
        mutable_data = request.data.copy()
        mutable_data['dupuser'] = dupuser
        mutable_data['company'] = mutable_data['company'].capitalize()
        mutable_data['location'] = mutable_data['location'].capitalize()

        # Explicitly assign files to serializer validated data
        if 'photo' in request.FILES:
            mutable_data['photo'] = request.FILES['photo']
        if 'resume' in request.FILES:
            mutable_data['resume'] = request.FILES['resume']
        
        serializer = JobSeekerSerializer(data=mutable_data)
        
        if serializer.is_valid():
            serializer.save()
            print("Profile saved...")
            return Response({
                'message': 'Profile created successfully',
            },
                status = status.HTTP_201_CREATED    
            )
        else:
            # Return errors if validation fails
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, pk=None):
        print(request.user)
        try:
            jobseeker = JobSeeker.objects.get(user=request.user)
        except:
            return Response({"message: No such jobseeker is present.."})

        username = CustomUser.objects.get(pk=jobseeker.user_id).username

        print(f"username: {username}")
        print(f"request user name: {request.user}")
        print(f"user id in request given: {request.user.id}")

        mutable_data = request.data.copy()
        mutable_data['dupuser'] = username
        mutable_data['company'] = mutable_data['company'].capitalize()
        mutable_data['location'] = mutable_data['location'].capitalize()
        # Explicitly assign files to serializer validated data
        if 'photo' in request.FILES:
            mutable_data['photo'] = request.FILES['photo']
        if 'resume' in request.FILES:
            mutable_data['resume'] = request.FILES['resume']

        # request.data['dupuser'] = username

        if jobseeker:
            serializer = JobSeekerSerializer(jobseeker, data=mutable_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "messgae" : "User data updated successfully..",
                }, status = status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RecruiterViewSet(viewsets.ModelViewSet):

    permission_classes = [IsRecruiter, IsAuthenticated]
    serializer_class = RecruiterSerializer
    parser_classes = (MultiPartParser, FormParser)

    def list(self, request):
        # Retrieve the current user details
        queryset = Recruiter.objects.filter(user_id=request.user.id)
        serializer = RecruiterSerializer(queryset, many=True)
        if serializer.data:
            print(f"Current recruiter details: {serializer.data[0]}")
            updated_data = serializer.data[0]
            updated_data.pop('id')
            updated_data.pop('created_ts')
            updated_data.pop('updated_ts')
            updated_data.pop('user')
            if updated_data.get('photo'):
                updated_data['photo'] = request.build_absolute_uri(updated_data['photo'])
            if updated_data.get('resume'):
                updated_data['resume'] = request.build_absolute_uri(updated_data['resume'])
            print(updated_data)
            return Response(updated_data)
        else:
            updated_data = {}
            print(f" Response: {updated_data}")
            return Response(updated_data, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        dupuser = request.user.username
        mutable_data = request.data.copy()
        mutable_data['dupuser'] = dupuser
        mutable_data['company'] = mutable_data['company'].capitalize()
        mutable_data['location'] = mutable_data['location'].capitalize()

        print(f'Req data: {mutable_data}')
        if 'resume' in request.FILES:
            mutable_data['resume'] = request.FILES['resume']
        if 'photo' in request.FILES:
            mutable_data['photo'] = request.FILES['photo']

        serializer = RecruiterSerializer(data=mutable_data)
        if serializer.is_valid():
            print("Profile saved...")
            serializer.save()
            return Response({
                'message': 'Recruiter profile created successfully',
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            recruiter = Recruiter.objects.get(user=request.user)
            print(f"Recruiter data: {recruiter}")
        except Recruiter.DoesNotExist:
            return Response({"message": "No such recruiter is present."}, status=status.HTTP_400_BAD_REQUEST)

        username = CustomUser.objects.get(pk=recruiter.user_id).username
        print(f"username: {username}")
        print(f"Req. data in Update: {request.data}")
        
        mutable_data = request.data.copy()
        mutable_data['dupuser'] = username
        mutable_data['company'] = mutable_data['company'].capitalize()
        mutable_data['location'] = mutable_data['location'].capitalize()

        if recruiter:
            # Explicitly assign files to serializer validated data
            if 'photo' in request.FILES:
                mutable_data['photo'] = request.FILES['photo']
            if 'resume' in request.FILES:
                mutable_data['resume'] = request.FILES['resume']
            print(f"Proceeding with updating the recruiter profile: {mutable_data}")
            serializer = RecruiterSerializer(recruiter, data=mutable_data, partial=True)  # To accept partial updates

            if serializer.is_valid():
                serializer.save()
                # Exclude binary data fields (photo, resume)
                updated_data = serializer.data
                updated_data.pop('photo', None)
                updated_data.pop('resume', None)

                return Response({
                    "message": "User data updated successfully.",
                }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
#Logout view
class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data['refresh_token']
            print(refresh_token)
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({
                "message": "User logged out successfully..",
            }, status=status.HTTP_205_RESET_CONTENT)
        
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class fetchUserDetails(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            username = request.user.username
            email = request.user.email
            user_id = request.user.id
            usertype = 'jobseeker' if request.user.is_jobseeker else 'recruiter'
            photo = None
            if usertype == 'jobseeker' and JobSeeker.objects.filter(user_id=user_id).exists():
                photo = JobSeeker.objects.get(user_id=user_id).photo

            if usertype == 'recruiter' and Recruiter.objects.filter(user_id=user_id).exists():
                photo = Recruiter.objects.get(user_id=user_id).photo
            
            if photo:
                print(f"photo: {photo.url}")
                photo_uri = request.build_absolute_uri(photo.url)
            else:
                photo_uri = None   
            userDetails = {
                "username" : username,
                "email": email,
                "user_id": user_id,
                "usertype": usertype,
                "photo": photo_uri,
            }
            print(f"userDetails: {userDetails}")
            return Response(userDetails)
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)

# Display list of job seeker profiles to all the users of the application 
class RetrieveJobSeekersList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            queryset = JobSeeker.objects.all()
            print(f"Fetching all job seekers: {queryset}")
            serializer = JobSeekerSerializer(queryset, many=True)
            mutable_data = serializer.data
            # Get user email, name from CustomUser table
            for i, job_seeker in enumerate(queryset):
                # Building the absolute URL for the photo field
                if job_seeker.photo:
                    mutable_data[i]['photo'] = request.build_absolute_uri(job_seeker.photo.url)
                else:
                    mutable_data[i]['photo'] = None  # Handle case where no photo exists
                
                # Adding user-related fields (email, username)
                mutable_data[i]['username'] = job_seeker.user.username
                mutable_data[i]['email'] = job_seeker.user.email
                print(f"Job Seeker {i+1}: {mutable_data[i]}")
                
            return Response({
                "message": "List of jobseeker details fetched successfully",
                "data":mutable_data
                }, status = status.HTTP_200_OK)
        except Exception as e:
            print(f"Error info: {e}")
            return Response({
            "message": "Cannot retrieve data at this time.."
            }, status = status.HTTP_400_BAD_REQUEST)


# Send notification to job seeker to be notified by recruiters
class NotifyJobSeekers(APIView):
    permission_classes = [IsRecruiter]
    def post(self, request):
        """
        Send email notification to job seekers when notified by a recruiter.
        """
        job_seeker_id = request.data.get('job_seeker_id')
        recruiter = request.user

        try:
            job_seeker = JobSeeker.objects.get(id=job_seeker_id)
            job_seeker_user = CustomUser.objects.get(id=job_seeker.user_id)
        except JobSeeker.DoesNotExist:
            return Response({"error": "Job seeker not found."}, status=status.HTTP_404_NOT_FOUND)
        except CustomUser.DoesNotExist:
            return Response({"error": "User associated with job seeker not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Sending Email Notification
        subject = "Job Opportunity Notification"
        message = f"Hi {job_seeker_user.username},\n\nYou have been notified by {recruiter.username} regarding a potential job opportunity.\n\nPlease check your job portal account for further details.\n\nBest Regards,\nJob Portal Team"
        recipient_list = [job_seeker_user.email]
        
        try:
            send_mail(subject, message, EMAIL_HOST_USER, recipient_list, fail_silently=False)
            return Response({"message": "Notification email sent successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to send email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
