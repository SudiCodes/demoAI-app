# Dockerfile for Flask app

FROM python:3.9

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r req_amilinux_p39.txt 

EXPOSE 8000

CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:8000", "app:app"]




