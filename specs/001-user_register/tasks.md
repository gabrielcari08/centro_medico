# Tasks — User Registration (001-user_register)

> Ordered strictly by technical dependencies. Each task is 20-30 min. Complete in sequence — do not skip.
> References: `spec.md` Scenarios WS-1/WS-2, BF-1..BF-10 and Business Rules; `plan.md` §1-§7; `AGENT.md` Clean Architecture.

---

### Phase 0 — Scaffolding & Tooling

#### Task 0.1: Initialize Clean Architecture skeleton and dependencies
**Requirements:** Unblocks all layers; respects `AGENT.md` structure.
**Files to create/touch:**
- `app/__init__.py`, `app/domain/__init__.py`, `app/domain/entities/__init__.py`, `app/domain/repositories/__init__.py`, `app/domain/services/__init__.py`, `app/domain/exceptions/__init__.py`
- `app/application/__init__.py`, `app/application/dtos/__init__.py`, `app/application/use_cases/__init__.py`, `app/application/use_cases/user/__init__.py`
- `app/infrastructure/__init__.py`, `app/infrastructure/config/__init__.py`, `app/infrastructure/db/__init__.py`, `app/infrastructure/db/models/__init__.py`, `app/infrastructure/db/seed/__init__.py`, `app/infrastructure/repositories/__init__.py`, `app/infrastructure/services/__init__.py`
- `app/entrypoints/__init__.py`, `app/entrypoints/api/__init__.py`, `app/entrypoints/api/v1/__init__.py`, `app/entrypoints/api/v1/routes/__init__.py`
- `requirements.txt` (add `fastapi`, `uvicorn`, `sqlalchemy`, `psycopg2-binary`, `pydantic`, `pydantic-settings`, `passlib[bcrypt]`, `python-jose`, `pytest`, `httpx`, `ruff`, `mypy`)
- `tests/__init__.py`, `tests/domain/__init__.py`, `tests/application/__init__.py`, `tests/infrastructure/__init__.py`, `tests/entrypoints/__init__.py`
**Checkboxes:**
- [ ] Create all `__init__.py` and folders exactly as `plan.md §2`
- [ ] Add dependencies to `requirements.txt`
- [ ] Verify `python -c "import app"` succeeds
**Done when:** `bash: ls app/domain/entities app/application/dtos app/infrastructure/db/models app/entrypoints/api/v1/routes` lists all folders; `pip install -r requirements.txt` exits 0.

#### Task 0.2: Configure Settings and database session
**Requirements:** Admin provisioning via `.env` at project root (`NAME=Gabriel Cari`, `PASSWORD=gabi12345`), single admin; `DATABASE_URL` from docker-compose.
**Files to create/touch:**
- `app/infrastructure/config/settings.py`
- `app/infrastructure/db/base.py`
- `app/infrastructure/db/session.py`
- `.env` (already exists — verify not overwritten)
**Checkboxes:**
- [ ] Implement `Settings(BaseSettings)` with `NAME`, `PASSWORD`, `DATABASE_URL`, `SECRET_KEY`, `env_file=".env"`
- [ ] Implement `Base = declarative_base()` and `get_session()` / `SessionLocal`
- [ ] Ensure `.env` is in `.gitignore` (already present — verify)
**Done when:** `bash: python -c "from app.infrastructure.config.settings import Settings; s=Settings(); assert s.NAME=='Gabriel Cari'; assert s.PASSWORD=='gabi12345'"` passes; `bash: python -c "from app.infrastructure.db.session import SessionLocal; print('ok')"` passes.

---

### Phase 1 — Domain Layer (zero framework imports)

