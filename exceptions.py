class APIError(Exception):
    pass


class ResponseDicIsEmptyException(Exception):
    pass


class ResponseDicNotContainHomeworkKeyException(Exception):
    pass


class ResponseKeyHomeworksIsNotListException(Exception):
    pass


class NoRequiredKey(Exception):
    pass
