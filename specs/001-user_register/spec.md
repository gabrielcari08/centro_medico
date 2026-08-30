# User Registration — Centro Médico

## 1. Objective

Define the process by which users are created and managed within the Centro Médico management system. The system supports three user roles: Administrator, Receptionist, and Professional. The Administrator is pre-provisioned via a `.env` file located at the project root and holds the exclusive permission to create Receptionist and Professional accounts. The objective is to ensure that all user accounts are created with accurate, validated, and unique information, with appropriate error feedback, so that only legitimate users gain access to the system.

## 2. Use Cases & User Flow

**Primary actors:**

- **Administrator** — pre-provisioned user whose credentials are stored in a `.env` file at the project root. The Administrator has the exclusive permission to create Receptionist or Professional accounts by filling in the required fields.
- **Receptionist** — user created by the Administrator through a form with the standard fields.
- **Professional** — user created by the Administrator through a form with the standard fields plus the cédula field.

**Main flow (Happy Path):**

1. The Administrator accesses the user creation interface.
2. The Administrator selects the type of user to create: Receptionist or Professional.
3. The Administrator fills in all required fields: name, last name, DNI, email, phone, and password. If creating a Professional, the Administrator also fills in the cédula field.
4. The system validates all fields: completeness, format, and uniqueness.
5. If all validations pass, the system creates the user and marks the account as active.
6. The created user can immediately log in.

## 3. Business Rules

- **Administrator provisioning:** The Administrator does not register through a form. Credentials are stored in a `.env` file located at the project root. The `.env` contains the fields: `NAME=Gabriel Cari` and `PASSWORD=gabi12345`. The `NAME` field represents the full name of the administrator (first and last name). The `PASSWORD` is stored in plain text. The `.env` file is not uploaded to the repository. Only one Administrator can exist in the system; no additional administrators can be created.
- **Exclusive creation right:** Only the Administrator can create Receptionist or Professional accounts. No self-registration is available for these roles.
- **Required fields (all user types):** name, last name, DNI, email, phone, password.
- **Additional field (Professional only):** cédula.
- **Completeness:** All required fields must be filled. If any required field is left empty, the system must display the error: "Campos faltantes".
- **Uniqueness:** The email, DNI, phone, and cédula (when applicable) must be unique across the entire system. No duplicates are allowed. If a duplicate email is detected, the system must display the error: "email ya registrado". If a duplicate DNI, phone, or cédula is detected, the system must display the error: "Usuario ya registrado".
- **Email format:** The email must contain the "@" character. If the email format is invalid, the system returns the error: "email invalido" via Pydantic.
- **DNI format:** The DNI must consist of exactly 8 digits, no more and no fewer. If invalid, the system displays the error: "Formato inválido, debe tener 8 caracteres".
- **Phone format:** The phone number must consist of exactly 10 digits, no more and no fewer. If invalid, the system displays the error: "Formato inválido, debe tener 10 caracteres".
- **Cédula format (Professional only):** The cédula must be between 7 and 8 characters, which may be letters or numbers. If invalid, the system displays the error: "Formato inválido, debe tener 7 u 8 caracteres".
- **Password:** Minimum 8 characters in length.
- **Account status:** The user is active immediately upon creation.
- **Role assignment:** The role is determined by the Administrator at the time of creation based on which creation template is used (Receptionist or Professional).
- **System limits:** No explicit limits on registration attempts or maximum number of stored users are defined.

## 4. Scenarios

### Well Scenarios (Success)

**WS-1: Successful creation of a Receptionist**

- **Context:** The Administrator wants to create a new Receptionist account.
- **When:** The Administrator fills in all required fields (name, last name, DNI, email, phone, password) with valid and unique values, and the DNI has exactly 8 digits, the email contains "@", the phone has exactly 10 digits, and the password is at least 8 characters.
- **So/Then:** The system creates the Receptionist account, marks the user as active, and the user can immediately log in.

**WS-2: Successful creation of a Professional**

- **Context:** The Administrator wants to create a new Professional account.
- **When:** The Administrator fills in all required fields plus the cédula, with valid and unique values. The cédula is between 7 and 8 characters (letters or numbers), the DNI has exactly 8 digits, the email contains "@", the phone has exactly 10 digits, and the password is at least 8 characters.
- **So/Then:** The system creates the Professional account, marks the user as active, and the user can immediately log in.

### Bad Scenarios (Failure)

**BF-1: Duplicate email**

- **Context:** The Administrator attempts to create a user with an email that already exists in the system.
- **When:** The Administrator submits a form with an email that is already registered.
- **So/Then:** The system rejects the creation and displays the error: "email ya registrado".

**BF-2: Duplicate DNI**

- **Context:** The Administrator attempts to create a user with a DNI that already exists in the system.
- **When:** The Administrator submits a form with a DNI that is already registered.
- **So/Then:** The system rejects the creation and displays the error: "Usuario ya registrado".

**BF-3: Duplicate phone**

- **Context:** The Administrator attempts to create a user with a phone number that already exists in the system.
- **When:** The Administrator submits a form with a phone number that is already registered.
- **So/Then:** The system rejects the creation and displays the error: "Usuario ya registrado".

**BF-4: Duplicate cédula (Professional)**

- **Context:** The Administrator attempts to create a Professional with a cédula that already exists in the system.
- **When:** The Administrator submits a form with a cédula that is already registered.
- **So/Then:** The system rejects the creation and displays the error: "Usuario ya registrado".

**BF-5: Password too short**

- **Context:** The Administrator attempts to create a user with a password shorter than 8 characters.
- **When:** The Administrator submits a form with a password of fewer than 8 characters.
- **So/Then:** The system rejects the creation and displays the error: "La contraseña debe tener al menos 8 caracteres".

**BF-6: Missing required fields**

- **Context:** The Administrator attempts to create a user but leaves one or more required fields empty.
- **When:** The Administrator submits the form with any required field left blank.
- **So/Then:** The system rejects the creation and displays the error: "Campos faltantes".

**BF-7: Invalid email format**

- **Context:** The Administrator attempts to create a user with an email that does not contain "@".
- **When:** The Administrator submits a form with an email lacking the "@" character.
- **So/Then:** The system rejects the creation and displays the error: "email invalido".

**BF-8: Invalid DNI format**

- **Context:** The Administrator attempts to create a user with a DNI that does not have exactly 8 digits.
- **When:** The Administrator submits a form with a DNI that has fewer or more than 8 digits, or contains non-numeric characters.
- **So/Then:** The system rejects the creation and displays the error: "Formato inválido, debe tener 8 caracteres".

**BF-9: Invalid phone format**

- **Context:** The Administrator attempts to create a user with a phone number that does not have exactly 10 digits.
- **When:** The Administrator submits a form with a phone number that has fewer or more than 10 digits, or contains non-numeric characters.
- **So/Then:** The system rejects the creation and displays the error: "Formato inválido, debe tener 10 caracteres".

**BF-10: Invalid cédula format (Professional)**

- **Context:** The Administrator attempts to create a Professional with a cédula that does not meet the format requirement.
- **When:** The Administrator submits a form with a cédula that is shorter than 7 characters or longer than 8 characters.
- **So/Then:** The system rejects the creation and displays the error: "Formato inválido, debe tener 7 u 8 caracteres".
