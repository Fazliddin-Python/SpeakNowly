# SpeakNowly: FastAPI Application

SpeakNowly is a modular FastAPI application that provides RESTful APIs for a client website, a mobile app, and an admin dashboard.

---

## Table of Contents

1. Project Overview  
2. Directory Structure  
3. Key Features  
4. Installation  
5. Configuration  
6. Database Migrations  
7. Running the Application  
8. API Documentation  
9. Available Endpoints  
10. Contributing  
11. License  

---

## Project Overview

SpeakNowly offers:

- User registration, authentication (including OTP verification), and profile management  
- Tariff and feature management, including categories and discounts  
- A suite of language tests (listening, reading, writing, speaking, grammar, vocabulary) with result analysis  
- Notification delivery with read/unread tracking  
- Payment processing and token-based transactions  

---

## Directory Structure

```text
app/
├── api/
│ ├── client\_site/ # Client website API (v1)
│ │ ├── serializers/
│ │ ├── views/
│ │ └── routes.py
│ ├── mobile/ # Mobile app API (v1)
│ │ ├── serializers/
│ │ ├── views/
│ │ └── routes.py
│ └── dashboard/ # Admin dashboard API (v1)
│ ├── serializers/
│ ├── views/
│ └── routes.py
├── models/ # Database models
│ ├── base.py
│ ├── users.py
│ ├── tariffs.py
│ ├── notifications.py
│ ├── transactions.py
│ └── tests/ # Test-related models
│ ├── listening.py
│ ├── reading.py
│ ├── writing.py
│ ├── speaking.py
│ ├── grammar.py
│ └── vocabulary.py
├── services/ # Business logic
├── tasks/ # Background jobs
├── utils/ # Helpers and utilities
├── main.py # Application entry point
├── config.py # Configuration settings
├── .env # Environment variables
├── Pipfile # Dependencies
└── README.md # Project documentation
```

---

## Key Features

- **Users**: Registration, login, profile management, OTP-based verification  
- **Tariffs**: CRUD operations for tariffs, categories, features, discounts  
- **Language Tests**: Listening, reading, writing, speaking, grammar, vocabulary, automated result analysis  
- **Notifications**: Send notifications to users, track read/unread status  
- **Payments**: Create and manage payments, token transaction history  

---

## Installation

1. Clone the repository:  
   ```bash
   git clone https://github.com/your-org/speaknowly.git
   cd speaknowly
   ```

2. Install dependencies (requires Python 3.7+ and pipenv):  
   ```bash
   pip install pipenv
   pipenv install
   ```

3. Activate the virtual environment:  
   ```bash
   pipenv shell
   ```

---

## Configuration

Create a .env file in the project root with the following variables:

```env
SECRET_KEY=your_secret_key
DEBUG=true
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

---

## Database Migrations

Apply database migrations using Tortoise ORM (aerich):

```bash
aerich init --config=config.TORTOISE_ORM
aerich migrate
aerich upgrade
```

---

## Running the Application

Start the development server:

```bash
uvicorn main:app --reload
```

The API will be available at: [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## API Documentation

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)  

---

## Available Endpoints

### Authentication

- `POST /api/v1/auth/register/` — Register a new user  
- `POST /api/v1/auth/login/` — Obtain JWT tokens  

### Users

- `GET /api/v1/users/me/` — Get current user profile  

### Tariffs

- `GET /api/v1/tariffs/` — List all tariffs  
- `GET /api/v1/tariffs/{id}/` — Get tariff by ID  

### Tests

- `GET /api/v1/tests/listening/` — Retrieve listening tests  
- `POST /api/v1/tests/writing/` — Submit a writing test  
  *(other test endpoints follow the same pattern)*  

### Notifications

- `GET /api/v1/notifications/` — List notifications  
- `GET /api/v1/notifications/{id}/` — Get notification details  

### Payments

- `POST /api/v1/payments/checkout/` — Initiate a payment  
- `GET /api/v1/payments/` — List payment records  

---

## Contributing

We welcome contributions from the community! Please refer to CONTRIBUTING.md for detailed guidelines.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
