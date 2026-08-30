# Technical Plan — User Registration (001-user_register)

## 1. Functional Requirements Mapping to Modules

| Spec Requirement (spec.md) | Clean Architecture Module | Responsibility |
|---|---|---|
| Administrator pre-provisioned via `.env` (`NAME`, `PASSWORD`) at project root, single admin, not in repo, plain text | `infrastructure/config/settings.py` + `infrastructure/db/seed/admin_seed.py` | Load env via `pydantic-settings`; seed/check admin existence on startup; Domain prohibits creation of role `ADMINISTRATOR` via use case |
| Exclusive creation right: only Administrator can create Receptionist/Professional, no self-registration | `application/use_cases/user/create_receptionist.py`, `create_professional.py` + `entrypoints/api/v1/dependencies.py` (`get_current_admin`) + `entrypoints/api/v1/routes/user_router.py` | Auth dependency verifies admin identity before delegating to use case |
| Required fields: name, last_name, dni, email, phone, password (+ cedula for Professional) | `domain/entities/user.py` + `application/dtos/user_dtos.py` | Entity holds canonical fields; DTOs enforce presence (`Campos faltantes` is enforced at DTO validation level) |
| Completeness validation: `Campos faltantes` | `application/dtos/user_dtos.py` (Pydantic `field_validator` / required fields) + `entrypoints` exception mapper | Missing/empty fields rejected at entrypoint before reaching domain; mapped to 400 |
| Uniqueness: email, dni, phone, cedula must be unique; errors `email ya registrado` / `Usuario ya registrado` | `domain/repositories/user_repository.py` (abstract: `exists_by_email`, `exists_by_dni`, `exists_by_phone`, `exists_by_cedula`) → `infrastructure/repositories/postgres_user_repository.py` | Use case orchestrates sequential existence checks; domain exceptions `DuplicateEmailException`, `DuplicateUserException` raised |
| Email format: must contain `@`, error `email invalido` via Pydantic | `application/dtos/user_dtos.py` (`EmailStr` + custom validator) | Pydantic validation at DTO layer; entrypoint maps `ValidationError` to 422 with `email invalido` |
| DNI format: exactly 8 digits, error `Formato inválido, debe tener 8 caracteres` | `application/dtos/user_dtos.py` + `domain/entities/user.py` invariant check | Regex `^\d{8}$` in DTO; domain guard as secondary defense |
| Phone format: exactly 10 digits, same error pattern | `application/dtos/user_dtos.py` | Regex `^\d{10}$` |
| Cedula format: 7-8 alphanumeric, error `Formato inválido, debe tener 7 u 8 caracteres` (Professional only) | `application/dtos/user_dtos.py` (conditional DTO) + domain | Regex `^[A-Za-z0-9]{7,8}$`; separate DTO `CreateProfessionalRequest` |
| Password: min 8 chars, error `La contraseña debe tener al menos 8 caracteres` | `application/dtos/user_dtos.py` + `infrastructure/services/bcrypt_password_service.py` | Length validator in DTO; hashing in infrastructure service implementing domain `PasswordService` port |
| Account active immediately, role assigned at creation | `domain/entities/user.py` (`is_active: bool = True`, `role: UserRole`) | Use case sets `is_active=True`; role is input parameter restricted to `RECEPTIONIST`/`PROFESSIONAL` |
| No system limits on attempts/storage | No rate-limit module in this iteration; noted as future concern | — |

## 2. Folder and File Structure

```
app/
├── domain/
│   ├── entities/
│   │   └── user.py
│   ├── repositories/
│   │   └── user_repository.py
│   ├── services/
│   │   └── password_service.py
│   └── exceptions/
│       └── user_exceptions.py
├── application/
│   ├── dtos/
│   │   └── user_dtos.py
│   └── use_cases/
│       └── user/
│           ├── create_receptionist.py
│           ├── create_professional.py
│           └── _base_create_user.py  # shared orchestration helper (optional)
├── infrastructure/
│   ├── config/
│   │   └── settings.py
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   ├── models/
│   │   │   └── user_model.py
│   │   └── seed/
│   │       └── admin_seed.py
│   ├── repositories/
│   │   └── postgres_user_repository.py
│   └── services/
│       └── bcrypt_password_service.py
└── entrypoints/
    └── api/
        └── v1/
            ├── main.py
            ├── dependencies.py
            └── routes/
                └── user_router.py

specs/001-user_register/
├── spec.md
└── plan.md
.env  # project root, contains NAME, PASSWORD, DATABASE_URL, SECRET_KEY
```

