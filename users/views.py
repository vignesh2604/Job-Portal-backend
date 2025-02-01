from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, status
from rest_framework.views import APIView
# from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from .permission import IsJobSeeker, IsRecruiter
from .models import CustomUser, JobSeeker, Recruiter
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

        serializer = JobSeekerSerializer(data=mutable_data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile created successfully',
                'user': request.data
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

        # request.data['dupuser'] = username

        if jobseeker:
            serializer = JobSeekerSerializer(jobseeker, data=mutable_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "messgae" : "User data updated successfully..",
                    "user": request.data
                }, status = status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RecruiterViewSet(viewsets.ModelViewSet):

    permission_classes = [IsRecruiter, IsAuthenticated]
    serializer_class = RecruiterSerializer
    
    def list(self, request):
        # Retrive the current user Details
        queryset = Recruiter.objects.filter(user_id=request.user.id)
        serializer = RecruiterSerializer(queryset, many=True)
        print(f"Current recruiter details: {serializer.data[0]}")
        updated_data = serializer.data[0]
        updated_data.pop('id')
        updated_data.pop('created_ts')
        updated_data.pop('updated_ts')
        updated_data.pop('user')
        return Response(updated_data)

    def create(self, request):
        dupuser = request.user.username
        mutable_data = request.data.copy()
        mutable_data['dupuser'] = dupuser
        print(f'In views: {dupuser}')
        serializer = RecruiterSerializer(data=mutable_data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Recruiter profile created successfully',
                'user': request.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            recruiter = Recruiter.objects.get(user=request.user)
            print(recruiter)
        except:
            return Response({"message: No such recruiter is present.."})

        username = CustomUser.objects.get(pk=recruiter.user_id).username

        print(f"username: {username}")

        mutable_data = request.data.copy()
        mutable_data['dupuser'] = username

        # request.data['dupuser'] = username

        if recruiter:
            print("test")
            serializer = RecruiterSerializer(recruiter, data=mutable_data, partial=True) # To accept partial field updates on data in the table
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "messgae" : "User data updated successfully..",
                    "user": request.data
                }, status = status.HTTP_201_CREATED)
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
            userDetails = {
                "username" : username,
                "email": email,
                "user_id": user_id,
                "usertype": usertype,
            }
            print(f"userDetails: {userDetails}")
            return Response(userDetails)
        except:
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
            for i, id in enumerate(queryset):
                print(f"Username: {id.user} -> Email: {id.user.email}")
                print(f"Here :: {mutable_data[i]}")
                mutable_data[i]['username'] = id.user.username
                mutable_data[i]['email'] = id.user.email
                
            return Response({
                "message": "List of jobseeker details fetched successfully",
                "jobseekers":mutable_data
                }, status = status.HTTP_200_OK)
        except Exception as e:
            print(f"Error info: {e}")
            return Response({
            "message": "Cannot retrieve data at this time.."
            }, status = status.HTTP_400_BAD_REQUEST)
