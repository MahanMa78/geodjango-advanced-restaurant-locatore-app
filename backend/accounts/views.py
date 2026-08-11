import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, OTPCode
from .serializers import SendOTPSerializer, VerifyOTPSerializer, UserProfileSerializer


class SendOTPView(APIView):
    """Sending or generating an OTP code for a phone number"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            
            # Generating a random 5-digit code
            code = str(random.randint(10000, 99999))
            
            # Deleting old codes for this phone number and saving the new code
            OTPCode.objects.filter(phone_number=phone_number).delete()
            OTPCode.objects.create(phone_number=phone_number, code=code)

            # 💡 In the development environment, we display the code and the response within the terminal.
            print(f"🔑 [DEV OTP] Code for {phone_number} is: {code}")

            return Response({
                "message": "OTP code sent successfully.",
                "dev_code": code  # For easier testing
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    """Verify OTP code and retrieve JWT tokens (Auto-registration or login)"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            code = serializer.validated_data['code']

            # Verifying the OTP Code
            otp = OTPCode.objects.filter(phone_number=phone_number, code=code).first()
            if not otp or not otp.is_valid():
                return Response({"error": "OTP code is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)

            # If the user exists, log them in; otherwise, create a new user automatically
            user, created = User.objects.get_or_create(phone_number=phone_number)

            # Remove used code
            otp.delete()

            # Issuing JWTs
            refresh = RefreshToken.for_user(user)

            return Response({
                "message": "Login successful.",
                "is_new_user": created,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "user": UserProfileSerializer(user).data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """View and edit the current user's profile"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)