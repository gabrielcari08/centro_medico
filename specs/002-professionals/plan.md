# Technical Plan — Professionals CRUD (002-professionals)

## 1. Functional Requirements Mapping to Modules

| Spec Requirement (spec.md) | Clean Architecture Module | Responsibility |
|---|---|---|
| Public listing of active professionals (no auth), alphabetical A-Z, no pagination, search by name/last_name/full name/cédula case-insensitive | `application/use_cases/professional/list_professionals.py` + `infrastructure/repositories/postgres_professional_repository.py` (join query) + `entrypoints/api/v1/routes/professional_router.py` (`GET /professionals`) | Use case orchestrates filtering/ordering; repository executes `JOIN users + professionals WHERE is_active=true` with `ILIKE`; entrypoint exposes without `Depends(get_current_admin)` |
| Retrieval of single professional by id (public, no auth; active only?) + admin can retrieve any via same endpoint (or deactivated via separate) | `application/use_cases/professional/get_professional_by_id.py` + `infrastructure/repositories/*` | Use case fetches `Professional` + `User`, checks existence → `ProfessionalNotFoundException`; public path returns 404 if inactive (or optionally 404), admin path via same use case but no active filter for deactivated list |
| Admin-only listing of deactivated professionals (for reactivation) | `application/use_cases/professional/list_deactivated_professionals.py` + `entrypoints/api/v1/routes/professional_router.py` (`GET /professionals/deactivated`) with `Depends(get_current_admin)` | Separate use case querying `WHERE is_active=false` ordered A-Z; entrypoint enforces admin role |
| Create professional (admin only) — already implemented in 001 as `POST /users/professionals`, reused but extended to respect new is_active semantics | `application/use_cases/user/create_professional.py` (existing) + `domain/entities/professional.py` | No new logic, but plan ensures it remains admin-guarded and returns alphabetical ordering in subsequent lists |
| Update professional (admin only, password not editable, all other fields editable) | `application/use_cases/professional/update_professional.py` + `application/dtos/professional_dtos.py` (`UpdateProfessionalRequest`) | Use case validates completeness/format via DTO, checks uniqueness excluding self (email→`email ya registrado`, dni/phone/cedula→`Usuario ya registrado`), updates `users` + `professionals` atomically, updates `users.updated_at` |
| Delete professional (admin only, hard delete both rows) | `application/use_cases/professional/delete_professional.py` | Use case verifies existence, deletes `professionals` then `users` (or relies on `ON DELETE CASCADE` by deleting `users`); idempotent error `Professional Not Found` |
| Activate / Deactivate professional (admin only, toggles `users.is_active`, idempotent errors `Profesional ya activado/desactivado`, persists record, blocks login when inactive) | `application/use_cases/professional/activate_professional.py`, `deactivate_professional.py` | Use case loads `User` via `Professional.user_id`, checks current `is_active`, toggles, saves; login flow in `auth_router` must already reject `is_active=false` |
| Format/completeness validation (`Campos faltantes`, `email invalido`, `Formato inválido...`, `La contraseña...` on create only) | `application/dtos/professional_dtos.py` + `domain/entities/*` secondary guards | DTOs primary validator (Pydantic `field_validator` with spec literals); domain guards as defense |
| Uniqueness across system on create/update (excluding self on update) | `domain/repositories/user_repository.py` + `professional_repository.py` → `infrastructure/repositories/postgres_*.py` | Use case orchestrates `exists_by_*` checks with `id != current` exclusion; DB unique constraints as secondary defense (`IntegrityError` → domain exception) |
| Unauthorized/forbidden handling for mutations and deactivated list | `entrypoints/api/v1/dependencies.py` (`get_current_admin`) + `entrypoints/api/v1/routes/professional_router.py` | Dependency verifies JWT and `role==administrator`; public routes omit this dependency |

## 2. Folder and File Structure

