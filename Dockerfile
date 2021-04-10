FROM python:slim
LABEL maintainer="msoufastai@gmail.com"
RUN apt-get update \
     && apt-get upgrade \
     && apt-get install gcc -y \
     && apt-get clean


VOLUME /src/
COPY influxspeedtest.py requirements.txt config.ini /src/
ADD influxspeedtest /src/influxspeedtest
WORKDIR /src 

RUN pip install cython \
     && pip install -r requirements.txt \
     && apt-get remove gcc -y \
     && apt-get clean

CMD ["python", "-u", "/src/influxspeedtest.py"]