#### Task 1.1: Create User entity and UserRole enum
**Requirements:** WS-1, WS-2, Business Rules — required fields, cedula only for Professional, `is_active=True`, role assignment.
**Files to create/touch:**
- `app/domain/entities/user.py`
**Checkboxes:**
- [ ] Define `UserRole` enum (`ADMINISTRATOR`, `RECEPTIONIST`, `PROFESSIONAL`) — English names, string values
- [ ] Define `@dataclass User` with fields: `id`, `name`, `last_name`, `dni`, `email`, `phone`, `password_hash`, `role`, `cedula`, `is_active`, `created_at`
- [ ] Add `__post_init__` invariants: `PROFESSIONAL ↔ cedula is not None`, strip non-empty checks (no Pydantic/SQLAlchemy imports)
**Done when:** `bash: pytest tests/domain/test_user_entity.py -k test_invariants -v` passes (create minimal test file to verify `User(role=RECEPTIONIST, cedula="ABC1234")` raises, `User(role=PROFESSIONAL, cedula=None)` raises, `User(is_active=True)` default).

#### Task 1.2: Define domain exceptions
**Requirements:** BF-1..BF-10 error literals — `email ya registrado`, `Usuario ya registrado`, `Campos faltantes`, `email invalido`, `Formato inválido...`, `La contraseña debe tener al menos 8 caracteres`.
**Files to create/touch:**
- `app/domain/exceptions/user_exceptions.py`
**Checkboxes:**
- [ ] Create `DuplicateEmailException`, `DuplicateUserException`, `MissingFieldsException`, `InvalidFormatException`, `PasswordTooShortException`, `UnauthorizedException`, `ForbiddenException` (each with spec literal as default message)
**Done when:** `bash: python -c "from app.domain.exceptions.user_exceptions import DuplicateEmailException; assert str(DuplicateEmailException())=='email ya registrado'"` passes.

#### Task 1.3: Define repository and service ports (ABC)
**Requirements:** Uniqueness checks (BF-1..BF-4), password hashing; enables dependency inversion.
**Files to create/touch:**
- `app/domain/repositories/user_repository.py`
- `app/domain/services/password_service.py`
**Checkboxes:**
- [ ] Define `UserRepository(ABC)` with `get_by_email`, `get_by_dni`, `get_by_phone`, `get_by_cedula`, `exists_by_email`, `exists_by_dni`, `exists_by_phone`, `exists_by_cedula`, `save`, `exists_by_role` (for admin seed)
- [ ] Define `PasswordService(ABC)` with `hash(plain) -> str` and `verify(plain, hashed) -> bool`
**Done when:** `bash: python -c "from app.domain.repositories.user_repository import UserRepository; from app.domain.services.password_service import PasswordService; print('ports ok')"` passes; `mypy app/domain --ignore-missing-imports` passes.

---

### Phase 2 — Infrastructure: DB Model & Services

#### Task 2.1: Create SQLAlchemy User model
**Requirements:** Single `users` table with unique constraints, CHECKs for `dni ^\d{8}$`, `phone ^\d{10}$`, `cedula ^[A-Za-z0-9]{7,8}$`, role enum.
**Files to create/touch:**
- `app/infrastructure/db/models/user_model.py`
- `app/infrastructure/db/base.py` (register model)
**Checkboxes:**
- [ ] Implement `UserModel(Base)` with columns: `id UUID PK`, `name`, `last_name`, `dni UNIQUE`, `email UNIQUE`, `phone UNIQUE`, `password_hash`, `role`, `cedula UNIQUE NULL`, `is_active DEFAULT TRUE`, `created_at TIMESTAMPTZ`
- [ ] Add `CHECK` constraints and partial unique index for `cedula`
**Done when:** `bash: docker compose up db -d && python -c "from app.infrastructure.db.base import Base; from app.infrastructure.db.session import engine; Base.metadata.create_all(engine); print('tables created')"` exits 0; `bash: psql $DATABASE_URL -c "\d users"` shows table.