```
app/
├── domain/
│   ├── entities/
│   │   ├── user.py                          # (existing, now without cedula, with updated_at)
│   │   └── professional.py                  # (existing T1: id, user_id, cedula)
│   ├── repositories/
│   │   ├── user_repository.py               # (existing: no cedula methods)
│   │   └── professional_repository.py       # (existing: get_by_cedula, get_by_user_id, exists_by_cedula, save, + new list/get/delete)
│   ├── exceptions/
│   │   ├── user_exceptions.py               # (existing)
│   │   └── professional_exceptions.py       # (existing: ProfessionalNotFoundException, DuplicateCedulaException)
│   └── services/
│       └── password_service.py
├── application/
│   ├── dtos/
│   │   ├── user_dtos.py                     # (existing: CreateReceptionist/ProfessionalRequest, UserResponse)
│   │   └── professional_dtos.py             # NEW: UpdateProfessionalRequest, ProfessionalDetailResponse, ProfessionalListResponse
│   └── use_cases/
│       ├── user/
│       │   ├── create_receptionist.py       # (existing)
│       │   └── create_professional.py       # (existing, reused)
│       └── professional/
│           ├── list_professionals.py        # NEW: public active list + search
│           ├── list_deactivated_professionals.py # NEW: admin only
│           ├── get_professional_by_id.py    # NEW
│           ├── update_professional.py       # NEW
│           ├── delete_professional.py       # NEW
│           ├── activate_professional.py     # NEW
│           └── deactivate_professional.py   # NEW
├── infrastructure/
│   ├── config/
│   │   └── settings.py
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── models/
│   │       ├── user_model.py                # (existing: without cedula, with updated_at)
│   │       └── professional_model.py        # (existing: id, user_id FK, cedula)
│   ├── repositories/
│   │   ├── postgres_user_repository.py      # (existing)
│   │   └── postgres_professional_repository.py # (existing, extended with list/search/delete)
│   └── services/
│       └── bcrypt_password_service.py
└── entrypoints/
    └── api/
        └── v1/
            ├── main.py                      # (existing, registers professional_router)
            ├── dependencies.py              # (existing: add get_professional_repository, get_*_use_case for new use cases)
            └── routes/
                ├── auth_router.py           # (existing)
                ├── user_router.py           # (existing: create endpoints remain)
                └── professional_router.py   # NEW: GET /, GET /{id}, GET /deactivated, PUT /{id}, DELETE /{id}, PATCH /{id}/activate, PATCH /{id}/deactivate

specs/002-professionals/
├── spec.md
└── plan.md
specs/002-professioanls/
└── plan.md  # alias for typo as requested

tests/
├── domain/
│   └── test_user_entity.py, test_professional_entity.py
├── application/
│   └── test_list_professionals.py, test_update_professional.py, etc.
├── infrastructure/
│   └── test_postgres_professional_repository.py (extended)
└── entrypoints/
    └── test_professional_router.py
```

All new files follow `AGENT.md` layer rules: domain has zero framework imports (`@dataclass`, `Enum`, `ABC` only).

## 3. Data Model / Schemas

### 3.1 Domain Entities (pure Python) — `domain/entities/`

```python
@dataclass
User:
  id: int | None
  name: str
  last_name: str
  dni: str              # 8 digits, unique
  email: str            # unique
  phone: str            # 10 digits, unique
  password_hash: str
  role: UserRole        # administrator | receptionist | professional
  is_active: bool
  created_at: datetime
  updated_at: datetime  # new in 002 per spec

@dataclass
Professional:
  id: int | None
  user_id: int          # FK → users.id, unique
  cedula: str           # 7-8 alphanumeric, unique
```

`Professional` intentionally has no `is_active`/`created_at`/`updated_at` — those live on `User` per spec clarification 1 & 2. Relationship is 1:1 via `user_id`.

### 3.2 Infrastructure ORM Models — `infrastructure/db/models/`

```sql
users (already migrated in T2):
  id integer PK autoincrement
  name varchar(100) NOT NULL
  last_name varchar(100) NOT NULL
  dni varchar(8) UNIQUE NOT NULL CHECK (dni ~ '^\d{8}$')
  email varchar(255) UNIQUE NOT NULL
  phone varchar(10) UNIQUE NOT NULL CHECK (phone ~ '^\d{10}$')
  password_hash varchar(255) NOT NULL
  role varchar(20) NOT NULL CHECK (role IN ('administrator','receptionist','professional'))
  is_active boolean NOT NULL DEFAULT true
  created_at timestamptz NOT NULL DEFAULT now()
  updated_at timestamptz NOT NULL DEFAULT now()  -- onupdate now()

professionals (existing from T2):
  id integer PK autoincrement
  user_id integer UNIQUE NOT NULL FK → users.id ON DELETE CASCADE
  cedula varchar(8) UNIQUE NOT NULL CHECK (cedula ~ '^[A-Za-z0-9]{7,8}$')
```

