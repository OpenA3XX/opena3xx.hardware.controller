import logging
import os
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from ipaddress import IPv4Network
from typing import Optional, Tuple
import time
import netifaces as ni

from opena3xx.exceptions import OpenA3XXNetworkingException
from opena3xx.http import OpenA3xxHttpClient


class OpenA3XXNetworkingClient:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def start_api_discovery(self) -> Tuple[str, str, int]:
        try:
            scheme = os.getenv("OPENA3XX_API_SCHEME", "http")
            env_host = os.getenv("OPENA3XX_API_HOST")
            port = int(os.getenv("OPENA3XX_API_PORT", "5000"))
            self.logger.info(f"Discovery parameters: scheme={scheme}, env_host={env_host}, port={port}")

            if env_host:
                self.logger.info(f"Using OPENA3XX_API_HOST override: {env_host}:{port}")
                if self.__ping_request_target(scheme, env_host, port):
                    return scheme, env_host, port
                raise OpenA3XXNetworkingException(
                    f"API at {scheme}://{env_host}:{port} not responding to ping")

            interface = self.__discover_default_interface()
            local_ip, netmask = self.__discover_local_ip_and_netmask(interface)
            network = self.__compute_network(local_ip, netmask)
            self.logger.info(f"Scanning subnet {network} for OpenA3XX API on port {port}")
            total_hosts_count = sum(1 for _ in network.hosts())
            self.logger.info(f"Total hosts to scan: {total_hosts_count}")
            t0 = time.monotonic()
            host = self.__scan_network_for_api(scheme, network, port)
            duration = time.monotonic() - t0
            self.logger.info(f"Scan completed in {duration:.2f}s")
            if host:
                return scheme, host, port
            self.logger.info("OpenA3XX API not found on local subnet; will retry after controller backoff")
            raise OpenA3XXNetworkingException("OpenA3XX API not found on local subnet")
        except Exception as ex:
            raise OpenA3XXNetworkingException(ex)

    def __ping_request_target(self, scheme: str, target_ip: str, target_port: int) -> bool:
        try:
            http_client = OpenA3xxHttpClient(scheme, target_ip, target_port)
            self.logger.debug(f"Sending ping request to {scheme}://{target_ip}:{target_port}/core/heartbeat/ping")
            r = http_client.send_ping_request(scheme, target_ip, target_port)
            # Accept any HTTP 200 as success; log a snippet for diagnostics
            if r.status_code == 200:
                snippet = (r.text or "")[:80].replace("\n", " ")
                self.logger.info(f"Ping OK from {target_ip}:{target_port} (body starts with): '{snippet}'")
                return True
            self.logger.info(f"Ping failed from {target_ip}:{target_port} status={r.status_code}")
            return False
        except Exception as ex:
            self.logger.critical(f"Ping error for {target_ip}:{target_port}: {ex}")
            return False

    def __scan_network_for_api(self, scheme: str, network: IPv4Network, port: int) -> Optional[str]:
        self.logger.info("Started Scanning Network")
        # small pool to avoid overwhelming the Pi
        with ThreadPoolExecutor(max_workers=64) as executor:
            futures = {}
            total_hosts = 0
            for ip in network.hosts():
                future = executor.submit(self.__probe_host, str(ip), port)
                futures[future] = str(ip)
                total_hosts += 1
            self.logger.debug(f"Submitted probes for {total_hosts} hosts")
            processed = 0
            for future in as_completed(futures):
                host = futures[future]
                try:
                    open_port = future.result()
                    processed += 1
                    if processed % 64 == 0:
                        self.logger.debug(f"Probes completed: {processed}/{total_hosts}")
                    if open_port:
                        self.logger.info(f"Found open port on {host}:{port}, verifying API ping")
                        if self.__ping_request_target(scheme, host, port):
                            return host
                except Exception:
                    continue
        return None

    def __discover_default_interface(self) -> str:
        gateways = ni.gateways()
        default = gateways.get('default', {})
        if ni.AF_INET in default and default[ni.AF_INET]:
            iface = default[ni.AF_INET][1]
            self.logger.debug(f"Default IPv4 gateway interface detected: {iface}")
            return iface
        # Fallback to first interface with IPv4
        for interface in ni.interfaces():
            addrs = ni.ifaddresses(interface)
            if ni.AF_INET in addrs:
                self.logger.debug(f"Falling back to first IPv4-capable interface: {interface}")
                return interface
        raise RuntimeError("No IPv4 interface found")

    def __discover_local_ip_and_netmask(self, interface: str) -> tuple[str, str]:
        self.logger.info(f"Discovering Local IP and netmask on interface {interface}")
        addrs = ni.ifaddresses(interface)
        ip = addrs[ni.AF_INET][0]['addr']
        netmask = addrs[ni.AF_INET][0]['netmask']
        self.logger.info(f"Local IP {ip} with netmask {netmask}")
        return ip, netmask

    def __compute_network(self, ip: str, netmask: str) -> IPv4Network:
        # Convert netmask to prefixlen
        packed = socket.inet_aton(netmask)
        bits = bin(int.from_bytes(packed, 'big')).count('1')
        network = IPv4Network(f"{ip}/{bits}", strict=False)
        self.logger.debug(f"Computed network {network} from ip={ip}, netmask={netmask} (/ {bits})")
        return network

    @staticmethod
    def __probe_host(host: str, port: int) -> bool:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.settimeout(0.5)
            result = s.connect_ex((host, int(port)))
            if result == 0:
                # Debug only on open to avoid log noise
                logging.getLogger("OpenA3XXNetworkingClient").debug(f"TCP {port} open on {host}")
                return True
            return False
        finally:
            s.close()
