# Professionals — Centro Médico

## 1. Objective

Provide complete management of Professional users within the Centro Médico system. While the existing user registration allows the Administrator to create Receptionists and Professionals, this feature extends to a full CRUD lifecycle for Professionals including listing, retrieving, updating, deleting, and activating/deactivating their accounts. It ensures that only active Professionals are publicly visible and can authenticate, that all personal and professional data remains validated and unique, and that only the Administrator can perform sensitive mutations, preserving data integrity and access control.

## 2. Use Cases & User Flow

**Primary actors:**
- **Administrator** — the only actor who can create, update, delete, and activate/deactivate a Professional. Credentials are pre-provisioned via `.env`. Can also list deactivated Professionals to retrieve their IDs.
- **Any user (no authentication required)** — can list and retrieve active Professionals without needing to log in.
- **Professional (as data subject)** — Professional account is linked to a `users` record (with `is_active`, `created_at`, `updated_at`) and a `professionals` record (with `cedula`).

**Main flows (Happy Path):**

**Create Professional:**
1. Administrator accesses professional creation.
2. Administrator fills all required fields: name, last_name, dni, email, phone, password, and cedula.
3. System validates completeness, format, and uniqueness.
4. System creates the linked `users` record (role=professional, is_active=True) and `professionals` record (cedula) atomically.
5. New Professional appears in the active list ordered alphabetically.

**List/Get Professionals (Public):**
1. Any user (without authentication) requests the list or a specific active professional.
2. System returns only active professionals, ordered alphabetically from A to Z by name, optionally filtered by search term (name, last name, full name, or cedula, case-insensitive).
3. User sees the data. Search by name may return multiple results if several professionals share the same name or last name.

**List Deactivated Professionals (Admin only):**
1. Administrator requests the list of deactivated professionals.
2. System returns all professionals with `is_active=False`, including their IDs and other fields, so the Administrator can identify and reactivate them.

**Update Professional:**
1. Administrator selects an existing professional and edits any of the editable fields (name, last_name, dni, email, phone, cedula). Password is not editable in this iteration.
2. System validates the new data with the same rules as creation, checking uniqueness against other records excluding the current one.
3. System updates both linked records.

**Activate / Deactivate Professional:**
1. Administrator triggers activate or deactivate for a professional.
2. System toggles `users.is_active` for the linked user.
3. A deactivated professional can no longer log in until re-activated; the record persists in the database but is hidden from the public active-only listing.

**Delete Professional:**
1. Administrator deletes a professional.
2. System permanently removes both the `professionals` record and the linked `users` record (hard delete).

## 3. Business Rules

- **Permissions:**
  - Only Administrator can create, update, delete, activate, and deactivate Professionals.
  - Any user can list and get active Professionals without authentication.
  - Only Administrator can list deactivated Professionals.

- **Preconditions:**
  - For create, update, delete, and activate/deactivate, Administrator must be authenticated.
  - For update, delete, activate/deactivate, and get-by-id, the professional must exist; otherwise the system returns an error.
  - Listing of active professionals requires no authentication; listing of deactivated requires Administrator authentication.

- **Required fields:**
  - On create: name, last_name, dni, email, phone, password, and cedula are all required.
  - On update: name, last_name, dni, email, phone, and cedula are editable and required if provided; password is not editable in this iteration and must not be included in update payloads.

- **Completeness:** If any required field is missing or empty on create (or on update for the fields being updated), the system must display the error: "Campos faltantes".

- **Format validation:**
  - Email must contain "@"; otherwise "email invalido".
  - DNI must be exactly 8 digits; otherwise "Formato inválido, debe tener 8 caracteres".
  - Phone must be exactly 10 digits; otherwise "Formato inválido, debe tener 10 caracteres".
  - Cedula must be 7-8 characters alphanumeric; otherwise "Formato inválido, debe tener 7 u 8 caracteres".
  - Password (on create only) must be at least 8 characters; otherwise "La contraseña debe tener al menos 8 caracteres".

- **Uniqueness:**
  - Email, dni, phone, and cedula must be unique across the system.
  - On create: duplicate email → "email ya registrado"; duplicate dni/phone/cedula → "Usuario ya registrado".
  - On update: the same checks apply, but the current professional's own values are excluded; if the new value collides with another record, the same error messages are returned.

- **Account status and activation:**
  - A newly created professional is active (`is_active=True`) and can log in immediately.
  - Deactivating sets `is_active=False` for the linked `users` record; the professional cannot log in until re-activated.
  - The database record persists after deactivation.
  - Activating an already active professional → "Profesional ya activado".
  - Deactivating an already inactive professional → "Profesional ya desactivado".

- **Listing and retrieval:**
  - Public listing returns only active professionals, ordered alphabetically from A to Z by name. No pagination is applied in this iteration; all matching active professionals are returned at once.
  - Search is case-insensitive and may be performed by name, last name, full name (name and last name combined), or cedula. Search by name or last name may return multiple results. If no search term is provided, all active professionals are returned.
  - Deactivated listing (admin only) returns all professionals with `is_active=False`, ordered alphabetically as well, to allow the Administrator to view IDs and reactivate.

- **Deletion:**
  - Deleting a professional permanently removes both the `professionals` row and the linked `users` row.
  - Attempting to delete, update, activate/deactivate, or get a non-existent professional → "Professional Not Found".

- **Role assignment:** Professionals are always created with role=professional; the role is not editable via this feature.

- **System limits:** No explicit limits on number of professionals are defined; pagination for active listing will be added in a future iteration.

## 4. Scenarios

### Well Scenarios (Success)

