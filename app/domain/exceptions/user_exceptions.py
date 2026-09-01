class DuplicateEmailException(Exception):
    # Error cuando el email ya existe
    def __init__(self, message: str = "email ya registrado"):
        super().__init__(message)


class DuplicateUserException(Exception):
    # Error generico de duplicado para dni / telefono / cedula
    def __init__(self, message: str = "Usuario ya registrado"):
        super().__init__(message)


class MissingFieldsException(Exception):
    # Error por campos obligatorios faltantes
    def __init__(self, message: str = "Campos faltantes"):
        super().__init__(message)


class InvalidFormatException(Exception):
    # Error de formato invalido para dni / telefono / cedula
    def __init__(self, message: str = "Formato inválido, debe tener 8 caracteres"):
        super().__init__(message)


class PasswordTooShortException(Exception):
    # Error por password menor a 8 caracteres
    def __init__(self, message: str = "La contraseña debe tener al menos 8 caracteres"):
        super().__init__(message)


class InvalidEmailException(Exception):
    # Error por email sin arroba
    def __init__(self, message: str = "email invalido"):
        super().__init__(message)


class UnauthorizedException(Exception):
    # No autenticado
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message)


class ForbiddenException(Exception):
    # Autenticado pero sin permiso de administrador
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message)
