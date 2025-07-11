FROM python:3.12-alpine

WORKDIR /app
COPY requirements.txt .
RUN mkdir -p /data
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENTRYPOINT ["python", "main.py"]
