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
git clone [https://github.com/olimp72/online-cinema-fastapi.git](https://github.com/olimp72/online-cinema-fastapi.git)
cd online-cinema-fastapi
```

### 2. Configure environment variables
Create a .env file in the root directory based on your configuration:

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

### 3. Встановлення залежностей через Poetry
```bash
poetry install
```

### 4. Запуск міграцій бази даних
```bash
poetry run alembic upgrade head
```

🏃 Запуск застосунку
Варіант А: Локально через Uvicorn
```bash
poetry run uvicorn app.main:app --reload
```

Варіант Б: Через Docker Compose (Рекомендовано)
Для запуску застосунку разом із PostgreSQL, Redis та worker'ами Celery:
```bash
docker-compose up --build -d
```

🧪 Запуск тестів та перевірка коду
Для запуску юніт- та інтеграційних тестів за допомогою Pytest:
```bash
poetry run pytest
```

Для перевірки дотримання стилю коду (Flake8):
```bash
poetry run flake8
```

📄 Документація API
Доступ до інтерактивної документації Swagger UI та ReDoc захищено за допомогою HTTP Basic Authentication. 
Використайте такі облікові дані для входу:
* **Логін (Username):** `admin`
* **Пароль (Password):** `admin`

Посилання на документацію:
* **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)