No new columns needed for 002; `updated_at` on `users` already satisfies requirement 2. Indexes: unique on `dni,email,phone,cedula` already provide uniqueness defense.

### 3.3 Application DTOs — `application/dtos/professional_dtos.py` (new) + `user_dtos.py` (existing)

```python
UpdateProfessionalRequest(BaseModel):
  name: str  # @field_validator: if missing/empty -> "Campos faltantes", else strip
  last_name: str
  dni: str  # regex ^\d{8}$ -> "Formato inválido, debe tener 8 caracteres"
  email: str  # contains "@" -> "email invalido", else lower
  phone: str  # ^\d{10}$ -> "Formato inválido, debe tener 10 caracteres"
  cedula: str  # ^[A-Za-z0-9]{7,8}$ -> "Formato inválido, debe tener 7 u 8 caracteres"
  # password intentionally absent per clarification 4

ProfessionalDetailResponse(BaseModel):
  id: int                 # professionals.id
  user_id: int
  cedula: str
  name: str
  last_name: str
  dni: str
  email: str
  phone: str
  role: UserRole
  is_active: bool
  created_at: datetime
  updated_at: datetime

  @classmethod from_entities(cls, user: User, professional: Professional) -> ...

ProfessionalListResponse(BaseModel):
  items: list[ProfessionalDetailResponse]
  count: int
```

Create DTOs remain in `user_dtos.py` (`CreateProfessionalRequest` includes password, `UserResponse` for legacy). Update reuses same validators for `Campos faltantes`.

## 4. Interface / API / Signature Contract

### 4.1 Repository Ports — `domain/repositories/`

```python
class ProfessionalRepository(ABC):
  def get_by_id(self, professional_id: int) -> Professional | None
  def get_by_user_id(self, user_id: int) -> Professional | None
  def get_by_cedula(self, cedula: str) -> Professional | None
  def list_active(self, search: str | None = None) -> list[tuple[User, Professional]]  # ordered A-Z
  def list_deactivated(self) -> list[tuple[User, Professional]]  # ordered A-Z, admin only
  def exists_by_cedula(self, cedula: str, exclude_user_id: int | None = None) -> bool
  def save(self, professional: Professional) -> Professional
  def delete(self, professional: Professional) -> None  # hard delete, caller deletes User separately or via cascade

class UserRepository(ABC) (existing, extended for updates):
  def get_by_id(self, user_id: int) -> User | None
  def exists_by_email(self, email: str, exclude_id: int | None = None) -> bool
  def exists_by_dni(self, dni: str, exclude_id: int | None = None) -> bool
  def exists_by_phone(self, phone: str, exclude_id: int | None = None) -> bool
  def save(self, user: User) -> User  # handles update via merge
  def delete(self, user: User) -> None
```

Note: `exclude_id` pattern enables update uniqueness checks excluding self.

### 4.2 Use Case Signatures — `application/use_cases/professional/`

```python
class ListProfessionalsUseCase:
  def __init__(self, professional_repo: ProfessionalRepository, user_repo: UserRepository)
  def execute(self, search: str | None = None) -> list[ProfessionalDetailResponse]
    # public, no auth, filters is_active=true, applies ILIKE on name/last_name/full name/cedula, order by name ASC

class ListDeactivatedProfessionalsUseCase:
  def __init__(self, professional_repo: ProfessionalRepository, user_repo: UserRepository)
  def execute(self, current_admin: User) -> list[ProfessionalDetailResponse]
    # raises ForbiddenException if not admin

class GetProfessionalByIdUseCase:
  def __init__(self, professional_repo: ProfessionalRepository, user_repo: UserRepository)
  def execute(self, professional_id: int) -> ProfessionalDetailResponse
    # raises ProfessionalNotFoundException -> 404

class UpdateProfessionalUseCase:
  def __init__(self, professional_repo: ProfessionalRepository, user_repo: UserRepository)
  def execute(self, professional_id: int, dto: UpdateProfessionalRequest, current_admin: User) -> ProfessionalDetailResponse

class DeleteProfessionalUseCase:
  def __init__(self, professional_repo: ProfessionalRepository, user_repo: UserRepository)
  def execute(self, professional_id: int, current_admin: User) -> None

class ActivateProfessionalUseCase:
  def __init__(self, professional_repo: ProfessionalRepository, user_repo: UserRepository)
  def execute(self, professional_id: int, current_admin: User) -> ProfessionalDetailResponse
    # if already active -> raise AlreadyActiveException("Profesional ya activado")

class DeactivateProfessionalUseCase:
  def __init__(self, professional_repo: ProfessionalRepository, user_repo: UserRepository)
  def execute(self, professional_id: int, current_admin: User) -> ProfessionalDetailResponse
    # if already inactive -> raise AlreadyInactiveException("Profesional ya desactivado")
```

