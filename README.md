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

5. **Useful links**:

- [Openrouter](https://openrouter.ai/)
- [Modelo deepseek gratuito](https://openrouter.ai/nex-agi/deepseek-v3.1-nex-n1:free)
- [Modelo gratuito Amazon con procesamiento de imagenes](https://openrouter.ai/amazon/nova-2-lite-v1:free)
- [Busqueda de modelos gratuitos en openrouter](https://openrouter.ai/models?q=free) 
