FROM python:3.12-alpine

WORKDIR /app

ENV TZ=Europe/Warsaw
RUN apk add --no-cache tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