New files only; no modification to existing `docker-compose.yml` / `Dockerfile` except ensuring `DATABASE_URL` and `NAME`/`PASSWORD` are passed via `environment` in `docker-compose.yml` (already supports interpolation).

Frontend (React + Tailwind) scope for this feature:
```
frontend/src/
├── pages/
│   └── AdminCreateUserPage.jsx
└── components/
    └── UserCreateForm.jsx  # variant prop: receptionist | professional
```
Frontend is out-of-scope for backend plan but contract defined via API; listed for completeness.

## 3. Data Model / Schemas

### 3.1 Domain Entity (Pure Python, no framework imports) — `domain/entities/user.py`

```
@dataclass
User:
  id: UUID | None
  name: str
  last_name: str
  dni: str              # 8 digits, unique, indexed
  email: str            # unique, indexed
  phone: str            # 10 digits, unique, indexed
  password_hash: str    # never plain text in entity after creation
  role: UserRole        # Enum: ADMINISTRATOR | RECEPTIONIST | PROFESSIONAL
  cedula: str | None    # 7-8 alphanumeric, unique where not null, only for PROFESSIONAL
  is_active: bool       # default True
  created_at: datetime

Enum UserRole:
  ADMINISTRATOR = "administrator"
  RECEPTIONIST = "receptionist"
  PROFESSIONAL = "professional"
```

Domain invariants (enforced in `__post_init__` without import of Pydantic):
- `role == PROFESSIONAL` ↔ `cedula is not None`
- All string fields stripped, non-empty

### 3.2 Infrastructure ORM Model — `infrastructure/db/models/user_model.py` (SQLAlchemy)

```
Table users:
  id              UUID PK default gen_random_uuid()
  name            VARCHAR(100) NOT NULL
  last_name       VARCHAR(100) NOT NULL
  dni             VARCHAR(8) UNIQUE NOT NULL  CHECK (dni ~ '^\d{8}$')
  email           VARCHAR(255) UNIQUE NOT NULL
  phone           VARCHAR(10) UNIQUE NOT NULL CHECK (phone ~ '^\d{10}$')
  password_hash   VARCHAR(255) NOT NULL
  role            VARCHAR(20) NOT NULL CHECK (role IN ('administrator','receptionist','professional'))
  cedula          VARCHAR(8) UNIQUE NULL CHECK (cedula ~ '^[A-Za-z0-9]{7,8}$')
  is_active       BOOLEAN NOT NULL DEFAULT TRUE
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()

Indexes: unique on dni, email, phone, cedula (partial where not null)
```

Single-table design chosen over joined-table inheritance to keep queries simple and enforce cross-role uniqueness (e.g., dni cannot repeat between receptionist and professional).

### 3.3 Application DTOs — `application/dtos/user_dtos.py` (Pydantic)

```
CreateReceptionistRequest:
  name: str (min_length=1, strip)
  last_name: str (min_length=1)
  dni: str (pattern='^\d{8}$', error="Formato inválido, debe tener 8 caracteres")
  email: EmailStr (if no '@' -> "email invalido")
  phone: str (pattern='^\d{10}$', error="Formato inválido, debe tener 10 caracteres")
  password: str (min_length=8, error="La contraseña debe tener al menos 8 caracteres")

CreateProfessionalRequest extends CreateReceptionistRequest:
  cedula: str (pattern='^[A-Za-z0-9]{7,8}$', error="Formato inválido, debe tener 7 u 8 caracteres")

UserResponse:
  id: UUID
  name: str
  last_name: str
  dni: str
  email: str
  phone: str
  role: UserRole
  cedula: str | None
  is_active: bool
  created_at: datetime
```

