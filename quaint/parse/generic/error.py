
__all__ = ['QuaintSyntaxError']

class QuaintSyntaxError(Exception):
    def __init__(self, kind, *info):
        self.kind = kind
        self.info = info
        super().__init__("%s (%s)" % (self.kind, ", ".join(map(str, self.info))))
