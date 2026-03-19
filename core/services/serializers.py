from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.contrib.auth import authenticate
from modeltranslation.translator import translator
from django.conf import settings


class EmptySerializer(serializers.Serializer):
    pass


class DeleteSerializer(serializers.Serializer):
    """
    Serializer for deletion with password confirmation
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        help_text=_("Password confirmation required to delete object"),
    )
    message = serializers.CharField(read_only=True)

    def validate_password(self, value):
        """
        Validate that the provided password matches the current user's password
        """
        request = self.context.get("request")

        if not request or not request.user:
            raise serializers.ValidationError(_("Authentication required"))

        # Authenticate the user with provided password
        user = authenticate(email=request.user.email, password=value)

        if user is None:
            raise serializers.ValidationError(_("Invalid password. Please try again."))

        return value


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        # Extract fields and exclude arguments
        fields = kwargs.pop("fields", None)
        exclude = kwargs.pop("exclude", None)
        super().__init__(*args, **kwargs)

        if fields is not None and exclude is not None:
            raise ValueError("Cannot specify both 'fields' and 'exclude' arguments")

        if fields is not None:
            # Include only specified fields
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name, None)

        elif exclude is not None:
            # Exclude specified fields
            excluded = set(exclude)
            for field_name in excluded:
                self.fields.pop(field_name, None)


class LocationSerializer(serializers.Serializer):
    latitude = serializers.CharField()
    longitude = serializers.CharField()

    def validate_latitude(self, value):
        """
        Convert string to decimal and truncate to 8 decimal places
        """
        try:
            # Convert string to float, then truncate to 8 decimals
            decimal_value = round(float(value), 8)

            # Validate range
            if not (-90.0 <= decimal_value <= 90.0):
                raise serializers.ValidationError(
                    _("Latitude must be between -90 and 90 degrees")
                )

            return Decimal(str(decimal_value))

        except (ValueError, TypeError):
            raise serializers.ValidationError(_("Invalid latitude format"))

    def validate_longitude(self, value):
        """
        Convert string to decimal and truncate to 8 decimal places
        """
        try:
            # Convert string to float, then truncate to 8 decimals
            decimal_value = round(float(value), 8)

            # Validate range
            if not (-180.0 <= decimal_value <= 180.0):
                raise serializers.ValidationError(
                    _("Longitude must be between -180 and 180 degrees")
                )

            return Decimal(str(decimal_value))

        except (ValueError, TypeError):
            raise serializers.ValidationError(_("Invalid longitude format"))


class TranslatedFieldsSerializerMixin:
    """
    Mixin to automatically handle translated fields in serializers.
    Supports both simple format (auto-populate) and explicit language fields.
    """

    def get_translated_fields(self):
        """Get list of translated field names from the model"""
        if not hasattr(self.Meta, "model"):
            return []

        try:
            translation_opts = translator.get_options_for_model(self.Meta.model)
            if translation_opts:
                return translation_opts.fields
        except:
            pass
        return []

    def get_available_languages_for_field(self, field_name):
        """Get list of language codes that actually exist in the database for this field"""
        if not hasattr(self.Meta, "model"):
            return []

        model_field_names = {f.name for f in self.Meta.model._meta.get_fields()}
        languages = [lang[0].split("-")[0] for lang in settings.LANGUAGES]

        # Only return languages where the field actually exists in database
        available_languages = []
        for lang_code in languages:
            lang_field_name = f"{field_name}_{lang_code}"
            if lang_field_name in model_field_names:
                available_languages.append(lang_code)

        return available_languages

    def get_fields(self):
        """Dynamically add language-specific fields"""
        fields = super().get_fields()
        translated_fields = self.get_translated_fields()

        # Determine if this is a write operation
        request = self.context.get("request")
        is_write_operation = request and request.method in ["POST", "PUT", "PATCH"]

        # Add language-specific fields
        for field_name in translated_fields:
            if field_name in fields:
                base_field = fields[field_name]

                # Check if the base field is in read_only_fields
                is_read_only = field_name in getattr(self.Meta, "read_only_fields", [])

                if is_read_only:
                    # If field is read-only, don't add language-specific write fields
                    continue

                if is_write_operation:
                    # For write operations: make base field write-only
                    base_field.write_only = True
                    base_field.required = False
                else:
                    # For read operations: keep base field visible (shows user's language)
                    # modeltranslation automatically returns the correct language
                    pass

                # Get only languages that exist in database
                available_languages = self.get_available_languages_for_field(field_name)

                # Add language-specific fields only for available languages
                for lang_code in available_languages:
                    lang_field_name = f"{field_name}_{lang_code}"

                    # Create a new field instance
                    field_class = base_field.__class__

                    # Basic field kwargs
                    field_kwargs = {
                        "required": False,
                    }

                    if is_write_operation:
                        # Writable for POST/PUT/PATCH
                        field_kwargs["read_only"] = False
                    else:
                        # Read-only for GET (just display)
                        field_kwargs["read_only"] = True

                    # Add optional kwargs if applicable
                    if hasattr(base_field, "allow_blank"):
                        field_kwargs["allow_blank"] = True
                    if hasattr(base_field, "allow_null"):
                        field_kwargs["allow_null"] = True

                    lang_field = field_class(**field_kwargs)
                    fields[lang_field_name] = lang_field

        return fields

    def validate(self, data):
        """Handle translation logic: copy base field to all languages if not provided"""
        data = super().validate(data)
        translated_fields = self.get_translated_fields()
        default_lang = settings.LANGUAGE_CODE.split("-")[0]

        for field_name in translated_fields:
            # Skip if field is read-only
            if field_name in getattr(self.Meta, "read_only_fields", []):
                continue

            # Get only languages that actually exist in database
            available_languages = self.get_available_languages_for_field(field_name)

            # If base field is provided (simple format: notes="string")
            if field_name in data:
                base_value = data.pop(field_name)

                # DEFAULT BEHAVIOR: Save to default language (notes_en) if it exists
                default_field_name = f"{field_name}_{default_lang}"
                if default_lang in available_languages:
                    if default_field_name not in data or not data[default_field_name]:
                        data[default_field_name] = base_value

                # Copy to other available languages ONLY if they're not provided
                for lang_code in available_languages:
                    if lang_code == default_lang:
                        continue  # Skip default, already handled

                    lang_field_name = f"{field_name}_{lang_code}"
                    if lang_field_name not in data or not data[lang_field_name]:
                        data[lang_field_name] = base_value

            # Ensure at least the default language is provided (only if field is required)
            if default_lang in available_languages:
                default_field_name = f"{field_name}_{default_lang}"

                # Check if any language variant exists
                has_value = any(
                    data.get(f"{field_name}_{lang}") for lang in available_languages
                )

                if not has_value:
                    # Check if the original model field is required
                    try:
                        model_field = self.Meta.model._meta.get_field(field_name)
                        # Only raise error if field is not blank and not null
                        if not model_field.blank and not model_field.null:
                            raise serializers.ValidationError(
                                {default_field_name: _("This field is required")}
                            )
                    except Exception:
                        pass

        return data


class TranslatedDynamicFieldsModelSerializer(
    TranslatedFieldsSerializerMixin, DynamicFieldsModelSerializer
):
    """
    Combines translation handling with dynamic fields.
    Use this as your base serializer for models with translations.
    """

    pass
