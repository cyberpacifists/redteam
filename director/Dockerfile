FROM python:3.8-alpine

WORKDIR /app
ADD requirements.txt /app
RUN pip install --no-cache -r /app/requirements.txt -t /app
COPY src/ /app

ENTRYPOINT [ "python", "main.py" ]
