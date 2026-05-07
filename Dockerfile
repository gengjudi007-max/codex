FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY README.md ./
COPY src ./src
COPY tests ./tests
COPY docs ./docs

RUN pip install --upgrade pip && pip install -e .

EXPOSE 8000

CMD ["python", "-m", "codex.api_gateway"]
