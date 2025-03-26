FROM python:latest
WORKDIR /workspace

RUN apt-get update && apt-get install -y cabextract

RUN pip install selenium beautifulsoup4
