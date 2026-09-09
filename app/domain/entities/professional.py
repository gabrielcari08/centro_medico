from dataclasses import dataclass


@dataclass
class Professional:
    user_id: int
    cedula: str
    id: int | None = None

    def __post_init__(self):
        # Normalizacion y validacion basica
        self.cedula = self.cedula.strip()
        if not self.cedula:
            raise ValueError("Campos faltantes")
