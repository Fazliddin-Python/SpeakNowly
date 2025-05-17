# SpeakNowly API

Modular FastAPI backend for the SpeakNowly platform: REST API for the client website, mobile app, and admin dashboard.

---

## Table of Contents

1. Overview  
2. Structure  
3. Features  
4. Installation  
5. Configuration  
6. Migrations  
7. Running  
8. Documentation  
9. API Routing & Organization  
10. Endpoints  
11. Contribution  
12. License  

---

## 1. Overview

SpeakNowly provides:

- User registration, authentication (JWT + OTP), and profile management
- Secure password reset and email update flows
- Management of tariffs, categories, and discounts
- Language tests (listening, reading, writing, speaking, grammar, vocabulary) with result analysis
- Notifications with read tracking
- Payments and token transactions
- Modular, scalable architecture for client, mobile, and admin interfaces

---

## 2. Structure

```text
app/
├── api/
│   ├── client_site/v1/
│   │   ├── views/
│   │   │   ├── users/
│   │   │   │   ├── users.py
│   │   │   │   ├── profile.py
│   │   │   │   ├── login.py
│   │   │   │   ├── logout.py
│   │   │   │   ├── register.py
│   │   │   │   ├── resend.py
│   │   │   │   ├── forget_password.py
│   │   │   │   ├── email_update.py
│   │   │   │   ├── verification_codes.py
│   │   │   │   └── __init__.py
│   │   │   ├── tests/
│   │   │   └── ... (other modules)
│   │   ├── serializers/
│   │   ├── routes.py
│   │   └── __init__.py
│   ├── dashboard/v1/
│   └── mobile/v1/
├── models/
├── services/
├── tasks/
├── utils/
├── main.py
├── config.py
├── celery_app.py
├── .env
├── Pipfile
└── README.md
```

---

## 3. Features

- **Users**: registration, login, logout, profile, OTP, password reset, email update
- **Tariffs**: CRUD for tariffs, categories, discounts
- **Tests**: all types of language tests, automatic analysis
- **Notifications**: sending, read status
- **Payments**: creation, history, tokens
- **Admin & Staff**: user management, permissions
- **Rate Limiting**: per-action (registration, login, password reset, etc.)
- **Celery**: background tasks for email, logging, etc.
- **Internationalization**: multi-language support for messages

---

## 4. Installation

```bash
git clone https://github.com/your-org/speaknowly.git
cd speaknowly
pip install pipenv
pipenv install
pipenv shell
```

---

## 5. Configuration

Create a `.env` file in the root:

```env
SECRET_KEY=your_secret_key
DEBUG=true
ALLOWED_HOSTS=*
DATABASE_URL=postgresql://user:password@host/db
EMAIL_BACKEND=smtp
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your@email
SMTP_PASSWORD=your_password
EMAIL_FROM=your@email
REDIS_URL=redis://localhost:6379/0
```

---

## 6. Migrations

```bash
aerich init --config=config.DATABASE_CONFIG
aerich migrate
aerich upgrade
```

---

## 7. Running

```bash
uvicorn main:app --reload
```

API: http://127.0.0.1:8000

---

## 8. Documentation

- Swagger: http://127.0.0.1:8000/docs  
- ReDoc: http://127.0.0.1:8000/redoc  

---

## 9. API Routing & Organization

- **All user and auth endpoints are grouped under `/api/v1/users/`** for clarity and REST consistency.
- **Other domains** (tests, tariffs, notifications, etc.) are grouped under their own prefixes.
- **Example structure:**
    - `/api/v1/users/` — user CRUD (admin)
    - `/api/v1/users/profile/` — user profile
    - `/api/v1/users/email-update/` — email update flow
    - `/api/v1/users/login/` — login
    - `/api/v1/users/logout/` — logout
    - `/api/v1/users/register/` — registration
    - `/api/v1/users/resend-otp/` — resend OTP
    - `/api/v1/users/forget-password/` — password reset
    - `/api/v1/users/verification/` — OTP verification
    - `/api/v1/tests/` — language tests
    - `/api/v1/tariffs/` — tariffs and categories
    - `/api/v1/notifications/` — notifications
    - `/api/v1/payments/` — payments and tokens

---

## 10. Endpoints (examples)

- `POST /api/v1/users/register/` — registration
- `POST /api/v1/users/login/` — JWT login
- `POST /api/v1/users/logout/` — logout
- `GET /api/v1/users/me/` — user profile
- `PUT /api/v1/users/profile/` — update profile
- `POST /api/v1/users/email-update/` — request email update
- `POST /api/v1/users/email-update/confirm/` — confirm email update
- `POST /api/v1/users/forget-password/` — request password reset
- `POST /api/v1/users/forget-password/confirm/` — confirm password reset
- `POST /api/v1/users/resend-otp/` — resend OTP
- `POST /api/v1/users/verification/verify-otp` — verify OTP
- `GET /api/v1/tariffs/` — list tariffs
- `GET /api/v1/tests/listening/` — listening tests
- `GET /api/v1/notifications/` — notifications
- `POST /api/v1/payments/checkout/` — payment

---

## 11. Contribution

PRs and ideas are welcome! See CONTRIBUTING.md.

---

## 12. License

MIT License. See LICENSE.
