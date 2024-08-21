FROM python:3.10-slim as build

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
	      build-essential gcc 

WORKDIR /usr/app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

CMD [ "python", "main.py" ]