#### Task 2.2: Implement bcrypt password service
**Requirements:** Password hashing (Business Rule: min 8 chars validated elsewhere, hash here), security (AGENT.md).
**Files to create/touch:**
- `app/infrastructure/services/bcrypt_password_service.py`
**Checkboxes:**
- [ ] Implement `BcryptPasswordService(PasswordService)` using `passlib.context.CryptContext(schemes=["bcrypt"])`
- [ ] Implement `hash` and `verify`
**Done when:** `bash: pytest tests/infrastructure/test_bcrypt_service.py -v` passes — test hashes `gabi12345` and verifies `verify("gabi12345", hash) is True` and `verify("wrong", hash) is False`.

#### Task 2.3: Implement Postgres user repository
**Requirements:** BF-1..BF-4 uniqueness, WS-1/WS-2 persistence, ORM ↔ entity mapping.
**Files to create/touch:**
- `app/infrastructure/repositories/postgres_user_repository.py`
**Checkboxes:**
- [ ] Implement all `UserRepository` methods mapping `UserModel <-> User` entity
- [ ] Handle `IntegrityError` → re-raise as domain exception (defense in depth)
**Done when:** `bash: pytest tests/infrastructure/test_postgres_user_repository.py -v` passes — tests: `save` then `exists_by_email` true, `exists_by_dni` true, duplicate insert raises mapped exception; `docker compose exec db psql -U postgres -d app_db -c "SELECT count(*) FROM users"` works.

#### Task 2.4: Implement admin seed (single admin)
**Requirements:** Admin provisioning via `.env` (`NAME=Gabriel Cari`, `PASSWORD=gabi12345`), only one admin, not in repo.
**Files to create/touch:**
- `app/infrastructure/db/seed/admin_seed.py`
**Checkboxes:**
- [ ] Implement `ensure_admin_exists(session, settings, user_repo, pwd_service)` — split `NAME` into `name`/`last_name`, synthesize `email=admin@centro.local`, `dni=00000000`, `phone=0000000000`, hash `PASSWORD`, save if no admin exists, idempotent
- [ ] Wire to FastAPI lifespan in `app/entrypoints/api/v1/main.py` (create stub if not exists)
**Done when:** `bash: pytest tests/infrastructure/test_admin_seed.py -v` passes — first call creates admin, second call does not duplicate, `exists_by_role(ADMINISTRATOR)` true; `bash: python -c "from app.infrastructure.db.seed.admin_seed import ensure_admin_exists; print('seed ok')"` passes.

---

### Phase 3 — Application Layer: DTOs

#### Task 3.1: Create receptionist and professional DTOs with Pydantic validation
**Requirements:** BF-5..BF-10, `Campos faltantes`, `email invalido`, `Formato inválido...`, `La contraseña...`, completeness and format.
**Files to create/touch:**
- `app/application/dtos/user_dtos.py`
**Checkboxes:**
- [ ] Implement `CreateReceptionistRequest` with `name`, `last_name` (strip, min 1), `dni` pattern `^\d{8}$` error `Formato inválido, debe tener 8 caracteres`, `email` EmailStr custom message `email invalido`, `phone` pattern `^\d{10}$`, `password` min 8 error `La contraseña debe tener al menos 8 caracteres`
- [ ] Implement `CreateProfessionalRequest` extending above + `cedula` pattern `^[A-Za-z0-9]{7,8}$` error `Formato inválido, debe tener 7 u 8 caracteres`
- [ ] Implement `UserResponse` with `from_entity` mapper
- [ ] Ensure missing/empty field triggers `Campos faltantes` via validator
**Done when:** `bash: pytest tests/application/test_user_dtos.py -v` passes — 10+ cases: missing field → `Campos faltantes`, email without `@` → `email invalido`, dni `123` → `Formato inválido, debe tener 8 caracteres`, phone `123` → `Formato inválido, debe tener 10 caracteres`, cedula `abc` → `Formato inválido, debe tener 7 u 8 caracteres`, password `short` → `La contraseña debe tener al menos 8 caracteres`, valid payload passes.

---

### Phase 4 — Application Layer: Use Cases

