FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 10000

# Jalankan FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
