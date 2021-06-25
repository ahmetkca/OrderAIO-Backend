FROM python:3.7

COPY requirements.txt /app/requirements.txt

RUN pip3 install -r ./app/requirements.txt

EXPOSE 80:80

COPY ./app /app

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]