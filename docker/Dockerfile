# get the python image
FROM python:3.8-alpine

# environment variables
## prevent the pyc files
ENV PYTHONDONTWRITEBYTECODE 1
## prevent stdout and stderr buffering
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

# install all the dependencies regarding posgresql dev and more dev tools
RUN apk update \
    && apk add -U --no-cache \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev \
    nmap \
    nmap-scripts \
    && rm -f /var/cache/apk/*

# dependences
## update the pip just in case
RUN pip install --upgrade pip

## install the pipenvironment and the pipfile based on the .lock file, containing the versioning.
## if the lock is out-of-date, a new one will be created with the current versions instead of failing over.

RUN pip install pipenv

ADD ./Pipfile .
ADD ./Pipfile.lock .
RUN pipenv install --system --deploy --ignore-pipfile

## copy all the files into our new working directory
COPY ./src .
COPY ./docker/entrypoint.sh .

RUN chmod +x /usr/src/app/entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
