FROM python:alpine
LABEL maintainer="msoufastai@gmail.com"

RUN apk add --no-cache --virtual .build-deps gcc musl-dev \
     && pip install cython \
     && pip install -r requirements.txt \
     && apk del .build-deps gcc musl-dev

VOLUME /src/
COPY influxspeedtest.py requirements.txt config.ini /src/
ADD influxspeedtest /src/influxspeedtest
WORKDIR /src 

CMD ["python", "-u", "/src/influxspeedtest.py"]
