
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import get_db_connection
from fastapi.middleware.cors import CORSMiddleware
import time
import psycopg2

app = FastAPI()

# CORS - allow frontend at port 3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class User(BaseModel):
    username: str
    password: str

@app.post("/create_user")
async def create_user(user: User):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (user.username, user.password))
        conn.commit()
        return {"message": "User created successfully!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.post("/login")
async def login(user: User):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (user.username, user.password))
        result = cur.fetchone()
        if result:
            return {"message": "Login successful!"}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.on_event("startup")
async def startup_event():
    print("Connecting to database...")
    retries = 5
    while retries > 0:
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(10) NOT NULL
                )
            """)
            conn.commit()
            cur.close()
            conn.close()
            print("Database initialized.")
            break
        except psycopg2.OperationalError as e:
            print("Database not ready, retrying...")
            retries -= 1
            time.sleep(2)
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="Database initialization failed.")
