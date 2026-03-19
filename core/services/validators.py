from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# FOR SERIALIZERS (API)
def validate_file(value, file_type="image", max_size_mb=10):
    """
    Flexible file validation for serializers
    Args:
        value: The uploaded file
        file_type: 'image' or 'file' (default: 'image')
        max_size_mb: Maximum file size in MB (default: 10)
    """
    if not value:
        return value

    # Define allowed file types
    if file_type == "image":
        allowed_types = ["jpg", "jpeg", "png", "webp"]
        error_message = _("Only JPG, PNG, WebP images allowed.")
    elif file_type == "file":
        allowed_types = ["jpg", "jpeg", "png", "webp", "pdf"]
        error_message = _("Only JPG, PNG, WebP, PDF files allowed.")
    else:
        # Custom file types
        allowed_types = file_type if isinstance(file_type, list) else [file_type]
        error_message = _("Only {extensions} files allowed.").format(
            extensions=", ".join(allowed_types).upper()
        )

    # Check file type
    filename = getattr(value, "name", "").lower()
    if filename and not any(filename.endswith(f".{ext}") for ext in allowed_types):
        raise serializers.ValidationError(error_message)

    # Check file size
    max_size = max_size_mb * 1024 * 1024  # Convert MB to bytes
    if value.size > max_size:
        raise serializers.ValidationError(
            _("File must be under {max_size}MB.").format(max_size=max_size_mb)
        )

    return value


# FOR MODELS (Django Admin)
def validate_model_file(value, file_type="image", max_size_mb=10):
    """
    Flexible file validation for model fields

    Args:
        value: The uploaded file
        file_type: 'image' or 'file' (default: 'image')
        max_size_mb: Maximum file size in MB (default: 10)
    """
    if not value:
        return

    # Define allowed file types
    if file_type == "image":
        allowed_types = ["jpg", "jpeg", "png", "webp"]
        error_message = _("Only JPG, PNG, WebP images allowed.")
    elif file_type == "file":
        allowed_types = ["jpg", "jpeg", "png", "webp", "pdf"]
        error_message = _("Only JPG, PNG, WebP, PDF files allowed.")
    else:
        # Custom file types
        allowed_types = file_type if isinstance(file_type, list) else [file_type]
        error_message = _("Only {extensions} files allowed.").format(
            extensions=", ".join(allowed_types).upper()
        )

    # Check file type
    filename = getattr(value, "name", "").lower()
    if filename and not any(filename.endswith(f".{ext}") for ext in allowed_types):
        raise ValidationError(error_message)

    # Check file size
    max_size = max_size_mb * 1024 * 1024  # Convert MB to bytes
    if value.size > max_size:
        raise ValidationError(
            _("File must be under {max_size}MB.").format(max_size=max_size_mb)
        )


###############   CONVENIENCE FUNCTIONS FOR COMMON CASES  ###############
# For Serializers
def validate_image_only(value, max_size_mb=10):
    """Validate image files only in serializers"""
    return validate_file(value, file_type="image", max_size_mb=max_size_mb)


def validate_document_file(value, max_size_mb=10):
    """Validate document files in serializers"""
    return validate_file(value, file_type="file", max_size_mb=max_size_mb)


def validate_pdf_only(value, max_size_mb=10):
    """Validate PDF files only in serializers"""
    return validate_file(value, file_type=["pdf"], max_size_mb=max_size_mb)


# For Models
def validate_model_image_only(value):
    """Validate image files only in models"""
    return validate_model_file(value, file_type="image", max_size_mb=10)


def validate_model_document_file(value):
    """Validate document files in models"""
    return validate_model_file(value, file_type="file", max_size_mb=10)


def validate_model_pdf_only(value):
    """Validate PDF files only in models"""
    return validate_model_file(value, file_type=["pdf"], max_size_mb=10)