Pydantic handles `Campos faltantes` automatically: missing required field → ValidationError mapped to `Campos faltantes` (400) to match spec literal; alternative is 422 but spec mandates literal string.

### 3.4 Settings Schema — `infrastructure/config/settings.py`

```
Settings(BaseSettings):
  NAME: str
  PASSWORD: str
  DATABASE_URL: str
  SECRET_KEY: str  # for future JWT
  model_config: env_file=".env" at project root
```

## 4. Interface / API / Signature Contract

### 4.1 Repository Port — `domain/repositories/user_repository.py`

```
class UserRepository(ABC):
  def get_by_email(self, email: str) -> User | None
  def get_by_dni(self, dni: str) -> User | None
  def get_by_phone(self, phone: str) -> User | None
  def get_by_cedula(self, cedula: str) -> User | None
  def exists_by_email(self, email: str) -> bool
  def exists_by_dni(self, dni: str) -> bool
  def exists_by_phone(self, phone: str) -> bool
  def exists_by_cedula(self, cedula: str) -> bool
  def save(self, user: User) -> User

class PasswordService(ABC):
  def hash(self, plain: str) -> str
  def verify(self, plain: str, hashed: str) -> bool
```

### 4.2 Use Case Signatures — `application/use_cases/user/`

```
class CreateReceptionistUseCase:
  def __init__(self, user_repo: UserRepository, pwd_service: PasswordService)
  def execute(self, dto: CreateReceptionistRequest) -> User

class CreateProfessionalUseCase:
  def __init__(self, user_repo: UserRepository, pwd_service: PasswordService)
  def execute(self, dto: CreateProfessionalRequest) -> User

# Shared internal steps extracted to avoid duplication but exposed as two public use cases
# to respect "one class per operation" rule from AGENTS.md.
```

Domain exceptions — `domain/exceptions/user_exceptions.py`:
```
DuplicateEmailException(message="email ya registrado") -> HTTP 409
DuplicateUserException(message="Usuario ya registrado") -> HTTP 409  (covers dni/phone/cedula)
MissingFieldsException(message="Campos faltantes") -> HTTP 400
InvalidFormatException(message="Formato inválido, debe tener X caracteres") -> HTTP 422
PasswordTooShortException(message="La contraseña debe tener al menos 8 caracteres") -> HTTP 422
UnauthorizedException -> HTTP 401
ForbiddenException -> HTTP 403 (non-admin attempt)
```

### 4.3 HTTP API — `entrypoints/api/v1/routes/user_router.py`

```
POST /api/v1/users/receptionists
  Auth: Bearer <admin_jwt> OR Basic via admin credentials (decision: JWT after admin login)
  Body: CreateReceptionistRequest (JSON)
  Success: 201 { UserResponse }
  Errors:
    400 Campos faltantes
    409 email ya registrado
    409 Usuario ya registrado
    422 email invalido | Formato inválido... | La contraseña...

POST /api/v1/users/professionals
  Auth: same
  Body: CreateProfessionalRequest
  Success: 201 { UserResponse }
  Errors: same + cedula validation

POST /api/v1/auth/login  # required to obtain token for admin
  Body: { email | name, password }  # admin uses NAME+PASSWORD from .env
  Success: 200 { access_token, token_type }

GET /api/v1/users  # optional list for admin, not in spec but implied for verification
```

Headers: `Authorization: Bearer <token>`

Dependency injection — `entrypoints/api/v1/dependencies.py`:
```
def get_db_session() -> Session
def get_user_repository(session=Depends(get_db_session)) -> UserRepository
def get_password_service() -> PasswordService
def get_current_admin(token) -> User  # verifies role == ADMINISTRATOR, raises 401/403
def get_create_receptionist_use_case(...) -> CreateReceptionistUseCase
```

Frontend contract (React):
```
fetch POST /api/v1/users/receptionists with JSON, handle 201 vs error.detail string
fetch POST /api/v1/users/professionals
```

