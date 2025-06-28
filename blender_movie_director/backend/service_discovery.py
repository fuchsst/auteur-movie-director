"""Service Discovery Infrastructure for Blender Movie Director.

This module implements automatic discovery of AI backend services running locally.
It supports parallel discovery, protocol detection, and graceful fallback to manual configuration.
"""

import asyncio
import logging
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

try:
    import aiohttp
except ImportError:
    # Fallback for Blender environment where aiohttp might not be available
    aiohttp = None

import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


@dataclass
class ServiceInfo:
    """Information about a discovered service."""

    name: str
    host: str
    port: int
    protocol: str
    is_available: bool
    version: str | None = None
    capabilities: list[str] = field(default_factory=list)
    last_check: float = field(default_factory=time.time)
    error_message: str | None = None


@dataclass
class ServiceConfig:
    """Configuration for a service to discover."""

    name: str
    default_port: int
    protocol: str
    health_endpoint: str
    alternative_ports: list[int] = field(default_factory=list)
    timeout: float = 5.0


class ServiceDiscoveryManager:
    """Manages automatic discovery of AI backend services."""

    def __init__(self):
        """Initialize the service discovery manager."""
        self.services_config = {
            "comfyui": ServiceConfig(
                name="comfyui",
                default_port=8188,
                protocol="http",
                health_endpoint="/system_stats",
                alternative_ports=[8189, 8190, 8080],
            ),
            "wan2gp": ServiceConfig(
                name="wan2gp",
                default_port=7860,
                protocol="http",
                health_endpoint="/api/health",
                alternative_ports=[7861, 7862, 7863],
            ),
            "rvc": ServiceConfig(
                name="rvc",
                default_port=7865,
                protocol="http",
                health_endpoint="/api/status",
                alternative_ports=[7866, 7867],
            ),
            "audioldm": ServiceConfig(
                name="audioldm",
                default_port=7863,
                protocol="http",
                health_endpoint="/api/ready",
                alternative_ports=[7864, 7868],
            ),
        }

        self.discovered_services: dict[str, ServiceInfo] = {}
        self._discovery_lock = asyncio.Lock() if asyncio else None
        self._executor = ThreadPoolExecutor(max_workers=10)

    async def discover_all_services(
        self, custom_ports: dict[str, int] | None = None
    ) -> dict[str, ServiceInfo]:
        """Discover all backend services in parallel.

        Args:
            custom_ports: Optional dict mapping service names to custom ports

        Returns:
            Dict mapping service names to ServiceInfo objects
        """
        start_time = time.time()
        logger.info("Starting service discovery scan")

        # Apply custom ports if provided
        if custom_ports:
            for service_name, port in custom_ports.items():
                if service_name in self.services_config:
                    self.services_config[service_name].default_port = port

        # Create discovery tasks
        tasks = []
        for _service_name, config in self.services_config.items():
            if aiohttp:
                task = self._discover_service_async(config)
            else:
                task = self._discover_service_sync(config)
            tasks.append(task)

        # Execute all discovery tasks in parallel
        if aiohttp:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Fallback synchronous execution
            results = []
            for task in tasks:
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    results.append(e)

        # Process results
        self._process_discovery_results(results)

        elapsed = time.time() - start_time
        logger.info(f"Service discovery completed in {elapsed:.2f} seconds")
        logger.info(
            f"Discovered {len([s for s in self.discovered_services.values() if s.is_available])} "
            f"out of {len(self.services_config)} services"
        )

        return self.discovered_services

    async def _discover_service_async(self, config: ServiceConfig) -> ServiceInfo:
        """Discover a single service using async HTTP (when aiohttp is available)."""
        # Try default port first
        service_info = await self._check_port_async(
            config.name,
            "localhost",
            config.default_port,
            config.protocol,
            config.health_endpoint,
            config.timeout,
        )

        if service_info.is_available:
            return service_info

        # Try alternative ports
        for port in config.alternative_ports:
            service_info = await self._check_port_async(
                config.name,
                "localhost",
                port,
                config.protocol,
                config.health_endpoint,
                config.timeout,
            )
            if service_info.is_available:
                return service_info

        # Return last failed attempt
        return service_info

    async def _discover_service_sync(self, config: ServiceConfig) -> ServiceInfo:
        """Discover a single service using synchronous HTTP (fallback when aiohttp not available)."""
        # Try default port first
        service_info = self._check_port_sync(
            config.name,
            "localhost",
            config.default_port,
            config.protocol,
            config.health_endpoint,
            config.timeout,
        )

        if service_info.is_available:
            return service_info

        # Try alternative ports
        for port in config.alternative_ports:
            service_info = self._check_port_sync(
                config.name,
                "localhost",
                port,
                config.protocol,
                config.health_endpoint,
                config.timeout,
            )
            if service_info.is_available:
                return service_info

        # Return last failed attempt
        return service_info

    async def _check_port_async(
        self,
        service_name: str,
        host: str,
        port: int,
        protocol: str,
        health_endpoint: str,
        timeout: float,
    ) -> ServiceInfo:
        """Check if a service is available on a specific port using async HTTP."""
        url = f"{protocol}://{host}:{port}{health_endpoint}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status == 200:
                        data = (
                            await response.json()
                            if response.content_type == "application/json"
                            else {}
                        )
                        return ServiceInfo(
                            name=service_name,
                            host=host,
                            port=port,
                            protocol=protocol,
                            is_available=True,
                            version=data.get("version", "unknown"),
                            capabilities=self._extract_capabilities(service_name, data),
                        )
                    else:
                        return ServiceInfo(
                            name=service_name,
                            host=host,
                            port=port,
                            protocol=protocol,
                            is_available=False,
                            error_message=f"HTTP {response.status}",
                        )
        except TimeoutError:
            return ServiceInfo(
                name=service_name,
                host=host,
                port=port,
                protocol=protocol,
                is_available=False,
                error_message="Connection timeout",
            )
        except Exception as e:
            return ServiceInfo(
                name=service_name,
                host=host,
                port=port,
                protocol=protocol,
                is_available=False,
                error_message=str(e),
            )

    def _check_port_sync(
        self,
        service_name: str,
        host: str,
        port: int,
        protocol: str,
        health_endpoint: str,
        timeout: float,
    ) -> ServiceInfo:
        """Check if a service is available on a specific port using sync HTTP."""
        url = f"{protocol}://{host}:{port}{health_endpoint}"

        # First check if port is open
        if not self._is_port_open(host, port, timeout):
            return ServiceInfo(
                name=service_name,
                host=host,
                port=port,
                protocol=protocol,
                is_available=False,
                error_message="Port not open",
            )

        try:
            # Try HTTP request
            request = urllib.request.Request(url)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status == 200:
                    data = {}
                    try:
                        import json

                        data = json.loads(response.read().decode("utf-8"))
                    except:
                        pass

                    return ServiceInfo(
                        name=service_name,
                        host=host,
                        port=port,
                        protocol=protocol,
                        is_available=True,
                        version=data.get("version", "unknown"),
                        capabilities=self._extract_capabilities(service_name, data),
                    )
                else:
                    return ServiceInfo(
                        name=service_name,
                        host=host,
                        port=port,
                        protocol=protocol,
                        is_available=False,
                        error_message=f"HTTP {response.status}",
                    )
        except urllib.error.URLError as e:
            return ServiceInfo(
                name=service_name,
                host=host,
                port=port,
                protocol=protocol,
                is_available=False,
                error_message=str(e.reason),
            )
        except Exception as e:
            return ServiceInfo(
                name=service_name,
                host=host,
                port=port,
                protocol=protocol,
                is_available=False,
                error_message=str(e),
            )

    def _is_port_open(self, host: str, port: int, timeout: float) -> bool:
        """Check if a port is open using socket connection."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            result = sock.connect_ex((host, port))
            return result == 0
        except:
            return False
        finally:
            sock.close()

    def _extract_capabilities(self, service_name: str, response_data: dict[str, Any]) -> list[str]:
        """Extract service capabilities from health check response."""
        capabilities = []

        if service_name == "comfyui":
            # ComfyUI capabilities based on available nodes
            if "nodes" in response_data:
                if any("image" in node.lower() for node in response_data["nodes"]):
                    capabilities.append("image_generation")
                if any("video" in node.lower() for node in response_data["nodes"]):
                    capabilities.append("video_generation")
            else:
                # Default capabilities if not specified
                capabilities = ["image_generation", "video_generation"]

        elif service_name == "wan2gp":
            capabilities = ["video_generation", "quick_preview"]

        elif service_name == "rvc":
            capabilities = ["voice_cloning", "audio_processing"]

        elif service_name == "audioldm":
            capabilities = ["audio_generation", "sound_effects"]

        return capabilities

    def _process_discovery_results(self, results: list[Any]) -> None:
        """Process discovery results and update internal state."""
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                service_name = list(self.services_config.keys())[i]
                logger.error(f"Error discovering {service_name}: {result}")
                self.discovered_services[service_name] = ServiceInfo(
                    name=service_name,
                    host="localhost",
                    port=self.services_config[service_name].default_port,
                    protocol=self.services_config[service_name].protocol,
                    is_available=False,
                    error_message=str(result),
                )
            elif isinstance(result, ServiceInfo):
                self.discovered_services[result.name] = result
                if result.is_available:
                    logger.info(f"Discovered {result.name} at {result.host}:{result.port}")
                else:
                    logger.warning(f"Service {result.name} not available: {result.error_message}")

    def get_service_info(self, service_name: str) -> ServiceInfo | None:
        """Get information about a specific discovered service."""
        return self.discovered_services.get(service_name)

    def get_available_services(self) -> dict[str, ServiceInfo]:
        """Get all available (successfully discovered) services."""
        return {name: info for name, info in self.discovered_services.items() if info.is_available}

    def get_service_url(self, service_name: str) -> str | None:
        """Get the base URL for a discovered service."""
        info = self.get_service_info(service_name)
        if info and info.is_available:
            return f"{info.protocol}://{info.host}:{info.port}"
        return None

    async def refresh_service(self, service_name: str) -> ServiceInfo | None:
        """Refresh discovery for a specific service."""
        if service_name not in self.services_config:
            logger.error(f"Unknown service: {service_name}")
            return None

        config = self.services_config[service_name]

        if aiohttp:
            service_info = await self._discover_service_async(config)
        else:
            service_info = await self._discover_service_sync(config)

        self.discovered_services[service_name] = service_info
        return service_info


# Singleton instance for the addon
_discovery_manager = None


def get_discovery_manager() -> ServiceDiscoveryManager:
    """Get the singleton ServiceDiscoveryManager instance."""
    global _discovery_manager
    if _discovery_manager is None:
        _discovery_manager = ServiceDiscoveryManager()
    return _discovery_manager