#### Task 4.1: Create CreateReceptionist use case
**Requirements:** WS-1, BF-1, BF-2, BF-3, BF-5, BF-6, uniqueness and active status.
**Files to create/touch:**
- `app/application/use_cases/user/create_receptionist.py`
**Checkboxes:**
- [ ] Inject `UserRepository` + `PasswordService`
- [ ] Implement `execute(dto)` — checks in order: `exists_by_email` → `DuplicateEmailException("email ya registrado")`, `exists_by_dni`/`exists_by_phone` → `DuplicateUserException("Usuario ya registrado")`, hash password, create `User(role=RECEPTIONIST, is_active=True)`, save
**Done when:** `bash: pytest tests/application/test_create_receptionist.py -v` passes — mocks: success returns active user with hashed password; duplicate email/dni/phone raise correct exceptions; `pwd_service.hash` called once.

#### Task 4.2: Create CreateProfessional use case
**Requirements:** WS-2, BF-4, plus all receptionist rules, cedula uniqueness/format.
**Files to create/touch:**
- `app/application/use_cases/user/create_professional.py`
**Checkboxes:**
- [ ] Same injection, check `exists_by_email` first, then `dni`/`phone`/`cedula` → `Usuario ya registrado`, hash, create `User(role=PROFESSIONAL, cedula=dto.cedula)`
**Done when:** `bash: pytest tests/application/test_create_professional.py -v` passes — success with cedula `ABC1234` (7) and `12345678` (8); duplicate cedula raises; missing cedula fails at DTO level (no use case test needed).

---

### Phase 5 — Entrypoints: API & Auth

#### Task 5.1: Create FastAPI app, dependencies, and auth
**Requirements:** Exclusive creation right (admin only), JWT login via `.env` credentials, security (AGENT.md).
**Files to create/touch:**
- `app/entrypoints/api/v1/main.py`
- `app/entrypoints/api/v1/dependencies.py`
**Checkboxes:**
- [ ] Implement `main.py` with `FastAPI(title="Centro Médico")`, lifespan calling `ensure_admin_exists`, include router
- [ ] Implement `get_db_session`, `get_user_repository`, `get_password_service`, `get_current_admin` (verify JWT, check `role==ADMINISTRATOR` → 401/403), `get_create_receptionist_use_case`, `get_create_professional_use_case`
- [ ] Implement `POST /api/v1/auth/login` logic (compare against admin row or `.env` fallback, return JWT via `python-jose`)
**Done when:** `bash: pytest tests/entrypoints/test_auth.py -v` passes — login with `NAME=Gabriel Cari` / `PASSWORD=gabi12345` → 200 + token; wrong password → 401; `get_current_admin` with receptionist token → 403; `bash: curl -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"name":"Gabriel Cari","password":"gabi12345"}'` returns `access_token` when stack running.

#### Task 5.2: Create user router with two endpoints
**Requirements:** WS-1, WS-2, BF-1..BF-10 HTTP mapping (400/409/422/201), OpenAPI docs.
**Files to create/touch:**
- `app/entrypoints/api/v1/routes/user_router.py`
**Checkboxes:**
- [ ] Implement `POST /api/v1/users/receptionists` → 201 `UserResponse`, map `DuplicateEmailException`→409 `email ya registrado`, `DuplicateUserException`→409 `Usuario ya registrado`, `ValidationError` missing→400 `Campos faltantes`, format errors→422 with spec literals
- [ ] Implement `POST /api/v1/users/professionals` similarly with cedula
- [ ] Require `Depends(get_current_admin)` on both
**Done when:** `bash: pytest tests/entrypoints/test_user_router.py -v` passes — 12 cases: valid receptionist/professional →201; duplicate email→409 `email ya registrado`; duplicate dni/phone/cedula→409 `Usuario ya registrado`; missing field→400 `Campos faltantes`; invalid email→422 `email invalido`; invalid dni/phone→422 `Formato inválido, debe tener 8/10 caracteres`; invalid cedula→422 `Formato inválido, debe tener 7 u 8 caracteres`; password short→422 `La contraseña debe tener al menos 8 caracteres`; non-admin→403.

