FROM python:3.8-alpine AS dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir --user --no-warn-script-location -r requirements.txt

FROM python:3.8-alpine AS build-image
COPY --from=dependencies /root/.local /root/.local
COPY influxspeedtest /home/influxspeedtest
COPY influxspeedtest.py /home/

CMD [ "python", "-u", "/home/influxspeedtest.py" ]
