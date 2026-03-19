from rest_framework import status, permissions
from rest_framework.response import Response
import jwt
from rest_framework_simplejwt.views import TokenRefreshView
from jwt.exceptions import InvalidTokenError
from accounts.serializers.refresh_token import RefreshTokenSerializer


class CustomRefreshTokenAPIView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        # Use the RefreshTokenSerializer for validation
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            # Call the parent class to get the new access token
            response = super().post(request, *args, **kwargs)
            access_token = response.data.get("access")

            # Update the response with the new access token
            response.data["access"] = access_token

            return response

        except (InvalidTokenError, jwt.ExpiredSignatureError):
            return Response(
                {"error": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception:
            return Response(
                {"error": "Token refresh failed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
