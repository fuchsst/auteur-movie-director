"""Service Properties for Blender Movie Director.

This module defines the property groups for storing backend service information.
"""

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup


class ServiceCapability(PropertyGroup):
    """Property group for a service capability."""

    name: StringProperty(
        name="Capability Name",
        description="Name of the capability (e.g., image_generation, voice_cloning)",
        default="",
    )

    version: StringProperty(name="Version", description="Version of this capability", default="1.0")


class BackendServiceStatus(PropertyGroup):
    """Property group for backend service status information."""

    name: StringProperty(name="Service Name", description="Name of the backend service", default="")

    status: EnumProperty(
        name="Status",
        description="Current connection status",
        items=[
            ("disconnected", "Disconnected", "Service is not connected"),
            ("connecting", "Connecting", "Currently attempting to connect"),
            ("connected", "Connected", "Service is connected and ready"),
            ("error", "Error", "Connection error occurred"),
        ],
        default="disconnected",
    )

    url: StringProperty(name="Service URL", description="Full URL of the service", default="")

    version: StringProperty(name="Version", description="Service version", default="unknown")

    last_check: StringProperty(
        name="Last Check", description="Timestamp of last health check", default=""
    )

    error_message: StringProperty(
        name="Error Message", description="Last error message if any", default=""
    )

    show_details: BoolProperty(
        name="Show Details", description="Show detailed information in UI", default=False
    )

    is_required: BoolProperty(
        name="Required Service",
        description="Whether this service is required for basic functionality",
        default=True,
    )

    capabilities: CollectionProperty(
        type=ServiceCapability,
        name="Capabilities",
        description="List of capabilities this service provides",
    )

    # Connection settings
    host: StringProperty(name="Host", description="Service host address", default="localhost")

    port: IntProperty(name="Port", description="Service port number", default=0, min=1, max=65535)

    protocol: StringProperty(
        name="Protocol", description="Connection protocol (http, ws, etc.)", default="http"
    )

    # Health metrics
    response_time: IntProperty(
        name="Response Time", description="Last response time in milliseconds", default=0, min=0
    )

    success_rate: IntProperty(
        name="Success Rate",
        description="Connection success rate percentage",
        default=100,
        min=0,
        max=100,
        subtype="PERCENTAGE",
    )


class MovieDirectorProperties(PropertyGroup):
    """Main property group for Movie Director addon."""

    backend_services: CollectionProperty(
        type=BackendServiceStatus,
        name="Backend Services",
        description="Status of all backend services",
    )

    # Service discovery settings
    auto_discover: BoolProperty(
        name="Auto Discover", description="Automatically discover services on startup", default=True
    )

    discovery_in_progress: BoolProperty(
        name="Discovery In Progress",
        description="Service discovery is currently running",
        default=False,
    )

    last_discovery_time: StringProperty(
        name="Last Discovery", description="Timestamp of last discovery scan", default=""
    )

    # Connection monitoring
    enable_health_checks: BoolProperty(
        name="Enable Health Checks", description="Periodically check service health", default=True
    )

    health_check_interval: IntProperty(
        name="Health Check Interval",
        description="Seconds between health checks",
        default=30,
        min=5,
        max=300,
    )


# Registration
classes = [
    ServiceCapability,
    BackendServiceStatus,
    MovieDirectorProperties,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Add properties to scene
    bpy.types.Scene.movie_director_props = PointerProperty(type=MovieDirectorProperties)


def unregister():
    # Remove properties from scene
    del bpy.types.Scene.movie_director_props

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
