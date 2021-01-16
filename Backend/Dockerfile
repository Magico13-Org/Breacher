FROM python:3.9

EXPOSE 5000

COPY ./requirements_web.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENV FLASK_APP webapi.py

ENTRYPOINT [ "flask", "run", "--host=0.0.0.0" ]