Domain exceptions — `domain/exceptions/professional_exceptions.py`:
```python
ProfessionalNotFoundException("Professional Not Found") -> 404
AlreadyActiveException("Profesional ya activado") -> 409
AlreadyInactiveException("Profesional ya desactivado") -> 409
DuplicateEmailException("email ya registrado") -> 409 (reused)
DuplicateUserException("Usuario ya registrado") -> 409
MissingFieldsException("Campos faltantes") -> 400
```

### 4.3 HTTP API — `entrypoints/api/v1/routes/professional_router.py` (new)

```
GET /api/v1/professionals
  Auth: none (public)
  Query: ?search=<str> (optional, case-insensitive, matches name / last_name / full name / cedula)
  Success: 200 { items: [ProfessionalDetailResponse], count: int } ordered A-Z, only is_active=true

GET /api/v1/professionals/deactivated
  Auth: Bearer <admin_jwt> (Depends(get_current_admin))
  Success: 200 { items: [...] } only is_active=false, ordered A-Z
  Error: 401 Unauthorized, 403 Forbidden

GET /api/v1/professionals/{professional_id}
  Auth: none (public, returns active only; or 404 if inactive/non-existent)
  Success: 200 ProfessionalDetailResponse
  Error: 404 Professional Not Found

PUT /api/v1/professionals/{professional_id}
  Auth: Bearer <admin_jwt>
  Body: UpdateProfessionalRequest (no password)
  Success: 200 ProfessionalDetailResponse
  Error: 400 Campos faltantes, 422 email invalido/Formato inválido..., 409 email ya registrado/Usuario ya registrado, 404 Professional Not Found, 401/403

DELETE /api/v1/professionals/{professional_id}
  Auth: Bearer <admin_jwt>
  Success: 204 No Content
  Error: 404 Professional Not Found, 401/403

PATCH /api/v1/professionals/{professional_id}/activate
  Auth: Bearer <admin_jwt>
  Success: 200 ProfessionalDetailResponse (now is_active=true)
  Error: 404, 409 Profesional ya activado, 401/403

PATCH /api/v1/professionals/{professional_id}/deactivate
  Auth: Bearer <admin_jwt>
  Success: 200 ProfessionalDetailResponse (now is_active=false)
  Error: 404, 409 Profesional ya desactivado, 401/403
```

Existing `POST /api/v1/users/professionals` and `POST /api/v1/users/receptionists` remain in `user_router.py` for creation (admin only). No duplication.

Dependency injection — `entrypoints/api/v1/dependencies.py` (extend existing):
```python
def get_professional_repository(db=Depends(get_db)) -> ProfessionalRepository: ...
def get_list_professionals_use_case(...): ...
def get_update_professional_use_case(...): ...  # etc for each use case
def get_current_admin(...)  # already exists, reused
```

### 4.4 Auth / Login Contract (unchanged)

`POST /api/v1/auth/login` with `{"name":"Gabriel Cari","password":"gabi12345"}` → checks `users.is_active` (new: login must reject inactive professionals with 401). This is already enforced via `User.is_active` check in auth flow; plan explicitly adds that check.

## 5. Core Algorithms / Logic — Pseudocode

### 5.1 List Active Professionals (public, search, order)

