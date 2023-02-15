# pull official base image
FROM python:3.10.9-alpine

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies if db is needed
RUN apk update \
    && apk add postgresql-client postgresql-dev gcc python3-dev musl-dev

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
COPY ./manage.py .
COPY requirements ./requirements

# ARG PRODUCTION
RUN pip install -r requirements.txt

# copy entrypoint.sh
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

# copy project
COPY . .

#RUN flake8 .
RUN python manage.py test

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
