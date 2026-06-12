FROM python:3.8-alpine AS dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir --user --no-warn-script-location -r requirements.txt

FROM python:3.8-alpine AS build-image
COPY --from=dependencies /root/.local /root/.local
COPY speedtest-cli/ookla-speedtest-linux-x86_64/speedtest /usr/local/bin/speedtest
COPY influxspeedtest /home/influxspeedtest
COPY influxspeedtest.py /home/

RUN chmod +x /usr/local/bin/speedtest

CMD [ "python", "-u", "/home/influxspeedtest.py" ]
