import argparse
import sys

from influxspeedtest.InfluxdbSpeedtest import InfluxdbSpeedtest
from influxspeedtest.config import config


def parse_args():
    parser = argparse.ArgumentParser(
        description='Run Speedtest once and print the InfluxDB payload without writing it'
    )
    parser.add_argument(
        '--server',
        action='append',
        help='Speedtest server id to test against. Can be passed more than once or as a comma-separated list.'
    )
    return parser.parse_args()


def selected_servers(server_args):
    if not server_args:
        return config.servers or [None]

    servers = []
    for value in server_args:
        servers.extend(server.strip() for server in value.split(',') if server.strip())

    return servers or [None]


def main():
    args = parse_args()
    collector = InfluxdbSpeedtest(skip_influxdb=True)

    success = True
    for server in selected_servers(args.server):
        if not collector.run_speed_test(server=server):
            success = False

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
