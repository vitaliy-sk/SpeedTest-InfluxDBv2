FROM python:slim-buster
LABEL maintainer="msoufastai@gmail.com"

VOLUME /src/
COPY influxspeedtest.py requirements.txt config.ini /src/
ADD influxspeedtest /src/influxspeedtest
WORKDIR /src 

RUN deb add --no-cache --virtual .build-deps gcc musl-dev \
     && pip install cython \
     && pip install -r requirements.txt \
     && deb del .build-deps gcc musl-dev



CMD ["python", "-u", "/src/influxspeedtest.py"]
