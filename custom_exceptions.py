class Error(Exception):
    pass


class NoResultsFoundException(Error):
    def __init__(self, arg):
        self.strerror = arg
        self.args = {arg}


class IllegalCharacterInHashtagException(Error):
    def __init__(self, arg):
        self.strerror = arg
        self.args = {arg}
