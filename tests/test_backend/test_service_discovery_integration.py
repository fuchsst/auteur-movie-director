"""Integration tests for Service Discovery with Blender.

Tests the complete integration of service discovery with Blender operators,
properties, and UI components.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

# Mock bpy module for testing outside Blender
sys.modules["bpy"] = MagicMock()
sys.modules["bpy.types"] = MagicMock()
sys.modules["bpy.props"] = MagicMock()

# Import after mocking bpy
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from blender_movie_director.backend.service_discovery import ServiceInfo
from blender_movie_director.ui.operators.service_discovery_ops import (
    MOVIE_DIRECTOR_OT_discover_services,
    MOVIE_DIRECTOR_OT_refresh_service,
    MOVIE_DIRECTOR_OT_test_service_connection,
)
from blender_movie_director.ui.properties.service_properties import (
    BackendServiceStatus,
    MovieDirectorProperties,
)


class TestServiceDiscoveryOperators(unittest.TestCase):
    """Test Blender operators for service discovery."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock Blender context
        self.context = Mock()
        self.context.scene = Mock()
        self.context.scene.movie_director_props = Mock()
        self.context.scene.movie_director_props.backend_services = Mock()
        self.context.preferences = Mock()
        self.context.preferences.addons = {"blender_movie_director": Mock()}
        self.context.preferences.addons["blender_movie_director"].preferences = Mock()
        self.context.window_manager = Mock()
        self.context.window = Mock()
        self.context.screen = Mock()
        self.context.screen.areas = []

    @patch("blender_movie_director.ui.operators.service_discovery_ops.get_discovery_manager")
    @patch("threading.Thread")
    def test_discover_services_operator(self, mock_thread, mock_get_discovery):
        """Test the discover services operator."""
        # Setup
        operator = MOVIE_DIRECTOR_OT_discover_services()
        operator.report = Mock()

        # Mock discovery manager
        mock_discovery_manager = Mock()
        mock_get_discovery.return_value = mock_discovery_manager

        # Execute operator
        result = operator.execute(self.context)

        # Verify
        self.assertEqual(result, {"RUNNING_MODAL"})
        operator.report.assert_called_with({"INFO"}, "Service discovery started...")
        mock_thread.assert_called_once()

    def test_discover_services_modal_running(self):
        """Test modal handler while discovery is running."""
        # Setup
        operator = MOVIE_DIRECTOR_OT_discover_services()
        operator._discovery_complete = False
        operator._timer = Mock()

        # Mock event
        event = Mock()
        event.type = "TIMER"

        # Execute modal
        result = operator.modal(self.context, event)

        # Verify still running
        self.assertEqual(result, {"PASS_THROUGH"})

    def test_discover_services_modal_complete(self):
        """Test modal handler when discovery completes."""
        # Setup
        operator = MOVIE_DIRECTOR_OT_discover_services()
        operator._discovery_complete = True
        operator._timer = Mock()
        operator.report = Mock()
        operator._discovery_results = {
            "comfyui": ServiceInfo(
                name="comfyui",
                host="localhost",
                port=8188,
                protocol="http",
                is_available=True,
                version="1.0.0",
                capabilities=["image_generation", "video_generation"],
            ),
            "wan2gp": ServiceInfo(
                name="wan2gp",
                host="localhost",
                port=7860,
                protocol="http",
                is_available=False,
                error_message="Connection refused",
            ),
        }

        # Mock backend services collection
        mock_services = Mock()
        mock_services.clear = Mock()
        mock_services.add = Mock(return_value=Mock(capabilities=Mock()))
        self.context.scene.movie_director_props.backend_services = mock_services

        # Mock event
        event = Mock()
        event.type = "TIMER"

        # Execute modal
        result = operator.modal(self.context, event)

        # Verify
        self.assertEqual(result, {"FINISHED"})
        operator.report.assert_called_with({"INFO"}, "Discovery complete: 1 services found")
        mock_services.clear.assert_called_once()
        self.assertEqual(mock_services.add.call_count, 2)  # Two services

    def test_update_service_properties(self):
        """Test updating Blender properties with discovery results."""
        # Setup
        operator = MOVIE_DIRECTOR_OT_discover_services()
        operator._discovery_results = {
            "comfyui": ServiceInfo(
                name="comfyui",
                host="localhost",
                port=8188,
                protocol="http",
                is_available=True,
                version="1.0.0",
                capabilities=["image_generation"],
            )
        }

        # Mock service property
        mock_service_prop = Mock()
        mock_service_prop.capabilities = Mock()
        mock_service_prop.capabilities.clear = Mock()
        mock_service_prop.capabilities.add = Mock(return_value=Mock())

        # Mock backend services
        mock_services = Mock()
        mock_services.clear = Mock()
        mock_services.add = Mock(return_value=mock_service_prop)
        self.context.scene.movie_director_props.backend_services = mock_services

        # Update properties
        operator._update_service_properties(self.context)

        # Verify service properties were set correctly
        mock_services.clear.assert_called_once()
        mock_services.add.assert_called_once()
        self.assertEqual(mock_service_prop.name, "comfyui")
        self.assertEqual(mock_service_prop.status, "connected")
        self.assertEqual(mock_service_prop.url, "http://localhost:8188")
        self.assertEqual(mock_service_prop.version, "1.0.0")

    @patch("blender_movie_director.ui.operators.service_discovery_ops.get_discovery_manager")
    def test_refresh_service_operator(self, mock_get_discovery):
        """Test the refresh service operator."""
        # Setup
        operator = MOVIE_DIRECTOR_OT_refresh_service()
        operator.service_name = "comfyui"
        operator.report = Mock()

        # Execute
        with patch("threading.Thread") as mock_thread:
            result = operator.execute(self.context)

        # Verify
        self.assertEqual(result, {"FINISHED"})
        operator.report.assert_called_with({"INFO"}, "Refreshing comfyui...")
        mock_thread.assert_called_once()

    def test_test_connection_operator(self):
        """Test the connection test operator."""
        # Setup
        operator = MOVIE_DIRECTOR_OT_test_service_connection()
        operator.service_name = "comfyui"
        operator.service_url = ""
        operator.report = Mock()

        # Mock discovery manager
        with patch(
            "blender_movie_director.ui.operators.service_discovery_ops.get_discovery_manager"
        ) as mock_get_dm:
            mock_dm = Mock()
            mock_dm.get_service_info = Mock(
                return_value=ServiceInfo(
                    name="comfyui", host="localhost", port=8188, protocol="http", is_available=True
                )
            )
            mock_get_dm.return_value = mock_dm

            # Mock socket
            with patch("socket.socket") as mock_socket:
                mock_sock = Mock()
                mock_sock.connect_ex = Mock(return_value=0)  # Success
                mock_socket.return_value = mock_sock

                # Execute
                result = operator.execute(self.context)

        # Verify
        self.assertEqual(result, {"FINISHED"})
        operator.report.assert_called_with(
            {"INFO"}, "Successfully connected to comfyui at localhost:8188"
        )

    def test_custom_ports_configuration(self):
        """Test custom port configuration from preferences."""
        # Setup
        operator = MOVIE_DIRECTOR_OT_discover_services()

        # Mock preferences with custom ports
        prefs = self.context.preferences.addons["blender_movie_director"].preferences
        prefs.use_custom_ports = True
        prefs.comfyui_port = 8080
        prefs.wan2gp_port = 7777
        prefs.rvc_port = 0  # Should be ignored
        prefs.audioldm_port = 7999

        # Get custom ports
        custom_ports = operator._get_custom_ports()

        # Verify
        self.assertEqual(custom_ports["comfyui"], 8080)
        self.assertEqual(custom_ports["wan2gp"], 7777)
        self.assertNotIn("rvc", custom_ports)  # Port 0 should be ignored
        self.assertEqual(custom_ports["audioldm"], 7999)


