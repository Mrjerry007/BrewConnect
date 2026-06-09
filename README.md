# BrewConnect

BrewConnect is a social discovery platform designed to help you connect with like-minded individuals nearby. By combining location-based proximity and machine-learning interest matching, BrewConnect surfaces the most relevant potential connections around you, whether you're at a coffee shop, an airport, or a co-working space. It also features real-time messaging using WebSockets.

## Features
- **Proximity-Based Discovery**: Find active users within your immediate radius.
- **Interest Matching**: Ranks nearby users based on shared interests and profile descriptions using TF-IDF and Cosine Similarity.
- **Real-time Messaging**: Chat instantly with your connections via WebSockets.
- **Active Session Management**: Easily toggle your visibility and update your current location or mood.
- **FastAPI Backend**: High-performance backend providing seamless and fast API experiences.

## Prerequisites
- **Python 3.8+**

## Installation and Setup

1. **Clone the repository (or navigate to the project folder)**:
   ```bash
   cd BrewConnect
   ```

2. **Create a virtual environment (Recommended)**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   Install the required Python packages from the `requirements.txt` file.
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Start the FastAPI server**:
   You can start the server using Python. The application will automatically create the necessary SQLite database upon initialization.
   ```bash
   python main.py
   ```
   *Alternatively, you can run uvicorn directly:*
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Access the application**:
   - Web App UI: [http://localhost:8000](http://localhost:8000)
   - API Documentation (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
   - Alternative API Docs (ReDoc): [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Project Structure
- `main.py`: Entry point for the FastAPI application and route definitions.
- `database.py`: Database connection and initialization setup.
- `models.py`: SQLAlchemy database models.
- `schemas.py`: Pydantic models for request/response validation.
- `config.py`: Configuration and environment variables.
- `ml_matching.py`: Machine learning logic for ranking nearby users.
- `static/`: Contains the frontend HTML/CSS/JS (e.g., `index.html`).
