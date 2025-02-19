class PdfFileInvalidFormat(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

class InvalidCollectionName(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

class InvalidCollection(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

class DatabaseError(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

class Web3ConnectionError(Exception):
    """Custom exception for Web3 connection issues"""
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)