class TestServiceProperties(unittest.TestCase):
    """Test Blender property groups for service information."""

    def test_backend_service_status_defaults(self):
        """Test default values for BackendServiceStatus."""
        # Note: In real Blender, PropertyGroup would be instantiated differently
        # This tests the structure and attributes
        self.assertTrue(hasattr(BackendServiceStatus, "name"))
        self.assertTrue(hasattr(BackendServiceStatus, "status"))
        self.assertTrue(hasattr(BackendServiceStatus, "url"))
        self.assertTrue(hasattr(BackendServiceStatus, "capabilities"))

    def test_movie_director_properties_structure(self):
        """Test MovieDirectorProperties structure."""
        self.assertTrue(hasattr(MovieDirectorProperties, "backend_services"))
        self.assertTrue(hasattr(MovieDirectorProperties, "auto_discover"))
        self.assertTrue(hasattr(MovieDirectorProperties, "enable_health_checks"))


class TestFullIntegrationFlow(unittest.TestCase):
    """Test the complete integration flow from discovery to UI update."""

    @patch("blender_movie_director.backend.service_discovery.aiohttp")
    @patch("blender_movie_director.ui.operators.service_discovery_ops.get_discovery_manager")
    def test_complete_discovery_flow(self, mock_get_discovery, mock_aiohttp):
        """Test complete flow from operator trigger to UI update."""
        # Setup mock responses
        mock_response = Mock()
        mock_response.status = 200
        mock_response.content_type = "application/json"
        mock_response.json = Mock(
            return_value={"version": "1.0.0", "nodes": ["image_generator", "video_processor"]}
        )

        # Setup aiohttp mock
        mock_session = Mock()
        mock_session.get = Mock(return_value=mock_response)
        mock_session.__aenter__ = Mock(return_value=mock_session)
        mock_session.__aexit__ = Mock(return_value=None)
        mock_aiohttp.ClientSession = Mock(return_value=mock_session)

        # Create real discovery manager
        from blender_movie_director.backend.service_discovery import ServiceDiscoveryManager

        discovery_manager = ServiceDiscoveryManager()
        mock_get_discovery.return_value = discovery_manager

        # Setup context
        context = Mock()
        context.scene = Mock()
        context.scene.movie_director_props = Mock()

        # Mock backend services collection
        mock_services = []

        def mock_add():
            service = Mock()
            service.capabilities = Mock()
            service.capabilities.clear = Mock()
            service.capabilities.add = Mock(return_value=Mock())
            mock_services.append(service)
            return service

        context.scene.movie_director_props.backend_services = Mock()
        context.scene.movie_director_props.backend_services.clear = Mock()
        context.scene.movie_director_props.backend_services.add = mock_add

        # Create and execute operator
        operator = MOVIE_DIRECTOR_OT_discover_services()
        operator.report = Mock()

        # Manually run discovery (simulating thread execution)
        import asyncio

        loop = asyncio.new_event_loop()
        operator._discovery_results = loop.run_until_complete(
            discovery_manager.discover_all_services()
        )
        loop.close()

        # Update properties
        operator._update_service_properties(context)

        # Verify all services were discovered and properties updated
        self.assertEqual(len(mock_services), 4)  # All 4 services

        # Check that ComfyUI was properly configured
        comfyui_service = next((s for s in mock_services if s.name == "comfyui"), None)
        self.assertIsNotNone(comfyui_service)
        self.assertEqual(comfyui_service.status, "connected")
        self.assertEqual(comfyui_service.version, "1.0.0")


if __name__ == "__main__":
    unittest.main()
