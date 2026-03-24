from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models.choices import UserType
from accounts.serializers import ProfileSerializer
from accounts.serializers.me import ME_UPDATE_MAP, ME_PROFILE_READ_MAP
from accounts.views.schema import me_schema


@me_schema
class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_profile_data(self, user, ctx):
        """Returns serialized profile dict (ME_FIELDS preset) or None."""
        entry = ME_PROFILE_READ_MAP.get(user.user_type)
        if not entry:
            return None
        Model, Serializer = entry
        instance = Model.objects.filter(user=user, is_active=True).first()
        if not instance:
            return None
        # ME_FIELDS = all admin fields minus `user` (user already at top level)
        return Serializer(instance, fields=Serializer.ME_FIELDS, context=ctx).data

    def _build_response(self, user, ctx):
        user_data = ProfileSerializer(user, context=ctx).data
        profile_data = self._get_profile_data(user, ctx)
        return Response({**user_data, "profile": profile_data})

    def get(self, request):
        return self._build_response(request.user, {"request": request})

    def patch(self, request):
        user = request.user
        ctx = {"request": request}

        serializer_class = ME_UPDATE_MAP.get(user.user_type)
        if not serializer_class:
            return Response(
                {"detail": "Profile update not available for this user type."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = serializer_class(
            user, data=request.data, partial=True, context=ctx
        )
        serializer.is_valid(raise_exception=True)
        serializer.update(user, serializer.validated_data)

        # Return fresh merged response
        user.refresh_from_db()
        return self._build_response(user, ctx)
