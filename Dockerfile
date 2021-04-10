FROM python:slim
LABEL maintainer="msoufastai@gmail.com"
RUN apt-get update \
     && apt-get upgrade \
     && apt-get install gcc

VOLUME /src/
COPY influxspeedtest.py requirements.txt config.ini /src/
ADD influxspeedtest /src/influxspeedtest
WORKDIR /src 

RUN pip install cython \
     && pip install -r requirements.txt \
     && apt-get remove gcc

CMD ["python", "-u", "/src/influxspeedtest.py"]
