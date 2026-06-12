import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
from influxdb_client import InfluxDBClient as InfluxDBClient2
from influxdb_client.client.write_api import SYNCHRONOUS
from requests import ConnectTimeout, ConnectionError

from influxspeedtest.common import log
from influxspeedtest.config import config

SPEEDTEST_TIMEOUT = 300


class SpeedtestCliError(Exception):
    pass


class InfluxdbSpeedtest():

    def __init__(self, skip_influxdb=False):

        self.skip_influxdb = skip_influxdb
        self.influx_client = None if skip_influxdb else self._get_influx_connection()
        self.speedtest_binary = self._get_speedtest_binary()
        self.results = None

    def _get_influx_connection(self):
        """
        Create an InfluxDB connection and test to make sure it works.
        We test with the get all users command.  If the address is bad it fails
        with a 404.  If the user doesn't have permission it fails with 401
        :return:
        """
        if config.influx_version == 1:
            influx = InfluxDBClient(
                config.influx_address,
                config.influx_port,
                database=config.influx_database,
                ssl=config.influx_ssl,
                verify_ssl=config.influx_verify_ssl,
                username=config.influx_user,
                password=config.influx_password,
                timeout=5)
        elif config.influx_version == 2:
            log.debug('InfluxDB V2.0 is selected')
            protocol = "http://"
            if config.influx_ssl:
                protocol="https://"
            else:
                protocol="http://"    
            
            influx = InfluxDBClient2(
                url= protocol + config.influx_address + ":" + str(config.influx_port),
                token=config.influx_token,
                org=config.influx_org)
            
        try:
            log.debug('Testing connection to InfluxDb using provided credentials')
            if config.influx_version == 1:
                influx.get_list_users()  # TODO - Find better way to test connection and permissions
            else:
                influx.health()
            log.debug('Successful connection to InfluxDb')
        except (ConnectTimeout, InfluxDBClientError, ConnectionError) as e:
            if isinstance(e, ConnectTimeout):
                log.critical('Unable to connect to InfluxDB at the provided address (%s)', config.influx_address)
            elif e.code == 401:
                log.critical(e)
                log.critical('Unable to connect to InfluxDB with provided credentials')
            else:
                log.critical('Failed to connect to InfluxDB for unknown reason')

            sys.exit(1)

        return influx

    def _get_speedtest_binary(self):
        """
        Finds the Ookla Speedtest CLI binary.
        :return: str
        """
        candidates = []
        configured_binary = os.getenv('SPEEDTEST_BINARY')
        if configured_binary:
            candidates.append(Path(configured_binary).expanduser())

        repo_root = Path(__file__).resolve().parent.parent
        system = platform.system()
        if system == 'Linux':
            candidates.append(repo_root / 'speedtest-cli' / 'ookla-speedtest-linux-x86_64' / 'speedtest')
        elif system == 'Darwin':
            candidates.append(repo_root / 'speedtest-cli' / 'ookla-speedtest-macosx-universal' / 'speedtest')

        path_binary = shutil.which('speedtest')
        if path_binary:
            candidates.append(Path(path_binary))

        for candidate in candidates:
            if candidate.is_file() and os.access(candidate, os.X_OK):
                log.debug('Using Speedtest CLI binary: %s', candidate)
                return str(candidate)

        log.critical('Unable to find Speedtest CLI binary. Set SPEEDTEST_BINARY or install speedtest in PATH.')
        sys.exit(1)

    def _speedtest_command(self, server=None):
        """
        Builds the Speedtest CLI command.
        :param server: Server to test against
        :return: list
        """
        command = [
            self.speedtest_binary,
            '--accept-license',
            '--accept-gdpr',
            '--format=json',
            '--progress=no'
        ]

        server_id = str(server).strip() if server else ''
        if server_id:
            command.extend(['--server-id', server_id])

        return command

    def _parse_speedtest_output(self, output):
        """
        Parses JSON output from Speedtest CLI.
        :param output: str
        :return: dict
        """
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            start = output.find('{')
            end = output.rfind('}')
            if start != -1 and end != -1:
                return json.loads(output[start:end + 1])
            raise

    def _run_speedtest_cli(self, server=None):
        """
        Runs Speedtest CLI and returns its JSON result.
        :param server: Server to test against
        :return: dict
        """
        command = self._speedtest_command(server)
        log.debug('Running Speedtest CLI: %s', ' '.join(command))

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=SPEEDTEST_TIMEOUT
            )
        except subprocess.TimeoutExpired as e:
            raise SpeedtestCliError('Speedtest CLI timed out after {} seconds'.format(e.timeout))
        except OSError as e:
            raise SpeedtestCliError('Unable to run Speedtest CLI: {}'.format(e))

        output = completed.stdout.strip()
        error_output = completed.stderr.strip()
        if completed.returncode != 0:
            raise SpeedtestCliError(error_output or output or 'Exited with code {}'.format(completed.returncode))

        try:
            return self._parse_speedtest_output(output or error_output)
        except json.JSONDecodeError as e:
            raise SpeedtestCliError('Unable to parse Speedtest CLI JSON output: {}'.format(e))

    def _normalize_results(self, raw_results):
        """
        Converts Ookla Speedtest CLI JSON to the legacy result shape.
        :param raw_results: dict
        :return: dict
        """
        server = raw_results.get('server', {})
        download = raw_results.get('download', {})
        upload = raw_results.get('upload', {})
        ping = raw_results.get('ping', {})

        server_location = server.get('location') or server.get('name') or ''
        server_sponsor = server.get('name') or ''

        return {
            'download': download.get('bandwidth', 0) * 8,
            'bytes_received': download.get('bytes', 0),
            'upload': upload.get('bandwidth', 0) * 8,
            'bytes_sent': upload.get('bytes', 0),
            'server': {
                'latency': ping.get('latency', 0),
                'id': str(server.get('id', '')),
                'name': server_location,
                'country': server.get('country', ''),
                'sponsor': server_sponsor
            },
            'client': {
                'isp': raw_results.get('isp', '')
            }
        }

    def send_results(self):
        """
        Formats the payload to send to InfluxDB
        :rtype: None
        """
        result_dict = self.results

        input_points = [
            {
                'measurement': 'speed_test_results',
                'fields': {
                    'download': result_dict['download'],
                    'bytes_received': result_dict['bytes_received'],
                    'upload': result_dict['upload'],
                    'bytes_sent': result_dict['bytes_sent'],
                    'ping': result_dict['server']['latency']#,
                    #'isp': result_dict['client']['isp'],
                    #'server': result_dict['server']['id'],
                    #'server_name': result_dict['server']['name'],
                    #'server_country': result_dict['server']['country'],
                    #'server_sponsor': result_dict['server']['sponsor']
                },
                'tags': {
                    'server': result_dict['server']['id'],
                    'server_name': result_dict['server']['name'],
                    'server_country': result_dict['server']['country'],
                    'server_sponsor': result_dict['server']['sponsor'],
                    'isp': result_dict['client']['isp']
                }
            }
        ]

        self.write_influx_data(input_points)

    def run_speed_test(self, server=None):
        """
        Performs the speed test with the provided server
        :param server: Server to test against
        """
        log.info('Starting Speed Test For Server %s', server)

        try:
            raw_results = self._run_speedtest_cli(server)
        except SpeedtestCliError as e:
            log.error('Speedtest CLI failed for server %s: %s', server, e)
            return False

        self.results = self._normalize_results(raw_results)
        self.send_results()

        results = self.results
        log.info('Download: %sMbps - Upload: %sMbps - Latency: %sms',
                 round(results['download'] / 1000000, 2),
                 round(results['upload'] / 1000000, 2),
                 results['server']['latency']
                 )

        return True



    def write_influx_data(self, json_data):
        """
        Writes the provided JSON to the database
        :param json_data:
        :return: None
        """
        log.debug(json_data)

        if self.skip_influxdb:
            print('InfluxDB write skipped. Payload that would be written:')
            print(json.dumps(json_data, indent=2, sort_keys=True))
            return

        try:
            if config.influx_version == 1:
                self.influx_client.write_points(json_data)
            else:
                write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
                write_api.write(config.influx_bucket,config.influx_org,json_data)
        except (InfluxDBClientError, ConnectionError, InfluxDBServerError) as e:
            if hasattr(e, 'code') and e.code == 404:
                log.error('Database %s Does Not Exist.  Attempting To Create', config.influx_database)
                self.influx_client.create_database(config.influx_database)
                self.influx_client.write_points(json_data)
                return

            log.error('Failed To Write To InfluxDB')
            print(e)

        log.debug('Data written to InfluxDB')

    def run(self):

        while True:
            if not config.servers:
                self.run_speed_test()
            else:
                for server in config.servers:
                    self.run_speed_test(server)
            log.info('Waiting %s seconds until next test', config.delay)
            time.sleep(config.delay)
