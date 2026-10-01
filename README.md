# Online Cinema API

Digital platform API that allows users to browse, search, purchase, and stream movies securely. Built with modern asynchronous Python stack.

---

## 🚀 Tech Stack

* **Framework:** FastAPI (Python 3.12)
* **Database & ORM:** PostgreSQL, SQLAlchemy (Asyncio), Alembic (Migrations)
* **Validation & Settings:** Pydantic v2, Pydantic-Settings
* **Task Queue & Background Jobs:** Celery, Redis, Celery Beat
* **Authentication:** JWT (JSON Web Tokens), Passlib (Bcrypt)
* **Payments:** Stripe API integration & Webhooks
* **Containerization:** Docker & Docker Compose
* **Dependency Management:** Poetry
* **Testing:** Pytest, Pytest-Asyncio, HTTPX

---

## 🛠️ Project Architecture & Features

1. **User Management & RBAC:**
   * Registration with email activation (24-hour token expiration & Celery cleanup task).
   * Password reset mechanism and complexity enforcement.
   * Role-Based Access Control (User, Moderator, Admin).
2. **Movie Catalog:**
   * Advanced filtering, sorting, pagination, and full-text search.
   * Management of genres, directors, stars, and certifications.
3. **Shopping Cart & Orders:**
   * Cart management with duplicate and purchase-status validations.
   * Secure order placement preserving historical item prices.
4. **Stripe Payments:**
   * Payment processing and asynchronous webhook status updates.

---

## ⚙️ Local Installation & Setup

### Prerequisites
* Python 3.12+
* Poetry
* Docker & Docker Compose (recommended for services)

### 1. Clone the repository
```bash
git clone [https://github.com/olimp72/online-cinema-api.git](https://github.com/olimp72/online-cinema-api.git)
cd online-cinema-api
```

### 2. Configure environment variables
Create a .env file in the root directory based on your configuration:

Фрагмент кода
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=cinema_db
SECRET_KEY=your_super_secret_jwt_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
REDIS_URL=redis://localhost:6379/0
STRIPE_API_KEY=your_stripe_secret_key

### 3. Install Dependencies with Poetry
```Bash
poetry install
```

### 4. Run Database Migrations
```Bash
poetry run alembic upgrade head
```

🏃 Running the Application

Option A: Locally via Uvicorn
```Bash
poetry run uvicorn app.main:app --reload
```
Option B: Via Docker Compose (Recommended)
To run the application along with PostgreSQL, Redis, and Celery workers:
```Bash
docker-compose up --build -d
```
🧪 Testing & Code Quality
To run unit and integration tests using Pytest:

```Bash
poetry run pytest
```
To check code style compliance (Flake8):
```Bash
poetry run flake8
```
📄 API Documentation
Access to the interactive Swagger UI and ReDoc documentation is protected via HTTP Basic Authentication.
Use the following credentials to log in:

Username: admin

Password: admin

Documentation endpoints:

Swagger UI: http://127.0.0.1:8000/docs

ReDoc: http://127.0.0.1:8000/redoc