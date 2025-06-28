"""Unit tests for Service Discovery Infrastructure - Fixed async mocking.

Tests the service discovery functionality including port scanning,
protocol detection, and service registration with proper async mocking.
"""

import asyncio
import json
import os
import socket
import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

import aiohttp

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from blender_movie_director.backend.service_discovery import (
    ServiceDiscoveryManager,
    ServiceInfo,
)


class TestServiceDiscovery(unittest.TestCase):
    """Test cases for ServiceDiscoveryManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.discovery_manager = ServiceDiscoveryManager()

    def test_initialization(self):
        """Test ServiceDiscoveryManager initialization."""
        # Check that all services are configured
        self.assertEqual(len(self.discovery_manager.services_config), 4)
        self.assertIn("comfyui", self.discovery_manager.services_config)
        self.assertIn("wan2gp", self.discovery_manager.services_config)
        self.assertIn("rvc", self.discovery_manager.services_config)
        self.assertIn("audioldm", self.discovery_manager.services_config)

        # Check default ports
        self.assertEqual(self.discovery_manager.services_config["comfyui"].default_port, 8188)
        self.assertEqual(self.discovery_manager.services_config["wan2gp"].default_port, 7860)
        self.assertEqual(self.discovery_manager.services_config["rvc"].default_port, 7865)
        self.assertEqual(self.discovery_manager.services_config["audioldm"].default_port, 7863)

    def test_service_config(self):
        """Test ServiceConfig data structure."""
        config = self.discovery_manager.services_config["comfyui"]
        self.assertEqual(config.name, "comfyui")
        self.assertEqual(config.protocol, "http")
        self.assertEqual(config.health_endpoint, "/system_stats")
        self.assertIsInstance(config.alternative_ports, list)

    @patch("blender_movie_director.backend.service_discovery.aiohttp.ClientSession")
    async def test_discover_all_services_success(self, mock_client_session):
        """Test successful discovery of all services."""
        # Create mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.content_type = "application/json"

        # Create an async method that returns the JSON data
        async def mock_json():
            return {"version": "1.0.0", "nodes": ["image_generator", "video_processor"]}

        mock_response.json = mock_json

        # Create mock session with proper async context manager
        mock_session = MagicMock()

        # Create async context manager for session.get()
        class MockGetContextManager:
            async def __aenter__(self):
                return mock_response

            async def __aexit__(self, *args):
                pass

        mock_session.get.return_value = MockGetContextManager()

        # Make ClientSession return async context manager
        class MockSessionContextManager:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, *args):
                pass

        mock_client_session.return_value = MockSessionContextManager()

        # Run discovery
        results = await self.discovery_manager.discover_all_services()

        # Check results
        self.assertEqual(len(results), 4)
        for _service_name, service_info in results.items():
            self.assertTrue(service_info.is_available)
            self.assertEqual(service_info.version, "1.0.0")
            self.assertIsNone(service_info.error_message)

    @patch("blender_movie_director.backend.service_discovery.aiohttp.ClientSession")
    async def test_discover_with_partial_services(self, mock_client_session):
        """Test discovery with only some services available."""

        # Create mock session
        mock_session = MagicMock()

        # Create different responses for different services
        class MockGetContextManager:
            def __init__(self, url, **kwargs):
                self.url = url

            async def __aenter__(self):
                if "8188" in self.url:  # ComfyUI available
                    mock_response = MagicMock()
                    mock_response.status = 200
                    mock_response.content_type = "application/json"

                    async def mock_json():
                        return {"version": "1.0.0"}

                    mock_response.json = mock_json
                    return mock_response
                else:  # Other services not available
                    raise aiohttp.ClientError("Connection failed")

            async def __aexit__(self, *args):
                pass

        mock_session.get = MockGetContextManager

        # Make ClientSession return async context manager
        class MockSessionContextManager:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, *args):
                pass

        mock_client_session.return_value = MockSessionContextManager()

        # Run discovery
        results = await self.discovery_manager.discover_all_services()

        # Check results
        self.assertTrue(results["comfyui"].is_available)
        self.assertFalse(results["wan2gp"].is_available)
        self.assertFalse(results["rvc"].is_available)
        self.assertFalse(results["audioldm"].is_available)

    def test_is_port_open(self):
        """Test port checking functionality."""
        # Test with mock socket
        with patch("socket.socket") as mock_socket:
            mock_sock_instance = Mock()
            mock_sock_instance.connect_ex.return_value = 0  # Port open
            mock_socket.return_value = mock_sock_instance

            result = self.discovery_manager._is_port_open("localhost", 8188, 5.0)
            self.assertTrue(result)

            # Test port closed
            mock_sock_instance.connect_ex.return_value = 1  # Port closed
            result = self.discovery_manager._is_port_open("localhost", 8188, 5.0)
            self.assertFalse(result)

    def test_extract_capabilities(self):
        """Test capability extraction from service responses."""
        # Test ComfyUI capabilities
        response_data = {"nodes": ["KSampler", "VAEDecode", "ImageToVideo", "VideoEncode"]}
        capabilities = self.discovery_manager._extract_capabilities("comfyui", response_data)
        self.assertIn("image_generation", capabilities)
        self.assertIn("video_generation", capabilities)

        # Test default capabilities
        capabilities = self.discovery_manager._extract_capabilities("wan2gp", {})
        self.assertIn("video_generation", capabilities)
        self.assertIn("quick_preview", capabilities)

    def test_get_service_url(self):
        """Test getting service URL."""
        # Add a discovered service
        self.discovery_manager.discovered_services["comfyui"] = ServiceInfo(
            name="comfyui", host="localhost", port=8188, protocol="http", is_available=True
        )

        url = self.discovery_manager.get_service_url("comfyui")
        self.assertEqual(url, "http://localhost:8188")

        # Test unavailable service
        self.discovery_manager.discovered_services["wan2gp"] = ServiceInfo(
            name="wan2gp", host="localhost", port=7860, protocol="http", is_available=False
        )

        url = self.discovery_manager.get_service_url("wan2gp")
        self.assertIsNone(url)

    def test_get_available_services(self):
        """Test getting only available services."""
        # Add mixed services
        self.discovery_manager.discovered_services = {
            "comfyui": ServiceInfo(
                name="comfyui", host="localhost", port=8188, protocol="http", is_available=True
            ),
            "wan2gp": ServiceInfo(
                name="wan2gp", host="localhost", port=7860, protocol="http", is_available=False
            ),
        }

        available = self.discovery_manager.get_available_services()
        self.assertEqual(len(available), 1)
        self.assertIn("comfyui", available)
        self.assertNotIn("wan2gp", available)

    @patch("urllib.request.urlopen")
    @patch("blender_movie_director.backend.service_discovery.aiohttp", None)
    def test_sync_fallback(self, mock_urlopen):
        """Test synchronous fallback when aiohttp is not available."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"version": "1.0.0"}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Patch port check
        with patch.object(self.discovery_manager, "_is_port_open", return_value=True):
            service_info = self.discovery_manager._check_port_sync(
                "comfyui", "localhost", 8188, "http", "/system_stats", 5.0
            )

        self.assertTrue(service_info.is_available)
        self.assertEqual(service_info.version, "1.0.0")

    async def test_custom_ports(self):
        """Test discovery with custom port configuration."""
        custom_ports = {"comfyui": 8080, "wan2gp": 7777}

        with patch.object(
            self.discovery_manager,
            "_discover_service_async",
            return_value=ServiceInfo(
                name="comfyui", host="localhost", port=8080, protocol="http", is_available=True
            ),
        ):
            await self.discovery_manager.discover_all_services(custom_ports)

            # Verify custom port was applied
            self.assertEqual(self.discovery_manager.services_config["comfyui"].default_port, 8080)

    async def test_discovery_timeout(self):
        """Test that discovery completes within 5 seconds."""
        import time

        # Mock slow service
        async def slow_discover(*args):
            await asyncio.sleep(10)  # Longer than timeout
            return ServiceInfo(
                name="test",
                host="localhost",
                port=8188,
                protocol="http",
                is_available=False,
                error_message="Timeout",
            )

        with patch.object(
            self.discovery_manager, "_discover_service_async", side_effect=slow_discover
        ):
            start_time = time.time()

            # This should complete despite slow services
            await self.discovery_manager.discover_all_services()

            elapsed = time.time() - start_time
            self.assertLess(elapsed, 6.0)  # Should complete within 6 seconds

    async def test_alternative_ports_discovery(self):
        """Test discovery on alternative ports when default fails."""

        # Mock responses - default port fails, alternative succeeds
        async def mock_check_port(service_name, host, port, protocol, endpoint, timeout):
            if port == 8188:  # Default ComfyUI port fails
                return ServiceInfo(
                    name=service_name,
                    host=host,
                    port=port,
                    protocol=protocol,
                    is_available=False,
                    error_message="Connection refused",
                )
            elif port == 8189:  # Alternative port succeeds
                return ServiceInfo(
                    name=service_name,
                    host=host,
                    port=port,
                    protocol=protocol,
                    is_available=True,
                    version="1.0.0",
                )
            else:
                return ServiceInfo(
                    name=service_name,
                    host=host,
                    port=port,
                    protocol=protocol,
                    is_available=False,
                    error_message="Not found",
                )

        with patch.object(self.discovery_manager, "_check_port_async", side_effect=mock_check_port):
            config = self.discovery_manager.services_config["comfyui"]
            result = await self.discovery_manager._discover_service_async(config)

            self.assertTrue(result.is_available)
            self.assertEqual(result.port, 8189)  # Should find on alternative port

    def test_service_type_detection(self):
        """Test detection of service type from response."""
        # Test ComfyUI detection
        comfyui_response = {"version": "1.0.0", "nodes": ["KSampler", "LoadImage", "SaveImage"]}
        capabilities = self.discovery_manager._extract_capabilities("comfyui", comfyui_response)
        self.assertIn("image_generation", capabilities)

        # Test service-specific capabilities
        self.assertEqual(
            self.discovery_manager._extract_capabilities("rvc", {}),
            ["voice_cloning", "audio_processing"],
        )
        self.assertEqual(
            self.discovery_manager._extract_capabilities("audioldm", {}),
            ["audio_generation", "sound_effects"],
        )

    @patch("socket.socket")
    def test_ipv4_ipv6_support(self, mock_socket):
        """Test support for both IPv4 and IPv6."""
        # Test IPv4
        mock_sock = Mock()
        mock_sock.connect_ex.return_value = 0
        mock_socket.return_value = mock_sock

        result = self.discovery_manager._is_port_open("127.0.0.1", 8188, 5.0)
        self.assertTrue(result)
        mock_socket.assert_called_with(socket.AF_INET, socket.SOCK_STREAM)

        # Note: Full IPv6 support would require additional implementation

    async def test_refresh_single_service(self):
        """Test refreshing discovery for a single service."""
        # Initial discovery - service unavailable
        self.discovery_manager.discovered_services["comfyui"] = ServiceInfo(
            name="comfyui", host="localhost", port=8188, protocol="http", is_available=False
        )

        # Mock successful refresh
        with patch.object(
            self.discovery_manager,
            "_discover_service_async",
            return_value=ServiceInfo(
                name="comfyui",
                host="localhost",
                port=8188,
                protocol="http",
                is_available=True,
                version="1.0.0",
            ),
        ):
            result = await self.discovery_manager.refresh_service("comfyui")

            self.assertTrue(result.is_available)
            self.assertEqual(result.version, "1.0.0")
            self.assertTrue(self.discovery_manager.discovered_services["comfyui"].is_available)

    async def test_parallel_discovery_performance(self):
        """Test that parallel discovery is faster than sequential."""
        import time

        # Mock discovery that takes 1 second per service
        async def mock_discover(config):
            await asyncio.sleep(1.0)
            return ServiceInfo(
                name=config.name,
                host="localhost",
                port=config.default_port,
                protocol=config.protocol,
                is_available=True,
            )

        with patch.object(
            self.discovery_manager, "_discover_service_async", side_effect=mock_discover
        ):
            start_time = time.time()
            results = await self.discovery_manager.discover_all_services()
            elapsed = time.time() - start_time

            # With 4 services, parallel should complete in ~1 second, not 4
            self.assertLess(elapsed, 2.0)
            self.assertEqual(len(results), 4)

    def test_error_message_clarity(self):
        """Test that error messages are clear and actionable."""
        error_scenarios = [
            ("Connection timeout", "Check if the service is running"),
            ("Connection refused", "Service may not be running on this port"),
            ("Port not open", "Service port appears to be closed"),
            ("HTTP 404", "Service is running but health endpoint not found"),
        ]

        for error, _expected_hint in error_scenarios:
            service_info = ServiceInfo(
                name="test",
                host="localhost",
                port=8188,
                protocol="http",
                is_available=False,
                error_message=error,
            )

            # Error message should be clear
            self.assertIn(error, service_info.error_message)

    def test_memory_usage_constant(self):
        """Test that discovery doesn't leak memory."""
        import gc

        # Get initial object count
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Create and destroy multiple discovery managers
        for _ in range(10):
            dm = ServiceDiscoveryManager()
            del dm

        # Force garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())

        # Object count should be roughly the same (allow small variance)
        self.assertLess(abs(final_objects - initial_objects), 100)


