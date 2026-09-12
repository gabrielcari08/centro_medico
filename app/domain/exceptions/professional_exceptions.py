class ProfessionalNotFoundException(Exception):
    def __init__(self, message: str = "Professional Not Found"):
        super().__init__(message)


class AlreadyActiveException(Exception):
    def __init__(self, message: str = "Profesional ya activado"):
        super().__init__(message)


class AlreadyInactiveException(Exception):
    def __init__(self, message: str = "Profesional ya desactivado"):
        super().__init__(message)


class DuplicateCedulaException(Exception):
    def __init__(self, message: str = "Usuario ya registrado"):
        super().__init__(message)
