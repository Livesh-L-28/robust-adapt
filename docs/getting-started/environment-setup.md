# Clean Environment Setup

We strongly recommend deploying ROBUST-ADAPT inside an isolated Python virtual environment or container to avoid dependency conflicts.

---

## 1. Setting Up a Virtual Environment

### Using Python Standard Library (`venv`)

=== "Linux / macOS"
    ```bash
    # Create isolated virtual environment
    python3 -m venv .venv

    # Activate virtual environment
    source .venv/bin/activate

    # Upgrade pip to latest standard
    pip install --upgrade pip

    # Install core package
    pip install robust-adapt
    ```

=== "Windows (PowerShell)"
    ```powershell
    # Create isolated virtual environment
    py -3.14 -m venv .venv

    # Activate virtual environment
    .venv\Scripts\Activate.ps1

    # Upgrade pip to latest standard
    python -m pip install --upgrade pip

    # Install core package
    pip install robust-adapt
    ```

---

## 2. Setting Up with Modern Package Managers

### Using `uv`
```bash
# Create and activate environment with uv
uv venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows

# Add core package
uv pip install robust-adapt
```

---

## 3. Docker Containerization

For containerized microservices and edge gateways:

```dockerfile
FROM python:3.12-slim-bookworm

WORKDIR /app

# Install minimal core runtime
RUN pip install --no-cache-dir robust-adapt

# Copy application code
COPY . /app

CMD ["python", "main.py"]
```
- **Image Size**: The base Python image with `robust-adapt` and `numpy` is $<160\text{ MB}$, compared to multi-gigabyte PyTorch/CUDA images.
