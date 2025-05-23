# Collaborative Event Management System 
A RESTful API for collaborative event management with authentication, role-based permissions, versioning, and change tracking. Built with FastAPI, SQLAlchemy, and supports real-time collaboration features. 

## How to Run 
### 1. Clone the Repository 
```bash 
git clone https://github.com/Alphazero99/NeoFI-backend-task.git cd NeoFI-backend-task
``` 

### 2. Create Virtual Environment 
```bash 
python -m venv venv # Windows venv\Scripts\activate # macOS/Linux source venv/bin/activate
``` 

### 3. Create the .env file 
```bash 

PROJECT_NAME="Collaborative Event Management API"
API_V1_STR="/api"

# Security
SECRET_KEY=your_secure_random_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=collaborative_events


# Rate limiting
RATE_LIMIT_PER_MINUTE=60

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
``` 

### 4. Install the dependencies 
```bash pip install -r requirements.txt 
```

### 5. Run the Application 
```bash uvicorn app.main:app --reload 
```
### 6. Run the test application 
```bash python test_api.py ```
