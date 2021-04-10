FROM python:alpine
LABEL maintainer="msoufastai@gmail.com"

VOLUME /src/
COPY influxspeedtest.py requirements.txt config.ini /src/
ADD influxspeedtest /src/influxspeedtest
WORKDIR /src 

RUN apk add --no-cache --virtual .build-deps gcc musl-dev \
     && pip install cython \
     && pip install -r requirements.txt \
     && apk del .build-deps gcc musl-dev



CMD ["python", "-u", "/src/influxspeedtest.py"]
