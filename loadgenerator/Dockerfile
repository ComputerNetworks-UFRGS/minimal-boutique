FROM python:3.11-slim
WORKDIR /loadgen

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["locust", "--host", "http://backend:5000", "--headless", "-u", "1000", "-r", "10"]