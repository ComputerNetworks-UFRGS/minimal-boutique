FROM python:3.11-slim

WORKDIR /app
COPY ./orders /app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]