```python
function list_active(search: str | None):
  base_query = SELECT User, Professional JOIN ON Professional.user_id = User.id
               WHERE User.role='professional' AND User.is_active=true

  if search is not None and search.strip() != "":
    term = "%" + search.strip().lower() + "%"
    base_query = base_query.WHERE(
      LOWER(User.name) ILIKE term OR
      LOWER(User.last_name) ILIKE term OR
      LOWER(User.name || ' ' || User.last_name) ILIKE term OR
      LOWER(Professional.cedula) ILIKE term
    )

  base_query = base_query.ORDER_BY(LOWER(User.name) ASC, LOWER(User.last_name) ASC)
  return [ProfessionalDetailResponse.from_entities(u,p) for u,p in base_query.all()]
```

No pagination in this iteration; returns all matches.

### 5.2 List Deactivated (admin only)

```python
function list_deactivated(current_admin):
  if current_admin.role != ADMINISTRATOR: raise Forbidden
  query = same JOIN WHERE is_active=false ORDER BY LOWER(User.name) ASC
  return mapped list
```

### 5.3 Get By Id

```python
function get_by_id(professional_id):
  professional = professional_repo.get_by_id(professional_id)
  if not professional: raise ProfessionalNotFound
  user = user_repo.get_by_id(professional.user_id)
  if not user: raise ProfessionalNotFound  # orphan
  # public endpoint: if not user.is_active -> raise 404 (or return but hidden? spec says only active visible publicly)
  return ProfessionalDetailResponse.from_entities(user, professional)
```

### 5.4 Update Professional

```python
function update(professional_id, dto, current_admin):
  if current_admin.role != ADMINISTRATOR: raise Forbidden
  professional = professional_repo.get_by_id(professional_id) or raise NotFound
  user = user_repo.get_by_id(professional.user_id) or raise NotFound

  # completeness already handled by DTO (Campos faltantes)
  # uniqueness excluding self
  if user_repo.exists_by_email(dto.email, exclude_id=user.id): raise DuplicateEmail("email ya registrado")
  if user_repo.exists_by_dni(dto.dni, exclude_id=user.id): raise DuplicateUser("Usuario ya registrado")
  if user_repo.exists_by_phone(dto.phone, exclude_id=user.id): raise DuplicateUser
  if professional_repo.exists_by_cedula(dto.cedula, exclude_user_id=user.id): raise DuplicateUser

  # update fields (password not present)
  user.name = dto.name.strip()
  user.last_name = dto.last_name.strip()
  user.dni = dto.dni
  user.email = dto.email.lower()
  user.phone = dto.phone
  user.updated_at = now()
  professional.cedula = dto.cedula

  user = user_repo.save(user)               # handles update via merge
  professional = professional_repo.save(professional)
  return ProfessionalDetailResponse.from_entities(user, professional)
```

### 5.5 Delete Professional (hard delete)

```python
function delete(professional_id, current_admin):
  if not admin: raise Forbidden
  professional = professional_repo.get_by_id(professional_id) or raise NotFound
  user = user_repo.get_by_id(professional.user_id) or raise NotFound
  # hard delete both; rely on ON DELETE CASCADE by deleting user, or delete professional first
  professional_repo.delete(professional)
  user_repo.delete(user)
  # alternative: user_repo.delete(user) alone cascades
  return None  # 204
```

### 5.6 Activate / Deactivate

```python
function activate(professional_id, current_admin):
  if not admin: raise Forbidden
  professional = get_or_404(professional_id)
  user = user_repo.get_by_id(professional.user_id)
  if user.is_active: raise AlreadyActive("Profesional ya activado")
  user.is_active = True
  user_repo.save(user)
  return DetailResponse

function deactivate(professional_id, current_admin):
  if not admin: raise Forbidden
  professional = get_or_404(professional_id)
  user = user_repo.get_by_id(professional.user_id)
  if not user.is_active: raise AlreadyInactive("Profesional ya desactivado")
  user.is_active = False
  user_repo.save(user)
  return DetailResponse
```

Login must check `if not user.is_active: raise 401` to enforce "cannot log in when inactive".

### 5.7 Validation Mapping (DTO → HTTP)

Pydantic `field_validator` raises `ValueError("Campos faltantes")` / `"email invalido"` / `"Formato inválido..."` etc. `RequestValidationError` handler in `main.py` maps:
- `type == "missing"` → 400 `Campos faltantes`
- message contains `"Campos faltantes"` → 400
- `"email invalido"` → 422
- `"Formato inválido"` → 422
- Domain exceptions mapped in router: `DuplicateEmail`→409, `DuplicateUser`→409, `ProfessionalNotFound`→404, `AlreadyActive/Inactive`→409, `Forbidden`→403.

