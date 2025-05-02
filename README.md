```markdown
# **SpeakNowly: FastAPI Application**

Welcome to the **SpeakNowly** project! This project provides APIs for various platforms, including a client site, mobile application, and admin dashboard. It is built using **FastAPI** and follows a modular structure.

---

## **Project Structure**

```
app/
├── api/                        # APIs for different platforms
│   ├── client_site/            # API for the client site
│   │   ├── v1/                 # Version 1 API
│   │   │   ├── serializers/    # API serializers
│   │   │   ├── views/          # API views
│   │   │   ├── routes.py       # API routes
│   ├── dashboard/              # API for the admin dashboard
│   │   ├── v1/                 # Version 1 API
│   │   │   ├── serializers/    # API serializers
│   │   │   ├── views/          # API views
│   │   │   ├── routes.py       # API routes
│   ├── mobile/                 # API for the mobile application
│   │   ├── v1/                 # Version 1 API
│   │   │   ├── serializers/    # API serializers
│   │   │   ├── views/          # API views
│   │   │   ├── routes.py       # API routes
├── models/                     # Database models
│   ├── base.py                 # Base model
│   ├── users.py                # User models
│   ├── tariffs.py              # Tariff and feature models
│   ├── notifications.py        # Notification models
│   ├── transactions.py         # Transaction models
│   ├── tests/                  # Test models
│   │   ├── listening.py        # Models for listening tests
│   │   ├── reading.py          # Models for reading tests
│   │   ├── writing.py          # Models for writing tests
│   │   ├── speaking.py         # Models for speaking tests
│   │   ├── grammar.py          # Models for grammar tests
│   │   └── vocabulary.py       # Models for vocabulary tests
├── services/                   # Microservice logic
├── tasks/                      # Background tasks
├── utils/                      # Utility and helper functions
├── main.py                     # Application entry point
├── config.py                   # Project configuration
├── .env                        # Environment variables
├── Pipfile                     # Project dependencies
└── README.md                   # Project documentation
```

---

## **Key Features**

- **Users**:
  - Registration, authentication, and profile management.
  - Verification via OTP codes.

- **Tariffs**:
  - Management of tariffs, categories, features, and discounts.

- **Tests**:
  - Support for tests (listening, writing, reading, speaking, etc.).
  - Analysis of test results.

- **Notifications**:
  - Sending notifications to users.
  - Tracking read status.

- **Payments and Transactions**:
  - Management of payments and token transactions.

---

## **How to Install and Run the Project**

### **1. Install Dependencies**
Ensure you have Python 3.7 or higher installed. Install `pipenv` if it is not already installed:

```bash
pip install pipenv
```

Then, install the project dependencies using `pipenv`:

```bash
pipenv install
```

### **2. Activate the Virtual Environment**
Activate the virtual environment created by `pipenv`:

```bash
pipenv shell
```

### **3. Configure Environment Variables**
Create a `.env` file in the project root and add the following variables:

```env
SECRET_KEY=your_secret_key
DEBUG=true
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

### **4. Apply Database Migrations**
Run the database migrations using Tortoise ORM:

```bash
aerich upgrade
```

### **5. Start the Application**
Run the development server using the following command:

```bash
uvicorn app.main:app --reload
```

### **6. Access the API**
Once the application is running, you can access the API documentation at:
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## **API Endpoints**

### **Users**
- `POST /api/v1/auth/login/` — User login.
- `POST /api/v1/auth/register/` — User registration.
- `GET /api/v1/users/me/` — Retrieve the current user's profile.

### **Tariffs**
- `GET /api/v1/tariffs/` — Retrieve a list of tariffs.
- `GET /api/v1/tariffs/{id}/` — Retrieve tariff details by ID.

### **Tests**
- `GET /api/v1/tests/listening/` — Retrieve listening tests.
- `POST /api/v1/tests/writing/` — Create a writing test.

### **Notifications**
- `GET /api/v1/notifications/` — Retrieve a list of notifications.
- `GET /api/v1/notifications/{id}/` — Retrieve a notification by ID.

### **Payments**
- `POST /api/v1/payments/checkout/` — Create a payment.
- `GET /api/v1/payments/` — Retrieve a list of payments.

---

## **Contributing**

We welcome any suggestions and contributions! If you'd like to contribute, please create a pull request or open an issue.

---

## **License**

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---

If you have any questions or suggestions, feel free to reach out. Happy coding with **SpeakNowly**! 🎉
```