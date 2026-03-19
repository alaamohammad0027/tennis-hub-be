from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import append_meta
from core.services.fields import LimitedFieldsSerializer
from django.conf import settings


from django.conf import settings


def preprocess_spectacular_hook(result, generator, request, public):
    """
    Preprocessing hook to handle:
    1. LimitedFieldsSerializer schema generation
    2. X-Language header to all endpoints
    3. Default error response to all endpoints
    """

    # Handle LimitedFieldsSerializer before schema generation
    for path, path_item in result.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() not in [
                "get",
                "post",
                "put",
                "patch",
                "delete",
                "options",
                "head",
            ]:
                continue

            # Try to get the view and serializer to process LimitedFieldsSerializer
            try:
                # The operation should have operationId which helps identify the view
                operation_id = operation.get("operationId", "")

                # Process request body schema
                if "requestBody" in operation:
                    content = operation["requestBody"].get("content", {})
                    for media_type, media_content in content.items():
                        if "schema" in media_content:
                            schema = media_content["schema"]
                            # Fix any nested LimitedFieldsSerializer schemas
                            _fix_limited_fields_in_schema(
                                schema, result.get("components", {}).get("schemas", {})
                            )

                # Process response schemas
                if "responses" in operation:
                    for status_code, response in operation["responses"].items():
                        if isinstance(response, dict) and "content" in response:
                            content = response.get("content", {})
                            for media_type, media_content in content.items():
                                if "schema" in media_content:
                                    schema = media_content["schema"]
                                    # Fix any nested LimitedFieldsSerializer schemas
                                    _fix_limited_fields_in_schema(
                                        schema,
                                        result.get("components", {}).get("schemas", {}),
                                    )
            except Exception:
                pass

    # Define the error schema
    error_schema = {
        "type": "object",
        "properties": {
            "error": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "example": "VALIDATION_ERROR"},
                    "message": {"type": "string", "example": "Validation failed."},
                    "details": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "example": {"field_name": ["Error message."]},
                    },
                    "status": {"type": "integer", "example": 400},
                },
            }
        },
    }

    # Get language configuration from settings
    supported_languages = [lang[0] for lang in settings.LANGUAGES]
    default_language = getattr(
        settings, "DEFAULT_USER_LANGUAGE", settings.LANGUAGE_CODE.split("-")[0]
    )

    # Add X-Language header parameter and error response to all paths
    for path, path_item in result.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() in [
                "get",
                "post",
                "put",
                "patch",
                "delete",
                "options",
                "head",
            ]:
                # Add X-Language header
                if "parameters" not in operation:
                    operation["parameters"] = []

                # Check if already exists
                has_language = any(
                    p.get("name") == "X-Language" for p in operation["parameters"]
                )

                if not has_language:
                    operation["parameters"].append(
                        {
                            "name": "X-Language",
                            "in": "header",
                            "required": False,
                            "description": "Language code",
                            "schema": {
                                "type": "string",
                                "enum": supported_languages,
                                "default": default_language,
                            },
                        }
                    )

                # Add default error response
                if "responses" not in operation:
                    operation["responses"] = {}

                if "default" not in operation["responses"]:
                    operation["responses"]["default"] = {
                        "description": "Error response",
                        "content": {"application/json": {"schema": error_schema}},
                    }

    return result


def _fix_limited_fields_in_schema(schema, components_schemas):
    """
    Recursively fix schemas that might have issues with LimitedFieldsSerializer
    """
    if not isinstance(schema, dict):
        return

    # Handle $ref
    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        if ref_name in components_schemas:
            _fix_limited_fields_in_schema(
                components_schemas[ref_name], components_schemas
            )
        return

    # Handle properties
    if "properties" in schema:
        for prop_name, prop_schema in schema["properties"].items():
            _fix_limited_fields_in_schema(prop_schema, components_schemas)

    # Handle array items
    if "items" in schema:
        _fix_limited_fields_in_schema(schema["items"], components_schemas)

    # Handle anyOf, oneOf, allOf
    for key in ["anyOf", "oneOf", "allOf"]:
        if key in schema:
            for sub_schema in schema[key]:
                _fix_limited_fields_in_schema(sub_schema, components_schemas)


