## servertest1

Basic Flask service exposing:

- **`GET /`**: Renders a simple HTML page.
- **`GET /version`**: Returns JSON with the service status and version.

### Run locally

1. **Create a virtual environment (optional but recommended)**:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

3. **Start the Flask service**:

```bash
python app.py
```

4. **Access the service**:

- **HTML page**: `http://localhost:8080/`
- **Status endpoint**: `http://localhost:8080/version`