---

### Phase 6 — Integration & Verification

#### Task 6.1: Wire docker-compose env and run full-stack smoke
**Requirements:** `.env` at project root, `DATABASE_URL`, `SECRET_KEY` passed to `api` service, hot-reload.
**Files to create/touch:**
- `docker-compose.yml` (verify `env_file` or `environment` includes `NAME`, `PASSWORD`, `SECRET_KEY`)
- `.env` (verify `NAME=Gabriel Cari`, `PASSWORD=gabi12345`, add `SECRET_KEY` if missing)
**Checkboxes:**
- [ ] Ensure `api` service reads `.env` via `env_file` or interpolates `DATABASE_URL`
- [ ] Run `docker compose up --build -d` and hit `GET /docs`
**Done when:** `bash: docker compose up --build -d && sleep 5 && curl -f http://localhost:8000/docs` returns 200; `bash: docker compose logs api | grep "Admin seeded"` shows seed executed.

#### Task 6.2: Linter, type-check, and coverage gates
**Requirements:** AGENT.md Definition of Done — linter, unit tests, spec.md updated.
**Files to create/touch:**
- `pyproject.toml` or `ruff.toml` (if not exists)
- All `app/` files
**Checkboxes:**
- [ ] Run `ruff check app/ && ruff format --check app/` → 0 errors
- [ ] Run `mypy app/domain app/application --ignore-missing-imports` → 0 errors
- [ ] Run `pytest --cov=app --cov-report=term-missing` → ≥80% domain+application, ≥60% infrastructure
**Done when:** `bash: ruff check app/` exits 0; `bash: mypy app/domain app/application` exits 0; `bash: pytest --cov=app` shows coverage above thresholds.

#### Task 6.3: End-to-end manual verification via curl and React stub
**Requirements:** Full flow WS-1/WS-2 as admin, verify all BF error messages visible.
**Files to create/touch:**
- `frontend/src/pages/AdminCreateUserPage.jsx` (optional stub — not required for backend done)
- `frontend/src/components/UserCreateForm.jsx` (optional)
**Checkboxes:**
- [ ] Login as admin, create receptionist with valid payload → 201
- [ ] Create professional with cedula → 201
- [ ] Attempt duplicate email → observe `email ya registrado`
- [ ] Attempt invalid dni/phone/cedula → observe `Formato inválido...`
- [ ] Verify `.env` never returned in any response (`grep -r "gabi12345" app/` → 0 hits except seed)
**Done when:** `bash: ./scripts/e2e.sh` (or manual curl sequence) executes all 10 BF scenarios and prints spec literals; `bash: grep -R "gabi12345" app/ --exclude="*.pyc"` shows only `seed` and `settings` usage, no hard-coded secret in routes.

---

### Task Completion Checklist (for tracking)

- [ ] 0.1 Scaffolding & dependencies
- [ ] 0.2 Settings & DB session
- [ ] 1.1 User entity & role
- [ ] 1.2 Domain exceptions
- [ ] 1.3 Repository/service ports
- [ ] 2.1 SQLAlchemy user model
- [ ] 2.2 Bcrypt service
- [ ] 2.3 Postgres repository
- [ ] 2.4 Admin seed
- [ ] 3.1 DTOs with validation
- [ ] 4.1 CreateReceptionist use case
- [ ] 4.2 CreateProfessional use case
- [ ] 5.1 FastAPI app & auth deps
- [ ] 5.2 User router endpoints
- [ ] 6.1 Docker smoke
- [ ] 6.2 Linter/type/coverage
- [ ] 6.3 E2E verification

> Total: 17 tasks × ~25 min ≈ 7 hours. Execute strictly in order; each phase's `Done when` must pass before starting next.
