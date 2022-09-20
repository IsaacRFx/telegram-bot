FROM python:3.10.7-bullseye

RUN apt-get update -y \
        && pip install --upgrade pip \
        && mkdir /app

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

CMD python devbot.py