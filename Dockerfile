FROM python:3.13.3-slim-bookworm 

LABEL maintainer="mahan78ma@gmail.com"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 
ENV PIP_DEFAULT_TIMEOUT=200

WORKDIR /code

RUN apt-get update && apt-get install -y \
    binutils \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /code/

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . /code/
# `/code` is the project's working directory.
# Since `manage.py` is inside the `backend` directory,
# configure `docker-compose.yml` to run:
#
# command: python backend/manage.py runserver 0.0.0.0:8000
EXPOSE 8000