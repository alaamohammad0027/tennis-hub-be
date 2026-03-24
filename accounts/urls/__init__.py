from django.urls import include, path

urlpatterns = [
    path("", include("accounts.urls.auth")),
    path("", include("accounts.urls.register")),
    path("", include("accounts.urls.profiles")),
]