## 6. Key Technical Decisions and Alternatives Discarded

| Decision | Chosen Approach | Why | Alternative Discarded | Reason Discarded |
|---|---|---|---|---|
| **1. Search implementation** | PostgreSQL `ILIKE` with `LOWER()` on `users.name`, `last_name`, `name || ' ' || last_name`, and `professionals.cedula`, in a single JOIN query, ordered by `LOWER(name) ASC`. | Case-insensitive per clarification 3, returns multiple matches, supports partial match, no extra dependency. | Full-text search (`tsvector`) or separate search service (Elasticsearch) | Over-engineering for no-pagination active list; ILIKE sufficient for <10k rows. |
| **2. Ordering** | `ORDER BY LOWER(users.name) ASC, LOWER(users.last_name) ASC` at DB level for both active and deactivated lists. | Guarantees alphabetical A-Z per clarification 2, deterministic, efficient with index. | Application-side sorting after fetch | Less efficient, non-deterministic for large lists, duplicates sorting logic. |
| **3. Auth for listing** | Public `GET /professionals` and `GET /professionals/{id}` with no `Depends(get_current_admin)`; `GET /professionals/deactivated` requires admin. | Matches clarification 1 & 5: public visibility for active, admin-only for deactivated to retrieve IDs. | Require auth for all lists | Contradicts clarified requirement that any user can list without login. |
| **4. Password on update** | Exclude `password` from `UpdateProfessionalRequest` entirely; hash only on create in `BcryptPasswordService`. | Per clarification 4, password not editable in this iteration, avoids accidental overwrite and simplifies validation. | Allow optional password on update with same 8-char rule | Adds complexity, requires conditional hashing, not requested. |
| **5. Hard delete vs soft delete** | Hard delete both `professionals` and `users` rows (`DELETE`); `ON DELETE CASCADE` as safety net, but use case deletes both explicitly for clarity. | Spec says "Se elimina el registro de professionals como el users vinculado" — physical deletion, not just `is_active=false`. | Soft delete only (`is_active=false` and keep row) | Would leave orphan professional data and violate hard-delete requirement; already have separate deactivate flow. |
| **6. Transaction for create/update** | Use same SQLAlchemy `Session` for both repos; `save` does `add` + `flush` + `commit` at use-case level (or rely on two commits with `exists` check beforehand). For 002, keep `exists` check before save to avoid race, DB unique constraints as defense. | Ensures atomic creation of `users`+`professionals`; prevents partial professional without user. | Separate transactions per repo | Risk of orphan user if professional save fails (e.g., duplicate cedula race). |
| **7. Uniqueness on update (exclude self)** | Repository methods `exists_by_email(email, exclude_id)` etc., implemented as `WHERE email = :email AND id != :exclude_id`. | Prevents false positive when admin keeps same email/dni/phone/cedula on update. | Naive `exists_by_*` without exclusion | Would incorrectly reject updates that don't change unique fields. |
| **8. Response shape** | Separate `ProfessionalDetailResponse` (joins User+Professional) for all professional reads; `UserResponse` remains for receptionist endpoints. | Avoids reintroducing `cedula` into `users`, keeps domain separation, provides full detail (including `is_active`, `created_at`, `updated_at`). | Reuse `UserResponse` with nullable `cedula` | Reintroduces removed column conceptually, blurs bounded contexts. |
| **9. Login inactive handling** | `auth_router` login checks `if not user.is_active: raise 401` after password verify. | Enforces spec "se impide su login a menos que el administrador lo active". | Allow inactive login with limited scope | Violates spec, security risk. |
| **10. No pagination** | Return all matching rows in one response (`{items, count}`) with no `limit/offset` params in this iteration. | Per clarification 2, pagination deferred; simplifies frontend. | Add `page`/`size` now | Premature, spec says will be added later. |

## 7. Test Strategy

### 7.1 Unit Tests (fast, no DB, mocked repos)

- **DTO tests** `tests/application/test_professional_dtos.py`:
  - `UpdateProfessionalRequest` missing/empty → `Campos faltantes`
  - Invalid email/dni/phone/cedula → `email invalido` / `Formato inválido...`
  - Valid payload passes; ensure password field absent (sending password → validation error)
