FROM python:slim-buster
LABEL maintainer="msoufastai@gmail.com"

VOLUME /src/
COPY influxspeedtest.py requirements.txt config.ini /src/
RUN apt-get update \
     && apt-get upgrade \
     && apt-get install gcc \
     && pip install cython \
     && pip install -r requirements.txt \
     && apt-get remove gcc


VOLUME /src/
COPY influxspeedtest.py requirements.txt config.ini /src/
ADD influxspeedtest /src/influxspeedtest
WORKDIR /src 





CMD ["python", "-u", "/src/influxspeedtest.py"]