class CustomSpectacularAutoSchema(AutoSchema):
    """
    Custom AutoSchema for handling custom tags from views and LimitedFieldsSerializer
    """

    def get_filter_backends(self):
        """Include filter backends for custom actions"""
        # Get the action-specific filter backends if they exist
        action = getattr(self.view, "action", None)
        if action and hasattr(self.view, action):
            action_method = getattr(self.view, action)
            if hasattr(action_method, "kwargs"):
                action_filters = action_method.kwargs.get("filter_backends")
                if action_filters:
                    return action_filters

        # Fall back to viewset-level filter backends
        return super().get_filter_backends()

    def _get_serializer_name(self, serializer, direction, bypass_extensions=False):
        """
        Override to generate unique component names for serializers with excluded fields
        """
        # Get the base name from parent
        name = super()._get_serializer_name(serializer, direction, bypass_extensions)

        # Check if serializer has excluded fields via DynamicFieldsModelSerializer
        if hasattr(serializer, "fields"):
            # Get all possible fields from the model
            serializer_class = serializer.__class__
            meta = getattr(serializer_class, "Meta", None)

            if meta and hasattr(meta, "model"):
                # Get the original field names that should exist
                from django.db import models as django_models

                model = meta.model
                all_field_names = set()

                # Get model field names
                for field in model._meta.get_fields():
                    if not field.many_to_many and not (
                        field.one_to_many and not field.related_name
                    ):
                        all_field_names.add(field.name)

                # Get current serializer field names
                current_field_names = set(serializer.fields.keys())

                # Find excluded fields
                excluded_fields = all_field_names - current_field_names

                if excluded_fields:
                    # Create a unique name based on excluded fields
                    excluded_str = "".join(
                        word.capitalize() for word in sorted(excluded_fields)
                    )
                    name = f"{name}Without{excluded_str}"

        return name

    def get_request_serializer(self):
        """Override to get serializer with proper exclusions for request"""
        return self._get_serializer_with_exclusions("request")

    def get_response_serializers(self):
        """Override to get serializer with proper exclusions for response"""
        return self._get_serializer_with_exclusions("response")

    def _get_serializer_with_exclusions(self, direction):
        """Get serializer and apply view's get_serializer logic for exclusions"""
        view = self.view

        # Set the action based on method and path
        action = getattr(view, "action", None)
        if action is None and hasattr(self, "method"):
            import uritemplate
            from rest_framework.generics import (
                RetrieveAPIView,
                ListAPIView,
                CreateAPIView,
                UpdateAPIView,
                DestroyAPIView,
                GenericAPIView,
            )
            from rest_framework.mixins import (
                ListModelMixin,
                RetrieveModelMixin,
                CreateModelMixin,
                UpdateModelMixin,
                DestroyModelMixin,
            )

            path_variables = uritemplate.variables(self.path)
            lookup_url_kwarg = getattr(view, "lookup_url_kwarg", None) or getattr(
                view, "lookup_field", "pk"
            )
            has_lookup_in_path = lookup_url_kwarg in path_variables

            # Determine action based on view class and HTTP method
            if self.method.upper() == "GET":
                # Check view class hierarchy for GET requests
                if isinstance(view, RetrieveAPIView) or isinstance(
                    view, RetrieveModelMixin
                ):
                    action = "retrieve"
                elif isinstance(view, ListAPIView) or isinstance(view, ListModelMixin):
                    action = "list"
                elif has_lookup_in_path:
                    # Path has lookup field, so it's a retrieve
                    action = "retrieve"
                else:
                    # No lookup in path, likely a list
                    action = "list"

            elif self.method.upper() == "POST":
                if isinstance(view, CreateAPIView) or isinstance(
                    view, CreateModelMixin
                ):
                    action = "create"
                else:
                    action = "create"

            elif self.method.upper() == "PUT":
                if isinstance(view, UpdateAPIView) or isinstance(
                    view, UpdateModelMixin
                ):
                    action = "update"
                else:
                    action = "update"

            elif self.method.upper() == "PATCH":
                if isinstance(view, UpdateAPIView) or isinstance(
                    view, UpdateModelMixin
                ):
                    action = "partial_update"
                else:
                    action = "partial_update"

            elif self.method.upper() == "DELETE":
                if isinstance(view, DestroyAPIView) or isinstance(
                    view, DestroyModelMixin
                ):
                    action = "destroy"
                else:
                    action = "destroy"

            if action:
                view.action = action

        # Now get the serializer - view.get_serializer will apply exclusions
        from drf_spectacular.plumbing import build_serializer_context
        from rest_framework.generics import GenericAPIView

        serializer = None
        try:
            context = build_serializer_context(view)

            if isinstance(view, GenericAPIView):
                # Call the view's get_serializer which will apply exclusions
                serializer = view.get_serializer(context=context)
            elif hasattr(view, "get_serializer") and callable(view.get_serializer):
                serializer = view.get_serializer(context=context)
            elif hasattr(view, "get_serializer_class") and callable(
                view.get_serializer_class
            ):
                serializer = view.get_serializer_class()(context=context)
            elif hasattr(view, "serializer_class"):
                serializer = view.serializer_class(context=context)
        except Exception:
            pass

        # Mark which fields were excluded for the schema naming
        if serializer and hasattr(serializer, "__class__"):
            # Check if fields were excluded by comparing with a fresh instance
            try:
                fresh_serializer = serializer.__class__()
                excluded = set(fresh_serializer.fields.keys()) - set(
                    serializer.fields.keys()
                )
                if excluded:
                    # Store excluded fields on the serializer instance for _get_serializer_name
                    serializer._excluded_fields_for_schema = excluded
            except Exception:
                pass

        return serializer if serializer else self._get_serializer()

    def _map_serializer_field(self, field, direction, bypass_extensions=False):
        """
        Override to handle LimitedFieldsSerializer and DynamicFieldsModelSerializer
        """

        # Handle LimitedFieldsSerializer
        if isinstance(field, LimitedFieldsSerializer):
            meta = self._get_serializer_field_meta(field, direction)

            # Create a schema for the limited serializer
            if field.limited_fields:
                # Get the base serializer
                base_serializer = field.serializer_class()

                # Build properties with only limited fields
                properties = {}
                required = []

                for field_name in field.limited_fields:
                    if field_name in base_serializer.fields:
                        nested_field = base_serializer.fields[field_name]
                        # Recursively map the nested field
                        field_schema = super()._map_serializer_field(
                            nested_field, direction, bypass_extensions
                        )
                        if field_schema:
                            properties[field_name] = field_schema
                            if nested_field.required and not nested_field.read_only:
                                required.append(field_name)

                schema = {"type": "object", "properties": properties}

                if required:
                    schema["required"] = required

                # Handle many=True (array)
                if field.many:
                    return append_meta({"type": "array", "items": schema}, meta)

                return append_meta(schema, meta)
            else:
                # No limited fields, use full serializer
                serializer = field.serializer_class()
                return super()._map_serializer(serializer, direction, bypass_extensions)

        # Default behavior for other fields
        return super()._map_serializer_field(field, direction, bypass_extensions)

    def get_tags(self):
        """
        Support custom tags from view's get_swagger_tags method or swagger_tags attribute
        """
        # Get the action (for ViewSets)
        action = getattr(self.view, "action", None)

        # Check if view has get_swagger_tags method
        if hasattr(self.view, "get_swagger_tags"):
            try:
                request = getattr(self, "request", None) or getattr(
                    self.view, "request", None
                )

                if request:
                    tags_mapping = self.view.get_swagger_tags(request)
                else:
                    tags_mapping = self.view.get_swagger_tags()

                # If it returns a dict and we have an action, find matching tags
                if isinstance(tags_mapping, dict) and action:
                    matching_tags = []
                    for tag, actions in tags_mapping.items():
                        if action in actions:
                            matching_tags.append(tag)

                    if matching_tags:
                        return matching_tags

                # If it returns a list directly
                elif isinstance(tags_mapping, list):
                    return tags_mapping

            except Exception:
                pass

        # Check for swagger_tags attribute
        if hasattr(self.view, "swagger_tags"):
            tags = self.view.swagger_tags
            if isinstance(tags, (list, tuple)):
                return list(tags)
            return [tags]

        # Fall back to default behavior
        return super().get_tags()
