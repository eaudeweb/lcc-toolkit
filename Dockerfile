FROM python:3
ENV PYTHONUNBUFFERED 1
RUN apt-get update
RUN apt-get install -y build-essential libpoppler-cpp-dev pkg-config python-dev\
 nodejs npm
RUN mkdir /code
WORKDIR /code
ADD . /code/
RUN pip install -r requirements-dev.txt
RUN npm install -g grunt-cli
RUN npm install
RUN ln -s /usr/bin/nodejs /usr/bin/node
