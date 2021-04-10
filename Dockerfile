FROM python:alpine
LABEL maintainer="msoufastai@gmail.com"

RUN apk add --no-cache --virtual .build-deps gcc musl-dev
RUN pip install cython

VOLUME /src/
COPY influxspeedtest.py requirements.txt config.ini /src/
ADD influxspeedtest /src/influxspeedtest
WORKDIR /src

RUN pip install -r requirements.txt
RUN apk del .build-deps gcc musl-dev

CMD ["python", "-u", "/src/influxspeedtest.py"]
