**Speedtest.net Collector For InfluxDB and Grafana**
------------------------------

This tool is a wrapper for speedtest-cli which allows you to run periodic speedtets and save the results to Influxdb
**+ Extended with support InfluxDB v2**

## Configuration within config.ini

#### GENERAL
|Key            |Description                                                                                                         |
|:--------------|:-------------------------------------------------------------------------------------------------------------------|
|Delay          |Seconds between speedtests (default 30 min)                                                                         |
#### INFLUXDB
|Key            |Description                                                                                                         |
|:--------------|:-------------------------------------------------------------------------------------------------------------------|
|Version        |1 or 2                                                                                                      |
|Address        |InfluxDB host or container name                                                                                     |
|Token        |InfluxDB2.0 Token with Read/Write                                                                                     |
|Organization        |InfluxDB2.0 Organization to connect to                                                                                     |
|Bucket        |InfluxDB2.0 Bucket to write to                                                                                     |
|Port           |InfluxDB port default 8086                                                                                          |
|Database       |Database to write collected stats to                                                                                |
|Username       |User that has access to the database                                                                                |
|Password       |Password for above user                                                                                             |
#### SPEEDTEST
|Key            |Description                                                                                                         |
|:--------------|:-------------------------------------------------------------------------------------------------------------------|
|Server         |Comma sperated list of servers.  Leave blank for auto                                                               |
|Share          |Upload results to speedtest.net and retrieve url                                                                    |
#### LOGGING
|Key            |Description                                                                                                         |
|:--------------|:-------------------------------------------------------------------------------------------------------------------|
|Level          |Set how verbose the console output is                                                           |


## Requirements

[influxdb](https://hub.docker.com/_/influxdb) 

[grafana](https://hub.docker.com/r/grafana/grafana)


## Usage 

1. Create config.ini using [reference](https://github.com/vitaliy-sk/SpeedTest-InfluxDBv2/blob/master/config.ini)
2. Run with docker or use compose below 

Sample docker-compose file

```yaml
version: '3.7'

services:

  speedtest:
    image: techh/speedtest-influxdb2:master
    restart: always
    network_mode: host 
    volumes:
      - ./config.ini:/config.ini
```