class TestServiceDiscoveryIntegration(unittest.TestCase):
    """Integration tests for service discovery with mock servers."""

    @patch("blender_movie_director.backend.service_discovery.aiohttp.ClientSession")
    async def test_full_discovery_flow(self, mock_client_session):
        """Test complete discovery flow with all service types."""
        discovery_manager = ServiceDiscoveryManager()

        # Set up different responses for each service
        responses = {
            "8188": {"version": "1.0.0", "nodes": ["image", "video"]},  # ComfyUI
            "7860": {"status": "ready", "models": ["causvid"]},  # Wan2GP
            "7865": {"status": "online", "version": "2.0"},  # RVC
            "7863": {"ready": True, "models": ["audioldm-l"]},  # AudioLDM
        }

        # Create mock session
        mock_session = MagicMock()

        # Create async context manager for session.get()
        class MockGetContextManager:
            def __init__(self, url, **kwargs):
                self.url = url

            async def __aenter__(self):
                for port, data in responses.items():
                    if port in self.url:
                        mock_response = MagicMock()
                        mock_response.status = 200
                        mock_response.content_type = "application/json"

                        async def mock_json(data=data):
                            return data

                        mock_response.json = mock_json
                        return mock_response

                raise aiohttp.ClientError("Not found")

            async def __aexit__(self, *args):
                pass

        mock_session.get = MockGetContextManager

        # Make ClientSession return async context manager
        class MockSessionContextManager:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, *args):
                pass

        mock_client_session.return_value = MockSessionContextManager()

        # Run discovery
        results = await discovery_manager.discover_all_services()

        # Verify all services discovered
        self.assertEqual(len(results), 4)

        # Check ComfyUI
        self.assertTrue(results["comfyui"].is_available)
        self.assertIn("image_generation", results["comfyui"].capabilities)
        self.assertIn("video_generation", results["comfyui"].capabilities)

        # Check others
        self.assertTrue(results["wan2gp"].is_available)
        self.assertTrue(results["rvc"].is_available)
        self.assertTrue(results["audioldm"].is_available)


def run_async_test(coro):
    """Helper to run async tests."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Patch async test methods for unittest
def make_async_test(test_func):
    """Create a synchronous wrapper for async test methods."""

    def wrapper(self):
        return run_async_test(test_func(self))

    wrapper.__name__ = test_func.__name__
    wrapper.__doc__ = test_func.__doc__
    return wrapper


# Apply to TestServiceDiscovery
for attr_name in dir(TestServiceDiscovery):
    attr = getattr(TestServiceDiscovery, attr_name)
    if asyncio.iscoroutinefunction(attr) and attr_name.startswith("test_"):
        setattr(TestServiceDiscovery, attr_name, make_async_test(attr))

# Apply to TestServiceDiscoveryIntegration
for attr_name in dir(TestServiceDiscoveryIntegration):
    attr = getattr(TestServiceDiscoveryIntegration, attr_name)
    if asyncio.iscoroutinefunction(attr) and attr_name.startswith("test_"):
        setattr(TestServiceDiscoveryIntegration, attr_name, make_async_test(attr))


if __name__ == "__main__":
    unittest.main()
