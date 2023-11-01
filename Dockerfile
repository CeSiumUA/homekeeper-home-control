FROM python:3.11-alpine

# Set the time zone to Kyiv
RUN apk add --no-cache tzdata
ARG TZ=Europe/Kiev

ENV TZ=${TZ}

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "src/main.py"]