# Marketing Agent (The Scribe)

This package contains the "Scribe" agent, which is responsible for content generation and maintaining brand voice.

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up Environment Variables:**
    Create a `.env` file in this directory and add the following variables:
    ```
    OPENAI_API_KEY="your_openai_api_key"
    DATABASE_URL="postgresql://user:password@host:port/database"
    ```
    Replace the values with your actual OpenAI API key and PostgreSQL database URL.

3.  **Initialize the Database:**
    Run the following command to initialize the PostgreSQL database with the required schema and seed it with sample data:
    ```bash
    python init_db.py
    ```

## Running the Agent

To run the agent as a service, use the `main.py` file and a uvicorn server:
```bash
uvicorn main:app --reload
```
The API documentation will be available at `http://127.0.0.1:8000/docs`.
