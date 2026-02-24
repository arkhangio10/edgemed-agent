FROM python:3.11-slim

WORKDIR /app

COPY cloud/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY cloud/ ./cloud/

ENV PYTHONPATH=/app
EXPOSE 8080

CMD ["uvicorn", "cloud.main:app", "--host", "0.0.0.0", "--port", "8080"]
