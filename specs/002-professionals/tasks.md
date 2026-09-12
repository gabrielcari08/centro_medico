# Tasks — Professionals CRUD (002-professionals)

> Ordered strictly by technical dependencies. Each task is 20-30 min. Complete in sequence — do not skip.
> References: `spec.md` WS-1..WS-8, BF-1..BF-13; `plan.md` §1-§7; `AGENT.md` Clean Architecture.
> Execution via Docker-first: all verifications run inside `api` container (`docker compose exec api ...`), `db` via `docker compose exec db`.

---

### Phase 1 — Domain & DTO Foundations

#### Task 1.1: Create ProfessionalDetail DTOs and UpdateProfessionalRequest

**Requirements:** WS-5, BF-1..BF-5, BF-7..BF-8; editable fields on update (name, last_name, dni, email, phone, cedula), password not editable; completeness/format messages `Campos faltantes`, `email invalido`, `Formato inválido...`.
**Files to create/touch:**

- `app/application/dtos/professional_dtos.py`
  **Checkboxes:**
- [x] Create `UpdateProfessionalRequest` with `name`, `last_name`, `dni` (`^\d{8}$`), `email` (contains `@`), `phone` (`^\d{10}$`), `cedula` (`^[A-Za-z0-9]{7,8}$`) — each `@field_validator` raises spec literals; strip + case handling; ensure no `password` field (sending password → validation error)
- [x] Create `ProfessionalDetailResponse` with `id`, `user_id`, `cedula`, `name`, `last_name`, `dni`, `email`, `phone`, `role`, `is_active`, `created_at`, `updated_at` + `from_entities(user, professional)` mapper
- [x] Create `ProfessionalListResponse` with `items: list[ProfessionalDetailResponse]` and `count: int`
      **Done when:** `docker compose exec api pytest tests/application/test_professional_dtos.py -v` passes — 10 cases: missing field → `Campos faltantes`, email without `@` → `email invalido`, dni `123` → `Formato inválido, debe tener 8 caracteres`, phone `123` → `Formato inválido, debe tener 10 caracteres`, cedula `abc` → `Formato inválido, debe tener 7 u 8 caracteres`, valid payload passes, password field rejected.

#### Task 1.2: Extend ProfessionalRepository port with list/search/delete and UserRepository with exclude_id + delete

**Requirements:** WS-2, WS-4, BF-8 (uniqueness excluding self), BF-9, hard delete.
**Files to create/touch:**

- `app/domain/repositories/professional_repository.py`
- `app/domain/repositories/user_repository.py`
  **Checkboxes:**
- [x] Add `get_by_id`, `list_active(search: str|None) -> list[tuple[User,Professional]]`, `list_deactivated()`, `delete(professional)`, and `exists_by_cedula(cedula, exclude_user_id)` to `ProfessionalRepository`
- [x] Add `exists_by_email/dni/phone(..., exclude_id)` and `delete(user)`, `get_by_id` with `exclude_id` pattern to `UserRepository` (if not already with exclude_id, add overload)
- [x] Ensure domain layer still has zero framework imports (`ABC`, `dataclass`, `Enum` only)
      **Done when:** `docker compose exec api python -c "from app.domain.repositories.professional_repository import ProfessionalRepository; from app.domain.repositories.user_repository import UserRepository; print('ports ok')"` passes; `docker compose exec api python -m mypy app/domain --ignore-missing-imports` → Success.

#### Task 1.3: Define professional domain exceptions for not-found and idempotent activate

**Requirements:** BF-9, BF-10, BF-11; WS-6, WS-7.
**Files to create/touch:**

- `app/domain/exceptions/professional_exceptions.py`
  **Checkboxes:**
- [x] Ensure `ProfessionalNotFoundException("Professional Not Found")`, `AlreadyActiveException("Profesional ya activado")`, `AlreadyInactiveException("Profesional ya desactivado")` exist (reuse `DuplicateEmailException`/`DuplicateUserException` for uniqueness)
      **Done when:** `docker compose exec api python -c "from app.domain.exceptions.professional_exceptions import ProfessionalNotFoundException, AlreadyActiveException; assert str(ProfessionalNotFoundException())=='Professional Not Found'; assert str(AlreadyActiveException())=='Profesional ya activado'"` passes.

---

### Phase 2 — Infrastructure Repository Enhancements

#### Task 2.1: Implement list/search/delete in PostgresProfessionalRepository

**Requirements:** WS-2, WS-4, BF-8, alphabetical A-Z, case-insensitive search by name/last_name/full name/cedula.
**Files to create/touch:**

- `app/infrastructure/repositories/postgres_professional_repository.py`
  **Checkboxes:**
