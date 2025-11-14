from .exceptions import ValidationError


def validate_user_id(user_id):
    if user_id is None:
        raise ValidationError("user_id is required")

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise ValidationError("user_id must be an integer")

    if user_id <= 0:
        raise ValidationError("user_id must be positive")

    return user_id


def validate_post_data(data):
    if not isinstance(data, dict):
        raise ValidationError("data must be a dictionary")

    validated_data = {}

    if not data:
        return validated_data

    if "like_count" in data:
        raise ValidationError(
            "like_count cannot be updated directly. Use like operations instead."
        )

    if "created_at" in data:
        raise ValidationError("created_at cannot be updated")

    return validated_data


def validate_pagination(limit, offset=0):
    try:
        limit = int(limit)
    except (ValueError, TypeError):
        raise ValidationError("limit must be an integer")

    try:
        offset = int(offset)
    except (ValueError, TypeError):
        raise ValidationError("offset must be an integer")

    if limit <= 0:
        raise ValidationError("limit must be positive")

    if limit > 1000:
        raise ValidationError("limit cannot exceed 1000")

    if offset < 0:
        raise ValidationError("offset cannot be negative")

    return limit, offset