### 4.4 Admin Seed Contract

```
admin_seed.py :: ensure_admin_exists():
  reads settings.NAME, settings.PASSWORD
  if not exists_by_email or exists_by_role ADMINISTRATOR:
    create User(name=NAME split, role=ADMINISTRATOR, ...), hash password, save
  runs on FastAPI startup event (lifespan)
```

## 5. Core Algorithms / Logic — Pseudocode

### 5.1 DTO Validation (Pydantic, entrypoint layer)

```
# Pydantic automatically:
# - if field missing or "" after strip -> raise ValidationError -> mapper returns "Campos faltantes" (400)
# - if email lacks '@' -> EmailStr validation -> "email invalido" (422)
# - if dni !~ ^\d{8}$ -> "Formato inválido, debe tener 8 caracteres" (422)
# - similarly phone, cedula, password length
```

### 5.2 CreateReceptionistUseCase.execute(dto)

```
function execute(dto):
  # dto already validated for format/completeness at entrypoint
  # uniqueness checks (order: email first for specific message)
  if user_repo.exists_by_email(dto.email):
    raise DuplicateEmailException("email ya registrado")

  if user_repo.exists_by_dni(dto.dni):
    raise DuplicateUserException("Usuario ya registrado")

  if user_repo.exists_by_phone(dto.phone):
    raise DuplicateUserException("Usuario ya registrado")

  # domain-level password service
  password_hash = pwd_service.hash(dto.password)

  user = User(
    id=None,
    name=dto.name.strip(),
    last_name=dto.last_name.strip(),
    dni=dto.dni,
    email=dto.email.lower(),
    phone=dto.phone,
    password_hash=password_hash,
    role=RECEPTIONIST,
    cedula=None,
    is_active=True,
    created_at=now()
  )

  return user_repo.save(user)
```

### 5.3 CreateProfessionalUseCase.execute(dto)

```
function execute(dto):
  if user_repo.exists_by_email(dto.email):
    raise DuplicateEmailException("email ya registrado")
  if user_repo.exists_by_dni(dto.dni):
    raise DuplicateUserException("Usuario ya registrado")
  if user_repo.exists_by_phone(dto.phone):
    raise DuplicateUserException("Usuario ya registrado")
  if user_repo.exists_by_cedula(dto.cedula):
    raise DuplicateUserException("Usuario ya registrado")

  password_hash = pwd_service.hash(dto.password)

  user = User(..., role=PROFESSIONAL, cedula=dto.cedula, ...)

  return user_repo.save(user)
```

### 5.4 Router Handler Pseudocode

```
@router.post("/receptionists", status=201)
def create_receptionist(dto: CreateReceptionistRequest, admin=Depends(get_current_admin), use_case=Depends(...)):
  try:
    user = use_case.execute(dto)
    return UserResponse.from_entity(user)
  except DuplicateEmailException as e:
    raise HTTPException(409, detail=str(e))  # "email ya registrado"
  except DuplicateUserException as e:
    raise HTTPException(409, detail=str(e))  # "Usuario ya registrado"
  except ValidationError as e:
    # Pydantic already handled, but fallback
    raise HTTPException(422, detail=e.errors())
```

### 5.5 Startup Seed Pseudocode

```
on_startup:
  settings = Settings()  # loads .env from project root
  if not settings.NAME or not settings.PASSWORD:
    log warning "Admin .env missing NAME/PASSWORD"
    return
  if user_repo.exists_by_role(ADMINISTRATOR):
    return
  admin = User(name=first(NAME), last_name=rest(NAME), dni="00000000" placeholder? -> see note, email="admin@centro.local" placeholder?)
  # NOTE: spec .env only defines NAME and PASSWORD, not email/dni/phone for admin.
  # Seed must synthesize required unique fields or admin is treated as special auth identity outside users table.
```

> **Seed nuance**: Spec `.env` only provides `NAME` and `PASSWORD` for admin, but `users` table requires dni/email/phone unique. Two viable approaches — see Decision 1 below.

