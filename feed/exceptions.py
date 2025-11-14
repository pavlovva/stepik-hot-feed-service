class FeedBaseException(Exception):
    def __init__(self, message=None):
        self.message = message or self.default_message
        super().__init__(self.message)

    default_message = "An error occurred"


class PostNotFoundError(FeedBaseException):
    default_message = "Post not found"


class LikeAlreadyExistsError(FeedBaseException):
    default_message = "Like already exists"


class LikeNotFoundError(FeedBaseException):
    default_message = "Like not found"


class ValidationError(FeedBaseException):
    default_message = "Validation error"
