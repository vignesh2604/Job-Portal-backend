from rest_framework import serializers
from .models import CustomUser, JobSeeker, Recruiter
# from django.contrib.auth.validators import UnicodeUsernameValidatorzz

class CustomUserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(max_length=20, write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'confirm_password', 
                  'is_jobseeker', 'is_recruiter']
        write_only_fields = ['is_jobseeker', 'is_recruiter']
        extra_kwargs = {
            'password': {'write_only': True},
            # 'username': {
            #     'validators': [UnicodeUsernameValidator()],
            # }
        }

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords does not match..")

        if CustomUser.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Username already taken..")
        if CustomUser.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already exists..")
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        # usertype = validated_data.pop('userType')

        # print(f"user type:: {usertype}")
        print(f'Data before storing it in dB', validated_data)
        user = CustomUser.objects.create_user(**validated_data)

        return user

class JobSeekerSerializer(serializers.ModelSerializer):

    dupuser = serializers.CharField(max_length=50, read_only=True)
    resume = serializers.FileField(required=False, allow_null=True, allow_empty_file=True)
    photo = serializers.ImageField(required=False, allow_null=True, allow_empty_file=True)

    class Meta:
        model = JobSeeker
        fields = "__all__"
        read_only_fields = ['user','created_ts', 'updated_ts']
    
    def validate(self, data):
        dupuser = self.initial_data.get('dupuser', None)
        if CustomUser.objects.filter(username=dupuser).exists():
            if CustomUser.objects.get(username = dupuser).is_jobseeker:
                return data
            raise serializers.ValidationError("User is not a jobseeker..")
        raise serializers.ValidationError("User doesn't exist..")

    def create(self, validated_data):
        username = self.initial_data.get('dupuser', None)

        validated_data['user_id'] = CustomUser.objects.get(username=username).id

        job_seeker = JobSeeker.objects.create(**validated_data)

        return job_seeker

    def update(self, instance, validated_data):

        for attr, value in validated_data.items():
            if value:
                setattr(instance, attr, value)
        
        instance.save()

        return instance
    
class RecruiterSerializer(serializers.ModelSerializer):
    dupuser = serializers.CharField(max_length=50, read_only=True)
    resume = serializers.FileField(required=False, allow_null=True, allow_empty_file=True)
    photo = serializers.ImageField(required=False, allow_null=True, allow_empty_file=True)

    class Meta:
        model = Recruiter
        fields = "__all__"
        read_only_fields = ['user','created_ts', 'updated_ts']
    
    def validate(self, data):
        dupuser = self.initial_data.get('dupuser', None)
        print(dupuser)
        if CustomUser.objects.filter(username=dupuser).exists():
            if CustomUser.objects.get(username=dupuser).is_recruiter:
                return data
            raise serializers.ValidationError("User is not a recruiter..")
        raise serializers.ValidationError("User doesn't exist..")

    def create(self, validated_data):
        username = self.initial_data.get('dupuser', None)

        validated_data['user_id'] = CustomUser.objects.get(username=username).id

        recruiter = Recruiter.objects.create(**validated_data)

        return recruiter   
    
    def update(self, instance, validated_data):

        for attr, value in validated_data.items():
            if value:
                setattr(instance, attr, value)
        
        instance.save()

        return instance