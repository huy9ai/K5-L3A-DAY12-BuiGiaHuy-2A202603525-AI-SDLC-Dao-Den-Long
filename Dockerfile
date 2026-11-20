FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml run.py ./
COPY src/ ./src/
COPY tests/ ./tests/
COPY scripts/ ./scripts/

EXPOSE 8000

CMD ["python3", "run.py", "--host", "0.0.0.0", "--port", "8000"]
