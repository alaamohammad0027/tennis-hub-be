from django.db.models import Max


def generate_reference(model_class, field_name="reference_id", prefix=None, event=None):
    """
    Generate unique 6-digit reference: CCNNNN
    - CC = event identifier from UUID (01-99)
    - NNNN = Counter per event (0001-9999)

    Example: 010001, 450023, 990100
    """
    if not event:
        raise ValueError("event is required")

    # Convert event UUID to consistent 2-digit number (01-99)
    uuid_str = str(event.id).replace("-", "")
    event_num = (int(uuid_str[:8], 16) % 99) + 1  # Range: 1-99

    # Get next counter for this event
    filter_kwargs = {"event": event, f"{field_name}__isnull": False}

    latest_ref = model_class.objects.filter(**filter_kwargs).aggregate(Max(field_name))[
        f"{field_name}__max"
    ]

    if latest_ref:
        try:
            # Get numeric part
            numeric_part = latest_ref.split("-")[-1] if prefix else latest_ref
            # Extract last 4 digits (counter)
            seq_num = int(numeric_part[-4:]) + 1
        except (IndexError, ValueError):
            seq_num = 1
    else:
        seq_num = 1

    # Walk forward until we find a slot that doesn't already exist.
    # This guards against stale MAX results (e.g. same-transaction inserts
    # not yet visible to the aggregate, or concurrent race conditions).
    while True:
        reference = f"{event_num:02d}{seq_num:04d}"
        candidate = f"{prefix}-{reference}" if prefix else reference
        if not model_class.objects.filter(
            event=event, **{field_name: candidate}
        ).exists():
            return candidate
        seq_num += 1
