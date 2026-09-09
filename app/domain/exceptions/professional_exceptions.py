class ProfessionalNotFoundException(Exception):
    def __init__(self, message: str = "Professional not found"):
        super().__init__(message)


class DuplicateCedulaException(Exception):
    def __init__(self, message: str = "Usuario ya registrado"):
        super().__init__(message)