- [ ] Implement `list_active(search)`: `JOIN users ON professionals.user_id=users.id WHERE users.role='professional' AND is_active=true`, apply `ILIKE` with `LOWER()` on `users.name`, `last_name`, `name||' '||last_name`, `professionals.cedula` if search provided, `ORDER BY LOWER(users.name) ASC, LOWER(users.last_name) ASC`
- [ ] Implement `list_deactivated()`: same JOIN with `is_active=false`, same ordering
- [ ] Implement `get_by_id`, `get_by_user_id`, `delete`, `exists_by_cedula` with `exclude_user_id` support
- [ ] Handle `IntegrityError` → `DuplicateUserException`
      **Done when:** `docker compose exec api pytest tests/infrastructure/test_postgres_professional_repository.py -v` passes — cases: save + `exists_by_cedula` true, `list_active` returns only active ordered A-Z, `list_active(search="ana")` case-insensitive returns multiple, `list_deactivated` returns only inactive, `get_by_id` not found → None, `delete` removes row.

#### Task 2.2: Extend PostgresUserRepository with exclude_id and delete + updated_at handling

**Requirements:** WS-5, BF-7..BF-8 (update uniqueness excluding self).
**Files to create/touch:**

- `app/infrastructure/repositories/postgres_user_repository.py`
  **Checkboxes:**
- [ ] Update `exists_by_email/dni/phone` to accept `exclude_id: int|None` → `WHERE field=:value AND id != :exclude_id` when provided
- [ ] Implement `delete(user)` → `DELETE FROM users WHERE id=:id` (cascade deletes professional via FK)
- [ ] Ensure `save` handles update via `merge` and touches `updated_at` (SQLAlchemy `onupdate=func.now()`)
      **Done when:** `docker compose exec api pytest tests/infrastructure/test_postgres_user_repository.py -v` passes — new cases: `exists_by_email("a@test.com", exclude_id=same_id)` → False, `exists_by_email` with other id → True, `delete` removes user and cascaded professional.

#### Task 2.3: Enforce login block for inactive professionals

**Requirements:** WS-6, BF-11 (deactivated cannot log in until reactivated).
**Files to create/touch:**

- `app/entrypoints/api/v1/routes/auth_router.py`
  **Checkboxes:**
- [ ] After password verify, check `if not user.is_active: raise HTTPException(401, "Unauthorized")` (or 403) for `users` with `is_active=false`
- [ ] Ensure admin (`role=administrator`) is_active check does not block admin (admin always active)
      **Done when:** `docker compose exec api pytest tests/entrypoints/test_auth.py::test_login_inactive_blocked -v` passes — create professional, deactivate via use case, then `POST /auth/login` with that professional's credentials → 401; admin login still 200.

---

### Phase 3 — Application Use Cases

#### Task 3.1: Implement ListProfessionals (public) and ListDeactivatedProfessionals (admin)

**Requirements:** WS-2, WS-4, BF-13; public no auth, admin-only deactivated, alphabetical, no pagination.
**Files to create/touch:**

- `app/application/use_cases/professional/list_professionals.py`
- `app/application/use_cases/professional/list_deactivated_professionals.py`
  **Checkboxes:**
- [ ] `ListProfessionalsUseCase` with `professional_repo, user_repo` → `execute(search)` calls `professional_repo.list_active(search)` and maps to `ProfessionalDetailResponse`
- [ ] `ListDeactivatedProfessionalsUseCase` with `execute(current_admin)` → raises `ForbiddenException` if not admin, else calls `list_deactivated()`
      **Done when:** `docker compose exec api pytest tests/application/test_list_professionals.py -v` passes — cases: empty search returns all active ordered A-Z, `search="ANA"` case-insensitive returns 2 with same name, inactive excluded, deactivated list without admin → Forbidden.

#### Task 3.2: Implement GetProfessionalById

**Requirements:** WS-3, BF-9; any user can get active professional by id.
**Files to create/touch:**

- `app/application/use_cases/professional/get_professional_by_id.py`
  **Checkboxes:**
- [ ] Fetch `professional` by id → `ProfessionalNotFoundException` if None, fetch linked `user` → if not found or (public mode) `is_active=false` → 404, map to `ProfessionalDetailResponse`
      **Done when:** `docker compose exec api pytest tests/application/test_get_professional_by_id.py -v` passes — found active → response, inactive/public → 404, non-existent → 404.

#### Task 3.3: Implement UpdateProfessional

**Requirements:** WS-5, BF-1..BF-5, BF-7..BF-9, BF-12; admin only, password not editable.
**Files to create/touch:**

- `app/application/use_cases/professional/update_professional.py`
  **Checkboxes:**
