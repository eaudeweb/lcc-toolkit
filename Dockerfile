FROM python:3-slim
MAINTAINER "Eau de Web" <office@eaudeweb.ro>

ENV PYTHONUNBUFFERED=1 \
    WORK_DIR=/opt/lcct \
    NODE_ENV=prod

RUN runDeps="curl build-essential libpoppler-cpp-dev pkg-config postgresql-client" \
    && apt-get update \
    && apt-get install -y --no-install-recommends $runDeps \
    && curl -sL https://deb.nodesource.com/setup_8.x | bash - \
    && apt-get install -y nodejs \
    && rm -vrf /var/lib/apt/lists/*

RUN mkdir -p $WORK_DIR \
    && mkdir -p /media/uploadfiles \
    && mkdir -p /var/www/

COPY ./docker/entrypoint.sh /bin/

COPY requirements* package.json Gruntfile.js $WORK_DIR/
WORKDIR $WORK_DIR
RUN pip install --no-cache-dir -r requirements-dep.txt \
    && npm install -g grunt-cli \
    && npm install

ADD . $WORK_DIR

RUN grunt $NODE_ENV

ENTRYPOINT ["entrypoint.sh"]
CMD ["run"]