**WS-1: Successful creation of a Professional by Administrator**
- **Context:** Administrator wants to create a new professional with valid data.
- **When:** Administrator provides all required fields with valid formats and unique values (dni 8 digits, phone 10 digits, email with "@", cedula 7-8 alphanumeric, password ≥8).
- **So/Then:** System creates both linked records atomically, marks the user as active, and the new professional appears in the alphabetically ordered active list.

**WS-2: Successful public listing of active Professionals without authentication**
- **Context:** Any visitor wants to browse professionals without logging in.
- **When:** User requests the public list (optionally with search by name, last name, full name, or cedula, case-insensitive).
- **So/Then:** System returns only active professionals matching the search term, ordered alphabetically A-Z.

**WS-3: Successful retrieval of a single active Professional**
- **Context:** Any user wants to view details of a specific professional.
- **When:** User requests a professional by valid id.
- **So/Then:** System returns the professional's data.

**WS-4: Successful listing of deactivated Professionals by Administrator**
- **Context:** Administrator wants to view deactivated professionals to reactivate one.
- **When:** Administrator requests the deactivated list.
- **So/Then:** System returns all professionals with `is_active=False` with their IDs and other fields.

**WS-5: Successful update of a Professional by Administrator**
- **Context:** Administrator wants to correct a professional's data.
- **When:** Administrator changes one or more editable fields (name, last_name, dni, email, phone, cedula) with valid and unique new values (password is not included).
- **So/Then:** System updates both linked records and the changes are visible in subsequent reads and remain alphabetically ordered.

**WS-6: Successful deactivation by Administrator**
- **Context:** Administrator wants to temporarily disable a professional.
- **When:** Administrator deactivates an active professional.
- **So/Then:** System sets `is_active` to False, the professional disappears from the public active-only list and cannot log in, but the record remains in the database and appears in the admin deactivated list.

**WS-7: Successful activation by Administrator**
- **Context:** Administrator wants to re-enable a previously deactivated professional.
- **When:** Administrator activates an inactive professional found via the deactivated list.
- **So/Then:** System sets `is_active` to True and the professional reappears in the public list and can log in again.

**WS-8: Successful deletion by Administrator**
- **Context:** Administrator wants to permanently remove a professional.
- **When:** Administrator deletes an existing professional.
- **So/Then:** System permanently deletes both the `professionals` and linked `users` records.

### Bad Scenarios (Failure)

**BF-1: Missing required fields on create or update**
- **Context:** Administrator submits the form with one or more required fields empty.
- **When:** System validates the payload.
- **So/Then:** System rejects the operation and displays "Campos faltantes".

**BF-2: Invalid email format**
- **Context:** Administrator provides an email without "@".
- **When:** System validates the email.
- **So/Then:** System rejects and displays "email invalido".

**BF-3: Invalid dni format**
- **Context:** Administrator provides a dni with fewer or more than 8 digits or non-numeric characters.
- **When:** System validates the dni.
- **So/Then:** System rejects and displays "Formato inválido, debe tener 8 caracteres".

**BF-4: Invalid phone format**
- **Context:** Administrator provides a phone with fewer or more than 10 digits.
- **When:** System validates the phone.
- **So/Then:** System rejects and displays "Formato inválido, debe tener 10 caracteres".

**BF-5: Invalid cedula format**
- **Context:** Administrator provides a cedula shorter than 7 or longer than 8 characters or with invalid characters.
- **When:** System validates the cedula.
- **So/Then:** System rejects and displays "Formato inválido, debe tener 7 u 8 caracteres".

**BF-6: Password too short on create**
- **Context:** Administrator provides a password with fewer than 8 characters on creation.
- **When:** System validates the password.
- **So/Then:** System rejects and displays "La contraseña debe tener al menos 8 caracteres".

**BF-7: Duplicate email on create or update**
- **Context:** Administrator tries to use an email already belonging to another user.
- **When:** System checks uniqueness.
- **So/Then:** System rejects and displays "email ya registrado".

**BF-8: Duplicate dni / phone / cedula on create or update**
- **Context:** Administrator tries to use a dni, phone, or cedula already belonging to another user/professional.
- **When:** System checks uniqueness (excluding the current professional on update).
- **So/Then:** System rejects and displays "Usuario ya registrado".

**BF-9: Professional not found**
- **Context:** Administrator or any user tries to get, update, delete, or activate/deactivate a professional with a non-existent id.
- **When:** System looks up the record.
- **So/Then:** System returns "Professional Not Found".

**BF-10: Activate an already active professional**
- **Context:** Administrator tries to activate a professional whose `is_active` is already True.
- **When:** System checks current status.
- **So/Then:** System rejects and displays "Profesional ya activado".

**BF-11: Deactivate an already inactive professional**
- **Context:** Administrator tries to deactivate a professional whose `is_active` is already False.
- **When:** System checks current status.
- **So/Then:** System rejects and displays "Profesional ya desactivado".

**BF-12: Unauthorized mutation by non-administrator**
- **Context:** A non-administrator (e.g., Receptionist) tries to create, update, delete, or activate/deactivate a professional.
- **When:** System checks the requester's role.
- **So/Then:** System rejects with unauthorized/forbidden error.

**BF-13: Unauthorized access to deactivated list**
- **Context:** A non-administrator tries to view the deactivated professionals list.
- **When:** System checks the requester's role.
- **So/Then:** System rejects with unauthorized/forbidden error.

## [NECESITA ACLARACIÓN]

- No hay puntos pendientes. Todas las dudas previas han sido aclaradas: el listado público no requiere autenticación, el orden es alfabético A-Z sin paginación por ahora, la búsqueda es insensible a mayúsculas y puede ser por nombre, apellido, nombre completo o cédula devolviendo múltiples resultados, la contraseña no es editable en actualización, y el administrador dispone de un listado separado de desactivados para reactivación.
