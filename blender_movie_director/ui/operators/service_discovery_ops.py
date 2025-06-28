"""Service Discovery Operators for Blender Movie Director.

This module provides Blender operators for discovering and managing backend services.
"""

import asyncio
import logging
import threading

import bpy
from bpy.types import Operator

from ...backend.service_discovery import get_discovery_manager

logger = logging.getLogger(__name__)


class MOVIE_DIRECTOR_OT_discover_services(Operator):
    """Discover all available AI backend services"""

    bl_idname = "movie_director.discover_services"
    bl_label = "Discover Services"
    bl_description = "Automatically discover all available AI backend services"
    bl_options = {"REGISTER", "UNDO"}

    _timer = None
    _thread = None
    _discovery_complete = False
    _discovery_results = None

    def execute(self, context):
        """Execute service discovery in a background thread."""
        # Start discovery in background thread
        self._discovery_complete = False
        self._thread = threading.Thread(target=self._run_discovery)
        self._thread.start()

        # Register timer for UI updates
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        self.report({"INFO"}, "Service discovery started...")
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        """Handle modal updates during discovery."""
        if event.type == "TIMER":
            if self._discovery_complete:
                # Discovery finished, update properties
                self._update_service_properties(context)

                # Clean up
                wm = context.window_manager
                wm.event_timer_remove(self._timer)

                # Report results
                available_count = len(
                    [s for s in self._discovery_results.values() if s.is_available]
                )
                self.report({"INFO"}, f"Discovery complete: {available_count} services found")

                return {"FINISHED"}

        return {"PASS_THROUGH"}

    def _run_discovery(self):
        """Run service discovery in background thread."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Get custom ports from preferences if set
            custom_ports = self._get_custom_ports()

            # Run discovery
            discovery_manager = get_discovery_manager()
            self._discovery_results = loop.run_until_complete(
                discovery_manager.discover_all_services(custom_ports)
            )

        except Exception as e:
            logger.error(f"Service discovery failed: {e}")
            self._discovery_results = {}
        finally:
            self._discovery_complete = True
            loop.close()

    def _get_custom_ports(self):
        """Get custom port settings from addon preferences."""
        preferences = bpy.context.preferences.addons[__package__.split(".")[0]].preferences
        custom_ports = {}

        # Check if custom ports are configured
        if preferences.use_custom_ports:
            if preferences.comfyui_port > 0:
                custom_ports["comfyui"] = preferences.comfyui_port
            if preferences.wan2gp_port > 0:
                custom_ports["wan2gp"] = preferences.wan2gp_port
            if preferences.rvc_port > 0:
                custom_ports["rvc"] = preferences.rvc_port
            if preferences.audioldm_port > 0:
                custom_ports["audioldm"] = preferences.audioldm_port

        return custom_ports

    def _update_service_properties(self, context):
        """Update service properties with discovery results."""
        props = context.scene.movie_director_props

        # Clear existing services
        props.backend_services.clear()

        # Add discovered services
        for service_name, service_info in self._discovery_results.items():
            service_prop = props.backend_services.add()
            service_prop.name = service_info.name
            service_prop.status = "connected" if service_info.is_available else "disconnected"
            service_prop.url = f"{service_info.protocol}://{service_info.host}:{service_info.port}"
            service_prop.version = service_info.version or "unknown"
            service_prop.error_message = service_info.error_message or ""
            service_prop.is_required = service_name in [
                "comfyui",
                "wan2gp",
            ]  # Mark core services as required

            # Set capabilities
            service_prop.capabilities.clear()
            for cap in service_info.capabilities:
                cap_prop = service_prop.capabilities.add()
                cap_prop.name = cap

        # Force UI update
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


class MOVIE_DIRECTOR_OT_refresh_service(Operator):
    """Refresh connection status for a specific service"""

    bl_idname = "movie_director.refresh_service"
    bl_label = "Refresh Service"
    bl_description = "Refresh the connection status for this service"

    service_name: bpy.props.StringProperty(
        name="Service Name", description="Name of the service to refresh", default=""
    )

    def execute(self, context):
        """Execute service refresh."""
        if not self.service_name:
            self.report({"ERROR"}, "No service specified")
            return {"CANCELLED"}

        # Run refresh in background
        threading.Thread(target=self._refresh_service, args=(context, self.service_name)).start()

        self.report({"INFO"}, f"Refreshing {self.service_name}...")
        return {"FINISHED"}

    def _refresh_service(self, context, service_name):
        """Refresh a single service in background thread."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Refresh service
            discovery_manager = get_discovery_manager()
            service_info = loop.run_until_complete(discovery_manager.refresh_service(service_name))

            if service_info:
                # Update property in main thread
                bpy.app.timers.register(
                    lambda: self._update_service_property(context, service_info), first_interval=0
                )

        except Exception as e:
            logger.error(f"Service refresh failed: {e}")
        finally:
            loop.close()

    def _update_service_property(self, context, service_info):
        """Update a single service property (must be called from main thread)."""
        props = context.scene.movie_director_props

        # Find and update the service
        for service_prop in props.backend_services:
            if service_prop.name == service_info.name:
                service_prop.status = "connected" if service_info.is_available else "disconnected"
                service_prop.url = (
                    f"{service_info.protocol}://{service_info.host}:{service_info.port}"
                )
                service_prop.version = service_info.version or "unknown"
                service_prop.error_message = service_info.error_message or ""
                service_prop.last_check = str(int(service_info.last_check))
                break

        # Force UI update
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()

        return None  # Don't repeat timer


class MOVIE_DIRECTOR_OT_test_service_connection(Operator):
    """Test connection to a specific service"""

    bl_idname = "movie_director.test_service_connection"
    bl_label = "Test Connection"
    bl_description = "Test the connection to this service"

    service_name: bpy.props.StringProperty(
        name="Service Name", description="Name of the service to test", default=""
    )

    service_url: bpy.props.StringProperty(
        name="Service URL", description="Custom URL to test", default=""
    )

    def execute(self, context):
        """Execute connection test."""
        if not self.service_name:
            self.report({"ERROR"}, "No service specified")
            return {"CANCELLED"}

        # Parse URL if provided
        if self.service_url:
            try:
                from urllib.parse import urlparse

                parsed = urlparse(self.service_url)
                host = parsed.hostname or "localhost"
                port = parsed.port
                if not port:
                    self.report({"ERROR"}, "No port specified in URL")
                    return {"CANCELLED"}
            except:
                self.report({"ERROR"}, "Invalid URL format")
                return {"CANCELLED"}
        else:
            # Use discovered service info
            discovery_manager = get_discovery_manager()
            service_info = discovery_manager.get_service_info(self.service_name)
            if not service_info:
                self.report({"ERROR"}, f"Service {self.service_name} not found")
                return {"CANCELLED"}
            host = service_info.host
            port = service_info.port

        # Test connection
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)

        try:
            result = sock.connect_ex((host, port))
            if result == 0:
                self.report(
                    {"INFO"}, f"Successfully connected to {self.service_name} at {host}:{port}"
                )
            else:
                self.report({"ERROR"}, f"Failed to connect to {self.service_name} at {host}:{port}")
        except Exception as e:
            self.report({"ERROR"}, f"Connection test failed: {str(e)}")
        finally:
            sock.close()

        return {"FINISHED"}


# Registration
classes = [
    MOVIE_DIRECTOR_OT_discover_services,
    MOVIE_DIRECTOR_OT_refresh_service,
    MOVIE_DIRECTOR_OT_test_service_connection,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
