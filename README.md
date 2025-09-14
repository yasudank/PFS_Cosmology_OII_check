# Image Rater

This is a simple web application to rate images.

## Configuration (Environment Variables)

This application is configured using environment variables. This is crucial for running the frontend and backend on different machines, or when using a server IP address instead of `localhost`.

### Frontend Configuration

In the `frontend/` directory, create a file named `.env`. This file stores the configuration for the React application.

-   **`REACT_APP_API_BASE_URL`**: **Required**. This is the full URL of the backend server that the frontend will make API calls to.

    *Example `frontend/.env` file:*
    ```
    REACT_APP_API_BASE_URL=http://192.168.1.10:8000
    ```

    **Important:** After creating or changing the `.env` file, you must restart the frontend development server for the changes to take effect.

### Backend Configuration

These variables should be set in your terminal *before* running the `uvicorn` command.

-   **`DATABASE_URL`**: The connection string for the database.
    -   **Default**: If this is not set, the application will create and use a local SQLite file (`image_rater.db`).
    -   **PostgreSQL Example**: `postgresql://user:password@host:port/dbname`
    -   (See the "Using PostgreSQL" section below for more details).

-   **`ALLOWED_ORIGINS`**: A comma-separated list of web addresses (origins) that are allowed to connect to the backend API (CORS policy).
    -   **For development (less secure)**: To allow any client to connect, you can use a wildcard.
        ```bash
        export ALLOWED_ORIGINS="*"
        ```
    -   **For specific clients (more secure)**: List the specific URLs of your frontend applications.
        ```bash
        export ALLOWED_ORIGINS="http://localhost:3000,http://192.168.1.10:3000"
        ```

## How to run

### 1. Add Images
Place the image files you want to rate into the `sample_images` directory. Subdirectories are also scanned.

### 2. Backend Setup
First, install the required Python packages. It's recommended to use a virtual environment.

```bash
# (Optional) Create and activate a virtual environment
python -m venv venv
source venv/bin/activate 

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Run Backend
Ensure you have set the necessary environment variables as described in the **Configuration** section above.

```bash
# Example for running with PostgreSQL and allowing specific origins
export DATABASE_URL="postgresql://your_user:your_password@localhost:5432/image_rater_db"
export ALLOWED_ORIGINS="http://localhost:3000,http://<your_server_ip>:3000"

# Start the server to listen on all network interfaces
uvicorn backend.main:app --reload --host 0.0.0.0
```

### 4. Frontend Setup
Navigate to the frontend directory, create your `.env` file as described in the **Configuration** section, and install the dependencies.

```bash
cd frontend
npm install
```

### 5. Run Frontend
Start the React development server. It will automatically use the variables from your `.env` file.

```bash
# From the 'frontend' directory
npm start
```

---

### Using PostgreSQL (Optional)

To switch to PostgreSQL, follow these steps:

1.  **Install the Database Driver:**
    Install the necessary Python driver for PostgreSQL. This is listed as an optional dependency in `backend/requirements.txt`.

    ```bash
    pip install psycopg2-binary
    ```

2.  **Set the `DATABASE_URL` Environment Variable:**
    As described in the main configuration section, set this variable before running the backend.

    **Example:**
    ```bash
    export DATABASE_URL="postgresql://your_user:your_password@localhost:5432/image_rater_db"
    ```

    The format for the URL is `postgresql://<user>:<password>@<host>:<port>/<dbname>`.

    For production use, you should use a database migration tool like Alembic to manage schema changes instead of the automatic `drop_all`/`create_all` used in this prototype.
