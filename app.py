# Importing Libraries
import os

try:
    import psycopg2
except ImportError:  # pragma: no cover - optional dependency
    psycopg2 = None

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    def load_dotenv():
        return False

from flask import Flask, render_template, request
from openai import OpenAI

# Loading Environment Variables
load_dotenv()

# Making flask app variable
app = Flask(__name__)


def get_db_connection():
    if psycopg2 is None:
        print("psycopg2 is not installed; skipping database connection")
        return None

    try:
        database_url = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
        if database_url:
            return psycopg2.connect(database_url)

        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT") or "5432",
            sslmode="require",
            connect_timeout=10,
        )
        return conn
    except Exception as exc:
        print(f"Database connection failed: {exc}")
        return None


def init_db():
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS students (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    age TEXT,
                    course TEXT,
                    city TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        conn.commit()
        conn.close()
        return True
    except Exception as exc:
        print(f"Database initialization failed: {exc}")
        if conn:
            conn.close()
        return False


def generate_local_ai_response(prompt):
    text = str(prompt or "").strip().lower()

    if any(keyword in text for keyword in ["study", "plan", "schedule", "exam", "revision"]):
        return (
            "Here is a practical study plan: start with the most important topic, break it into small tasks, "
            "review one topic at a time, and set aside 20–30 minutes for focused practice each day."
        )

    if any(keyword in text for keyword in ["register", "student", "course", "college", "university"]):
        return (
            "You are making a strong start. Focus on one course at a time, keep your notes organized, and ask for help "
            "early if anything feels unclear."
        )

    return (
        "I can help with that. A simple next step is to list the main goal, break it into smaller actions, and tackle "
        "the first task right away."
    )


def build_ai_response(prompt):
    if not prompt or not str(prompt).strip():
        return "Please enter a question so I can help you."

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return generate_local_ai_response(prompt)

    try:
        client = OpenAI(api_key=api_key, timeout=60)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a warm, helpful assistant for a student registration website. "
                        "Answer clearly, politely, and concisely. "
                        "Use friendly formatting with short paragraphs or bullet points when helpful."
                    ),
                },
                {"role": "user", "content": str(prompt).strip()},
            ],
            temperature=0.8,
            max_tokens=260,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        print(f"AI request failed: {exc}")
        error_text = str(exc)
        if "401" in error_text or "invalid_api_key" in error_text.lower() or "api key" in error_text.lower():
            return generate_local_ai_response(prompt)
        return (
            "The AI service is currently unavailable, but your website is working. "
            "Please check the OpenAI API key or try again shortly."
        )


# Making route for home page
@app.route("/")
def home():
    return render_template("index.html", ai_response="")


# Making route for Submit:
@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name", "")
    email = request.form.get("email", "")
    age = request.form.get("age", "")
    course = request.form.get("course", "")
    city = request.form.get("city", "")

    ai_prompt = (
        f"Write a short, encouraging message for a student named {name} who is registering for {course} in {city}."
    )
    ai_message = build_ai_response(ai_prompt)

    init_db()
    conn = get_db_connection()
    if conn is None:
        return f"Data received. The database is not available right now, but here is an AI insight: {ai_message}"

    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO students(name,email,age,course,city) VALUES(%s,%s,%s,%s,%s)""",
                (name, email, age, course, city),
            )
        conn.commit()
        conn.close()
        return f"Data Saved. AI insight: {ai_message}"
    except Exception as exc:
        print(f"Database insert failed: {exc}")
        if conn:
            conn.close()
        return f"Data received but could not be stored: {exc}. AI insight: {ai_message}"


@app.route("/ai", methods=["POST"])
def ai():
    prompt = request.form.get("prompt", "")
    response_text = build_ai_response(prompt)
    return render_template("index.html", ai_response=response_text)


if __name__ == "__main__":
    app.run(debug=True)

