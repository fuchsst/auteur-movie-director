"""Simplified unit tests for Service Discovery Infrastructure."""

import asyncio
import os

# Import the module under test
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from blender_movie_director.backend.service_discovery import (
    ServiceDiscoveryManager,
    ServiceInfo,
)


class TestServiceDiscoverySimple(unittest.TestCase):
    """Simple test cases for ServiceDiscoveryManager."""

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

    @patch("socket.socket")
    def test_is_port_open(self, mock_socket):
        """Test port checking functionality."""
        # Test with mock socket
        mock_sock_instance = Mock()
        mock_sock_instance.connect_ex.return_value = 0  # Port open
        mock_socket.return_value = mock_sock_instance

        result = self.discovery_manager._is_port_open("localhost", 8188, 5.0)
        self.assertTrue(result)

        # Test port closed
        mock_sock_instance.connect_ex.return_value = 1  # Port closed
        result = self.discovery_manager._is_port_open("localhost", 8188, 5.0)
        self.assertFalse(result)

    @patch("urllib.request.urlopen")
    def test_sync_fallback(self, mock_urlopen):
        """Test synchronous fallback when aiohttp is not available."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"version": "1.0.0"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Patch port check
        with patch.object(self.discovery_manager, "_is_port_open", return_value=True):
            service_info = self.discovery_manager._check_port_sync(
                "comfyui", "localhost", 8188, "http", "/system_stats", 5.0
            )

        self.assertTrue(service_info.is_available)
        self.assertEqual(service_info.version, "1.0.0")

    def test_process_discovery_results(self):
        """Test processing of discovery results."""
        # Create test results
        results = [
            ServiceInfo(
                name="comfyui", host="localhost", port=8188, protocol="http", is_available=True
            ),
            Exception("Test error for wan2gp"),
            ServiceInfo(
                name="rvc",
                host="localhost",
                port=7865,
                protocol="http",
                is_available=False,
                error_message="Connection refused",
            ),
        ]

        # Process results
        self.discovery_manager._process_discovery_results(results)

        # Check discovered services
        self.assertEqual(len(self.discovery_manager.discovered_services), 3)
        self.assertTrue(self.discovery_manager.discovered_services["comfyui"].is_available)
        self.assertFalse(self.discovery_manager.discovered_services["wan2gp"].is_available)
        self.assertFalse(self.discovery_manager.discovered_services["rvc"].is_available)


class TestAsyncServiceDiscovery(unittest.TestCase):
    """Test async functionality with proper mocking."""

    def setUp(self):
        """Set up test fixtures."""
        self.discovery_manager = ServiceDiscoveryManager()

    def test_custom_ports(self):
        """Test discovery with custom port configuration."""
        custom_ports = {"comfyui": 8080, "wan2gp": 7777}

        # Apply custom ports
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.discovery_manager.discover_all_services(custom_ports))
        loop.close()

        # Verify custom port was applied
        self.assertEqual(self.discovery_manager.services_config["comfyui"].default_port, 8080)


if __name__ == "__main__":
    unittest.main()
