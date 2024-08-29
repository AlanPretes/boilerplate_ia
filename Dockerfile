FROM python:3.10-slim

RUN apt-get update -y
RUN apt-get install -y gcc libpq-dev
RUN apt-get install -y libgl1-mesa-glx
RUN apt-get install -y libglib2.0-0
RUN rm -rf /var/lib/apt/lists/*

RUN groupadd -r ias_group && useradd -r -g ias_group ias_user

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R ias_user:ias_group /app

USER ias_user
