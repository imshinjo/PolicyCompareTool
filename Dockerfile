FROM python:latest
WORKDIR /mnt

RUN apt-get update && apt-get install -y cabextract p7zip-full

RUN pip install selenium beautifulsoup4
