# Build and Run Locally

This project is a **Python FastAPI** application with a static HTML/JS frontend. It does **not** require Node.js or `npm`.

## Prerequisites

- **Python 3.9+**
- **Git**

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/dhruvhaldar/alfven.git
    cd alfven
    ```

2.  **Create a Virtual Environment (Recommended):**
    
    This isolates dependencies from your system Python.

    **Windows:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

    **macOS / Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

    *To exit the virtual environment later, run:* `deactivate`

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

Start the development server using `uvicorn`. The application serves the static frontend from the `public/` directory and the API from `api/index.py`.

```bash
uvicorn api.index:app --reload
```

## Accessing the App

Open your browser and navigate to:

> **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

## Project Structure

- `api/`: Python backend (FastAPI endpoints).
- `public/`: Static frontend assets (HTML, CSS, JS).
- `alfven/`: Core physics modules.
- `requirements.txt`: Python package dependencies.
- `vercel.json`: Deployment configuration for Vercel.
