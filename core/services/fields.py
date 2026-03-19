from rest_framework import serializers


class LimitedFieldsSerializer(serializers.Field):
    """
    A field that wraps a serializer with limited fields.
    Schema generation is handled by CustomSpectacularAutoSchema.
    """

    def __init__(self, serializer_class, fields=None, exclude=None, **kwargs):
        self.serializer_class = serializer_class
        self.limited_fields = fields
        self.excluded_fields = exclude
        self.many = kwargs.pop("many", False)
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        """Pass the instance to to_representation"""
        return instance

    def to_representation(self, value):
        """Convert model instance to primitive datatypes (read operation)"""
        if value is None:
            return None

        # Get the actual object from source
        source = self.source if self.source and self.source != "*" else self.field_name
        if source and hasattr(value, source):
            value = getattr(value, source)

        if value is None:
            return None

        kwargs = {"context": self.context}
        if self.limited_fields:
            kwargs["fields"] = self.limited_fields
        if self.excluded_fields:
            kwargs["exclude"] = self.excluded_fields

        serializer = self.serializer_class(value, many=self.many, **kwargs)
        return serializer.data

    def to_internal_value(self, data):
        """Convert primitive datatypes to internal value (write operation)"""
        if data is None:
            return None

        kwargs = {"context": self.context, "data": data}
        if self.limited_fields:
            kwargs["fields"] = self.limited_fields
        if self.excluded_fields:
            kwargs["exclude"] = self.excluded_fields

        serializer = self.serializer_class(many=self.many, **kwargs)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def run_validation(self, data=serializers.empty):
        """Handle validation for write operations"""
        if data is serializers.empty:
            if self.required:
                self.fail("required")
            return self.get_default()

        if data is None:
            if not self.allow_null:
                self.fail("null")
            return None

        return self.to_internal_value(data)