- **Use case tests** (mocked `UserRepository`, `ProfessionalRepository`):
  - `test_list_professionals.py`: search `"ana"` case-insensitive returns multiple, empty search returns all ordered A-Z, only `is_active=true` returned
  - `test_list_deactivated_professionals.py`: admin returns deactivated, non-admin → Forbidden
  - `test_get_professional_by_id.py`: found → response, not found → `ProfessionalNotFound`
  - `test_update_professional.py`: success updates both tables, duplicate email/dni/phone/cedula excluding self → `Duplicate*`, not found → 404, non-admin → 403
  - `test_delete_professional.py`: success hard deletes both, not found → 404, verify `users` row also gone
  - `test_activate_professional.py`: inactive → active, already active → `Profesional ya activado`, not found → 404
  - `test_deactivate_professional.py`: active → inactive (blocks login), already inactive → `Profesional ya desactivado`

### 7.2 Integration Tests (with Test DB via `docker compose exec api`)

- **Repository tests** `tests/infrastructure/test_postgres_professional_repository.py` (extended):
  - Save professional, `exists_by_cedula` true, `get_by_user_id`, `list_active` with `ILIKE` search, `list_deactivated`, hard delete cascade, `updated_at` auto-touched on user save
- **Seed & model tests**: Verify `users.updated_at` changes on update, `professionals` FK cascade on user delete

### 7.3 API Integration Tests (FastAPI `TestClient`, `docker compose exec api`)

- **Public list tests** `tests/entrypoints/test_professional_router.py`:
  - `GET /professionals` without token → 200, items ordered A-Z, only active, search `?search=ana` case-insensitive returns multiple, search by cedula, empty result 200 with empty list
  - `GET /professionals/{id}` public without token → 200 for active, 404 for inactive/non-existent
  - `GET /professionals/deactivated` without token → 401, with receptionist token → 403, with admin token → 200 with deactivated items
  - `PUT /professionals/{id}` with admin token → 200, validates `Campos faltantes` (400), invalid formats (422), duplicate email (409 `email ya registrado`), duplicate cedula (409 `Usuario ya registrado`), not found (404), non-admin (403), sending password → 422 (field not allowed)
  - `DELETE /professionals/{id}` admin → 204, verify `SELECT * FROM users WHERE id=:id` gone and `professionals` gone; not found → 404
  - `PATCH /professionals/{id}/activate` and `/deactivate` admin → 200, idempotent errors 409 with `Profesional ya activado/desactivado`, verify login blocked after deactivate (`POST /auth/login` with deactivated professional → 401)
  - Verify `.env` not exposed, `is_active` toggling persists

### 7.4 Linter, Type, and Coverage Gates (Definition of Done)

- **Linter**: `docker compose exec api ruff check app/` + `ruff format --check` → 0 errors (PEP8)
- **Type check**: `docker compose exec api python -m mypy app/domain app/application --ignore-missing-imports` → 0 errors (domain remains pure, no FastAPI/SQLAlchemy imports)
- **Coverage**: `docker compose exec api pytest --cov=app --cov-report=term-missing` → ≥80% `domain`+`application`, ≥60% `infrastructure`
- **Security**: `grep -R "gabi12345" app/` only in `seed`/`settings`, `.env` in `.gitignore`, `is_active` check in `auth_router`

### 7.5 Test Data and Fixtures

- Factory `professional_payload(name="Ana", cedula="ABC1234")`, `deactivated_professional_payload()`
- Fixture `admin_headers()` → JWT for `NAME=Gabriel Cari` via `create_access_token({"sub":"admin@centro.local","role":"administrator"})`
- Fixture `public_client` (no auth) vs `admin_client` (with bearer)
- DB fixture: `Base.metadata.drop_all/create_all` with both `UserModel` and `ProfessionalModel` imported, `ensure_admin_exists` before each test, transactional rollback or truncate `professionals`/`users` where `role='professional'` between tests to keep `admin id=1`

### 7.6 Out of Scope for This Iteration

- Pagination (`?page=&size=`) and total count header — deferred per clarification 2
- Password change endpoint for professionals — deferred per clarification 4
- Frontend React pages for professional CRUD — backend only in this plan; contract defined for future `AdminProfessionalsPage`

