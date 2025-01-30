class CustomError(Exception):
    def __init__(self, error_code, message):
        self.error_code = error_code
        self.message = message
        super().__init__(f"Error with code {error_code}: {message}")
        