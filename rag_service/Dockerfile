FROM python:3.11-slim

WORKDIR /app

COPY rag_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY rag_service/ ./rag_service/
COPY .env .

EXPOSE 8000

CMD ["uvicorn", "rag_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