## 6. Key Technical Decisions and Alternatives Discarded

| Decision | Chosen Approach | Why | Alternative Discarded | Reason Discarded |
|---|---|---|---|---|
| **1. Admin identity storage** | **Option A (preferred): Admin as row in `users` table** with synthesized `email=admin@centro.local`, `dni=00000000`, `phone=0000000000` derived from `.env` NAME/PASSWORD, role=ADMINISTRATOR, `is_active=True`. Alternative **Option B: Admin outside DB, authenticated purely via .env comparison** (no DB row). Plan documents both; recommend Option A for unified auth/JWT. | Keeps auth logic uniform (`get_current_admin` queries same table), allows JWT generation, respects single-admin rule via unique constraint on role. | Option B: pure env check | Breaks uniformity, requires separate auth path, complicates future audit logs and password rotation. Option A chosen but flagged for confirmation. |
| **2. Password storage** | `bcrypt` via `passlib[bcrypt]` in `infrastructure/services/bcrypt_password_service.py`; plain text only in `.env` for initial admin, hashed immediately on seed. | Industry standard, AGENTS.md security focus, FastAPI ecosystem compatible. | Plain text in DB, `hashlib.sha256` without salt | Violates security rules; plain text forbidden except initial `.env` |
| **3. Validation layer** | **Pydantic DTOs** in `application/dtos` as primary validator (`EmailStr`, regex). Domain entity does minimal guard. | Matches AGENTS.md (DTOs are Pydantic), gives `email invalido`, `Campos faltantes` mapping, automatic OpenAPI docs. | Manual regex in domain only, or SQLAlchemy `CheckConstraint` only | Domain must stay framework-free; DB constraints are secondary defense, not UX-friendly error messages. |
| **4. Uniqueness enforcement** | **App-level check via repository `exists_*` + DB unique constraints** (defense in depth). Use case checks first for friendly messages, DB constraint catches race conditions. | Provides spec-mandated distinct messages (`email ya registrado` vs `Usuario ya registrado`), handles concurrency. | Only DB unique constraint with generic 500 | Loses ability to return spec-specific messages; race condition handling poor. |
| **5. Single table vs separate tables** | **Single `users` table with `role` discriminator and nullable `cedula`** | As argued in 3.2: enforces cross-role uniqueness (dni/phone/email cannot duplicate across roles), simple queries, aligns with spec business rule "unique across entire system". | Separate `receptionists` and `professionals` tables | Would allow same dni in both tables, violating spec; requires union queries for uniqueness. |
| **6. API design: one vs two endpoints** | **Two explicit endpoints** `POST /users/receptionists` and `POST /users/professionals` each bound to its DTO and use case. | Respects AGENTS.md "one class per use case", clear OpenAPI, no conditional `cedula` ambiguity, easier role-based validation. | Single `POST /users` with `role` field in body | Requires conditional validation (cedula required only if role=professional), more complex DTO, easier to send wrong role. |
| **7. Auth mechanism** | **JWT Bearer** after `POST /auth/login` using admin credentials; `get_current_admin` verifies JWT and role. | Stateless, fits FastAPI, docker-compose already exposes 8000, future-proof for receptionist/professional login. | Session cookie, Basic Auth per request | Session requires server state; Basic Auth sends password each request, less secure. |
| **8. `.env` loading** | `pydantic-settings` `BaseSettings` with `env_file=".env"` at project root, as per docker-compose interpolation. | Already used in docker-compose, type-safe, validated at startup. | `python-dotenv` manual load, `os.getenv` | Less validation, no type coercion. |
| **9. CSRF & Security headers** | `CSRF` via `fastapi-csrf-protect` for form endpoints if HTML frontend; `CORS` restricted to frontend origin. | AGENTS.md mandates CSRF for forms. | No CSRF | Violates security rules. |
| **10. ORM choice** | **SQLAlchemy 2.0 (async disabled sync first)** with `psycopg2` (already in Dockerfile `libpq-dev`) | Dockerfile already installs `libpq-dev`, PostgreSQL 16, ecosystem standard for FastAPI Clean Architecture. | Django ORM, Tortoise ORM | Django ORM conflicts with FastAPI; Tortoise less mature, not in Dockerfile. |

