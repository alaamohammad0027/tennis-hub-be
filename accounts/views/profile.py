from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from accounts.serializers import ProfileSerializer


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    """
    GET  - Retrieve the authenticated user's profile
    PUT/PATCH - Update the authenticated user's profile (including photo)
    """

    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    swagger_tags = ["Profile"]

    def get_object(self):
        return self.request.user
