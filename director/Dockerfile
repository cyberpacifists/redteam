FROM python:3.8-alpine

WORKDIR /app
ADD Pipfile.lock Pipfile /app/
RUN pip install pipenv \
    && pipenv install --system --deploy --ignore-pipfile
COPY director/ /app

ENTRYPOINT [ "python", "-u", "main.py" ]