## 7. Test Strategy

### 7.1 Unit Tests (fast, no DB)

- **Domain entity tests** `tests/domain/test_user_entity.py`:
  - Invariants: professional without cedula raises, receptionist with cedula raises, `is_active` defaults True.
- **DTO validation tests** `tests/application/test_user_dtos.py`:
  - `Campos faltantes` when any required field missing/empty/whitespace.
  - Invalid email without `@` → `email invalido`.
  - DNI `123`, `123456789`, `abcd1234` → `Formato inválido, debe tener 8 caracteres`.
  - Phone `123`, `12345678901`, `abcdefghij` → `Formato inválido, debe tener 10 caracteres`.
  - Cedula `abc`, `123456789`, `123456` → `Formato inválido, debe tener 7 u 8 caracteres`; valid `ABC1234`, `12345678`.
  - Password `short` (7 chars) → `La contraseña debe tener al menos 8 caracteres`.
- **Use case tests** `tests/application/test_create_user_use_cases.py` (mocked `UserRepository`, `PasswordService`):
  - Success path returns user with hashed password and `is_active=True`.
  - Duplicate email → `DuplicateEmailException` (`email ya registrado`).
  - Duplicate dni/phone/cedula → `DuplicateUserException` (`Usuario ya registrado`).
  - Verify `pwd_service.hash` called exactly once.

### 7.2 Integration Tests (with Test DB)

- **Repository tests** `tests/infrastructure/test_postgres_user_repository.py` (uses `docker-compose db` test container or `pytest` + `testcontainers`):
  - Save and retrieve user, verify ORM ↔ entity mapping.
  - Unique constraints: inserting duplicate email/dni/phone/cedula raises `IntegrityError` mapped to domain exception.
  - `exists_by_*` methods.
- **Seed test** `tests/infrastructure/test_admin_seed.py`:
  - With `.env` `NAME=Gabriel Cari`, `PASSWORD=gabi12345`, seed creates admin once, second run idempotent.
- **API integration tests** `tests/entrypoints/test_user_router.py` (FastAPI `TestClient`):
  - `POST /users/receptionists` with valid admin token → 201.
  - `POST /users/professionals` with valid cedula → 201.
  - Missing fields → 400 `Campos faltantes`.
  - Invalid formats → 422 with exact spec messages.
  - Duplicate flows → 409 with `email ya registrado` / `Usuario ya registrado`.
  - Non-admin token → 403; no token → 401.
  - Verify `.env` not exposed via any endpoint.

### 7.3 End-to-End / System Tests

- Docker-compose full stack: `docker-compose up` → hit `/docs` OpenAPI, perform admin login then create receptionist/professional via `curl` or React form.
- Frontend manual test: Admin logs in, creates both user types, checks error messages in UI.

### 7.4 Linter, Type, and Coverage Gates (Definition of Done)

- **Linter**: `ruff check` + `ruff format` (or `flake8` + `black`) must pass — PEP8 per AGENTS.md.
- **Type check**: `mypy app/` (strict for domain/application).
- **Coverage target**: ≥80% for `domain` + `application`; ≥60% for `infrastructure` (DB-dependent).
- **Security**: `bandit` scan, ensure no secret in code, `.env` in `.gitignore` (already present).
- **CI**: `pytest` with `coverage` + linter in GitHub Actions before merge.

### 7.5 Test Data and Fixtures

- Factory fixtures: `receptionist_payload()`, `professional_payload(overrides)`.
- Admin fixture: `admin_headers()` generates JWT for `NAME=Gabriel Cari`.
- DB fixture: transactional rollback per test to keep isolation.

### 7.6 Out of Scope for This Iteration

- Rate limiting, email verification, password reset, audit logging, soft delete.
- Frontend unit tests (React Testing Library) deferred to frontend plan.

