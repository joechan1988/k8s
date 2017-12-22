class BaseError(Exception):
    def __init__(self, message=None):
        if message is not None:
            super(BaseError, self).__init__()
            self.message = message


class PreCheckError(BaseError):
    def __init__(self, text):
        super(PreCheckError, self).__init__()
        self.message = "Pre Check Error: {0}".format(text)


class ClusterConfigError(BaseError):
    def __init__(self, text):
        super(ClusterConfigError, self).__init__()
        self.message = "Cluster Config Error: {0}. Check cluster.yml file".format(text)


class BinaryNotFoundError(BaseError):
    def __init__(self, binary_name, path):
        super(BinaryNotFoundError, self).__init__()
        self.message = "Binary '{0}' not found in temp path '{1}'".format(binary_name, path)
