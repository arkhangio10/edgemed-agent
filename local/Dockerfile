FROM python:3.11-slim

WORKDIR /app

COPY local/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY local/ ./local/

RUN mkdir -p /app/local/data /app/local/keys

ENV PYTHONPATH=/app
EXPOSE 8501 8000

CMD ["sh", "-c", "uvicorn local.local_api:app --host 0.0.0.0 --port 8000 & streamlit run local/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true"]
