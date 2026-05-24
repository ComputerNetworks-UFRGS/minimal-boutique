FROM python:3.11-slim

WORKDIR /app
COPY ./products /app
RUN pip install --no-cache-dir -r requirements.txt

# Set production environment variables
ENV FLASK_APP=app.py \
    FLASK_ENV=production

# Use Gunicorn to serve the app
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5001", "app:app"]