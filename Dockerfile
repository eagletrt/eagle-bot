FROM python:3.12-alpine

WORKDIR /app
COPY requirements.txt .
RUN mkdir -p /data
RUN pip install --no-cache-dir -r requirements.txt
# TODO: add better requirements management
RUN pip install --no-cache-dir urllib3==2.2.2 six==1.16.0
COPY . .

ENTRYPOINT ["python", "main.py"]