- [ ] Verify admin role, fetch professional+user or raise `ProfessionalNotFound`
- [ ] Validate uniqueness excluding self: `exists_by_email/dni/phone` with `exclude_id=user.id`, `exists_by_cedula` with `exclude_user_id=user.id` → `Duplicate*`
- [ ] Update `user` fields (name, last_name, dni, email, phone, updated_at) and `professional.cedula`, save both repos atomically (same session)
      **Done when:** `docker compose exec api pytest tests/application/test_update_professional.py -v` passes — success updates both tables and `updated_at` changed, duplicate email → `email ya registrado`, duplicate cedula excluding self allowed but other cedula → `Usuario ya registrado`, not found → 404, non-admin → Forbidden.

#### Task 3.4: Implement DeleteProfessional (hard delete)

**Requirements:** WS-8, BF-9, BF-12; admin only.
**Files to create/touch:**

- `app/application/use_cases/professional/delete_professional.py`
  **Checkboxes:**
- [ ] Verify admin, fetch professional+user, call `professional_repo.delete` then `user_repo.delete` (or just `user_repo.delete` with CASCADE), hard delete
      **Done when:** `docker compose exec api pytest tests/application/test_delete_professional.py -v` passes — success deletes both rows (`SELECT * FROM users WHERE id=:id` → 0, `professionals` → 0), not found → 404, second delete → 404.

#### Task 3.5: Implement Activate and Deactivate Professional

**Requirements:** WS-6, WS-7, BF-10, BF-11, BF-9, BF-12.
**Files to create/touch:**

- `app/application/use_cases/professional/activate_professional.py`
- `app/application/use_cases/professional/deactivate_professional.py`
  **Checkboxes:**
- [ ] `Activate`: verify admin, fetch, if `is_active` true → `AlreadyActiveException("Profesional ya activado")`, else set `True` and save, return detail
- [ ] `Deactivate`: same but checks `is_active` false → `AlreadyInactiveException("Profesional ya desactivado")`, set `False`, save, verify subsequent login blocked
      **Done when:** `docker compose exec api pytest tests/application/test_activate_professional.py tests/application/test_deactivate_professional.py -v` passes — 6 cases: activate inactive → active, activate already active → 409, deactivate active → inactive, deactivate already inactive → 409, not found → 404, non-admin → 403.

---

### Phase 4 — Entrypoints (API)

#### Task 4.1: Create ProfessionalRouter with public and admin endpoints

**Requirements:** WS-2..WS-8, BF-9..BF-13; routing, auth, status codes, validation mapping.
**Files to create/touch:**

- `app/entrypoints/api/v1/routes/professional_router.py`
- `app/entrypoints/api/v1/main.py`
  **Checkboxes:**
- [ ] `GET /api/v1/professionals` → `ListProfessionalsUseCase`, no auth, `?search=` query, 200 `{items,count}` ordered A-Z, only active
- [ ] `GET /api/v1/professionals/deactivated` → `ListDeactivatedProfessionalsUseCase` with `Depends(get_current_admin)`, 200 only inactive, 401/403 for non-admin
- [ ] `GET /api/v1/professionals/{id}` → `GetProfessionalByIdUseCase`, no auth, 200 or 404
- [ ] `PUT /api/v1/professionals/{id}` → `UpdateProfessionalUseCase` with admin auth, 200 or 400/422/409/404/403
- [ ] `DELETE /api/v1/professionals/{id}` → `DeleteProfessionalUseCase`, 204, 404/401/403
- [ ] `PATCH /api/v1/professionals/{id}/activate` and `/deactivate` → respective use cases, 200 or 409 `Profesional ya activado/desactivado`, 404/401/403
- [ ] Register `professional_router` in `main.py` via `app.include_router`, ensure `RequestValidationError` handler maps `Campos faltantes`→400, `email invalido`/`Formato inválido...`→422, domain exceptions → 409/404/403
      **Done when:** `docker compose exec api pytest tests/entrypoints/test_professional_router.py -k "test_public_list" -v` passes for ordering/search, and `docker compose up api -d && curl -s http://localhost:8000/api/v1/professionals | python -c "import json,sys; d=json.load(sys.stdin); assert d['count']>=0; print('public list ok')"` succeeds without token.

#### Task 4.2: Wire dependencies for new use cases

**Requirements:** All professional use cases require `ProfessionalRepository`, `UserRepository`, and `get_current_admin`.
**Files to create/touch:**

- `app/entrypoints/api/v1/dependencies.py`
  **Checkboxes:**
- [ ] Add `get_professional_repository`, `get_list_professionals_use_case`, `get_list_deactivated_use_case`, `get_get_professional_use_case`, `get_update_professional_use_case`, `get_delete_professional_use_case`, `get_activate_professional_use_case`, `get_deactivate_professional_use_case`
- [ ] Ensure `get_current_admin` still checks `role==administrator` and `is_active` (for deactivated admin edge case)
      **Done when:** `docker compose exec api python -c "from app.entrypoints.api.v1.dependencies import get_list_professionals_use_case, get_update_professional_use_case; print('deps ok')"` passes.

