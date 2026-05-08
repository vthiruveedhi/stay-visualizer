# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

RUN useradd --create-home --uid 1000 app
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY static ./static

# Make the static dir writable by the non-root user so generated PNGs
# can be cached at runtime under static/generated/.
RUN mkdir -p /app/static/generated && chown -R app:app /app

USER app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
