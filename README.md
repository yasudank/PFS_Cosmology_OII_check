# Image Rater

This is a simple web application to rate images.

## How to run

### 1. Add Images
Place the image files you want to rate into the `sample_images` directory.

### 2. Backend Setup
First, install the required Python packages. It's recommended to use a virtual environment.

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate 

# Install dependencies
pip install -r backend/requirements.txt
```

#### Using PostgreSQL (Optional)

By default, the application uses a simple SQLite database. To switch to PostgreSQL, follow these steps:

1.  **Install the Database Driver:**
    Install the necessary Python driver for PostgreSQL. This is listed as an optional dependency in `backend/requirements.txt`.

    ```bash
    pip install psycopg2-binary
    ```

2.  **Set the Database URL:**
    The application is configured via the `DATABASE_URL` environment variable. Before running the backend, set this variable to point to your PostgreSQL instance.

    **Example:**
    ```bash
    # Replace with your actual database credentials
    export DATABASE_URL="postgresql://your_user:your_password@localhost:5432/image_rater_db"
    
    # Now, run the backend
    uvicorn backend.main:app --reload
    ```

    The format for the URL is `postgresql://<user>:<password>@<host>:<port>/<dbname>`.

    When the backend starts, it will automatically use this URL to connect to PostgreSQL and create the necessary tables. For production use, you should use a database migration tool like Alembic to manage schema changes instead of the automatic `drop_all`/`create_all` used in this prototype.


### 3. Run Backend
Start the FastAPI backend server.

```bash
uvicorn backend.main:app --reload
```
The server will be running at `http://localhost:8000`.

### 4. Frontend Setup
Navigate to the frontend directory and install the dependencies.

```bash
cd frontend
npm install
```

### 5. Run Frontend
Start the React development server.

```bash
# From the 'frontend' directory
npm start
```
The application will open automatically in your browser at `http://localhost:3000`.

Now you can start rating your images!