---

### Phase 5 — Integration & Verification

#### Task 5.1: Full API integration tests for professional router

**Requirements:** All WS and BF scenarios end-to-end.
**Files to create/touch:**

- `tests/entrypoints/test_professional_router.py`
  **Checkboxes:**
- [ ] Implement 15+ cases: public list without token ordered A-Z (3 professionals created `Carlos, Ana, Beatriz` → order `Ana, Beatriz, Carlos`), search `?search=ana` case-insensitive returns `Ana` (and duplicate `Ana`), search by `cedula`, empty search → all active, inactive excluded from public, `GET /{id}` public 200 for active 404 for inactive, `GET /deactivated` without token 401 receptionist 403 admin 200, `PUT` success updates and changes order, `PUT` with duplicate email → 409, `PUT` with `cedula` duplicate → 409, `PUT` missing → 400, invalid formats → 422, password field in update → 422, not found → 404, `DELETE` admin 204 and verify `professionals` + `users` gone, `PATCH activate/deactivate` idempotent 409, login blocked after deactivate
      **Done when:** `docker compose exec api pytest tests/entrypoints/test_professional_router.py -v` passes — 15 passed; `docker compose exec api pytest tests/entrypoints/test_auth.py::test_login_inactive_blocked -v` passes.

#### Task 5.2: Linter, type-check, and coverage gates (Definition of Done)

**Requirements:** `AGENT.md` Definition of Done.
**Files to create/touch:**

- `app/` (all new files), `pyproject.toml` (if needed for ruff)
  **Checkboxes:**
- [ ] `docker compose exec api ruff check app/` → 0 errors
- [ ] `docker compose exec api ruff format --check app/` → 0 errors or run `ruff format`
- [ ] `docker compose exec api python -m mypy app/domain app/application --ignore-missing-imports` → Success
- [ ] `docker compose exec api pytest --cov=app --cov-report=term-missing` → ≥80% `domain`+`application`, ≥60% `infrastructure`; `pytest tests/entrypoints/test_professional_router.py tests/application/test_*` all pass
      **Done when:** All three commands exit 0 inside `api` container; `grep -R "gabi12345" app/` only in `seed`/`settings`; `.env` still in `.gitignore`.

#### Task 5.3: Final Docker smoke and public list manual verification

**Requirements:** WS-2 public without auth, alphabetical, no pagination.
**Files to create/touch:**

- (no new files, verification only)
  **Checkboxes:**
- [ ] `docker compose up --build -d && curl -s http://localhost:8000/api/v1/professionals | python -c "import json,sys; d=json.load(open(0)); assert d['items'][0]['name'] <= d['items'][1]['name']; print(f\"public list count={d['count']} ordered A-Z ok\")"` without token → 200 ordered
- [ ] Login as admin, create professional `Zoe`, verify she appears last in alphabetical order, deactivate her, verify she disappears from public list and appears in `GET /professionals/deactivated` with admin token, reactivate and verify reappears, delete and verify gone from both tables
- [ ] `docker compose exec db psql -U postgres -d app_db -c "SELECT u.name, p.cedula, u.is_active FROM users u JOIN professionals p ON p.user_id=u.id ORDER BY u.name;"` shows alphabetical and active flag
      **Done when:** All manual curl/psql checks return expected ordering and visibility; `docker compose logs api` shows no startup errors; `docker compose ps` shows `api` and `db` healthy.

---

### Task Completion Checklist (for tracking)

- [x] 1.1 DTOs: UpdateProfessionalRequest + ProfessionalDetailResponse
- [x] 1.2 Repository ports with exclude_id and delete
- [x] 1.3 Domain exceptions for activate idempotency
- [ ] 2.1 PostgresProfessionalRepository list/search/delete
- [ ] 2.2 PostgresUserRepository exclude_id + delete + updated_at
- [ ] 2.3 Login block for inactive
- [ ] 3.1 ListProfessionals + ListDeactivated
- [ ] 3.2 GetProfessionalById
- [ ] 3.3 UpdateProfessional
- [ ] 3.4 DeleteProfessional
- [ ] 3.5 Activate/Deactivate
- [ ] 4.1 ProfessionalRouter endpoints
- [ ] 4.2 Dependencies wiring
- [ ] 5.1 API integration tests
- [ ] 5.2 Linter/type/coverage gates
- [ ] 5.3 Docker smoke + manual verification

> Total: 16 tasks × ~25 min ≈ 6.5 hours. Execute strictly in order; each phase's `Done when` must pass inside `api` container before starting next.


