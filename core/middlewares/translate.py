from django.conf import settings
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication


class LanguageMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()
        # Get supported languages from settings
        self.supported_languages = [lang for lang, _ in settings.LANGUAGES]

    def _normalize_language_code(self, lang_code):
        """Normalize language code to supported format"""
        if not lang_code:
            return None

        lang_code = lang_code.lower().strip()

        # Direct match
        if lang_code in self.supported_languages:
            return lang_code

        # Try just the primary language part (e.g., 'ar-SA' -> 'ar')
        primary_lang = lang_code.split("-")[0]
        if primary_lang in self.supported_languages:
            return primary_lang

        return None

    def __call__(self, request):
        """
        Set the language for the current request based on priority:
        1. Authenticated user's language preference (including JWT auth)
        2. X-Language header (from CORS_ALLOW_HEADERS)
        3. Default language
        """
        # Default language
        lang = getattr(settings, "DEFAULT_USER_LANGUAGE", "en")
        selected_method = "default"

        # PRIORITY: If no user language, check X-Language header
        if selected_method == "default":
            header_lang = request.META.get("HTTP_X_LANGUAGE")
            normalized_header = self._normalize_language_code(header_lang)
            if normalized_header:
                lang = normalized_header
                selected_method = "x_language_header"

        # Activate the language for the current thread/request
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        # Get the response
        response = self.get_response(request)

        # Set Content-Language header so client knows what language was used
        response["Content-Language"] = lang

        # Deactivate the language after the response is generated
        translation.deactivate()

        return response
