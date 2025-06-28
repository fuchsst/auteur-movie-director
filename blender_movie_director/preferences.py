"""Addon Preferences for Blender Movie Director.

This module defines the addon preferences for configuring backend services.
"""

import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty
from bpy.types import AddonPreferences


class MovieDirectorPreferences(AddonPreferences):
    bl_idname = __package__

    # Service Discovery
    auto_discover_on_startup: BoolProperty(
        name="Auto Discover on Startup",
        description="Automatically discover services when Blender starts",
        default=True,
    )

    use_custom_ports: BoolProperty(
        name="Use Custom Ports", description="Override default service ports", default=False
    )

    # ComfyUI Settings
    comfyui_port: IntProperty(
        name="ComfyUI Port",
        description="Custom port for ComfyUI service",
        default=8188,
        min=1,
        max=65535,
    )

    comfyui_host: StringProperty(
        name="ComfyUI Host", description="Custom host for ComfyUI service", default="localhost"
    )

    # Wan2GP Settings
    wan2gp_port: IntProperty(
        name="Wan2GP Port",
        description="Custom port for Wan2GP service",
        default=7860,
        min=1,
        max=65535,
    )

    wan2gp_host: StringProperty(
        name="Wan2GP Host", description="Custom host for Wan2GP service", default="localhost"
    )

    # RVC Settings
    rvc_port: IntProperty(
        name="RVC Port", description="Custom port for RVC service", default=7865, min=1, max=65535
    )

    rvc_host: StringProperty(
        name="RVC Host", description="Custom host for RVC service", default="localhost"
    )

    # AudioLDM Settings
    audioldm_port: IntProperty(
        name="AudioLDM Port",
        description="Custom port for AudioLDM service",
        default=7863,
        min=1,
        max=65535,
    )

    audioldm_host: StringProperty(
        name="AudioLDM Host", description="Custom host for AudioLDM service", default="localhost"
    )

    # Connection Settings
    connection_timeout: IntProperty(
        name="Connection Timeout",
        description="Timeout for service connections in seconds",
        default=5,
        min=1,
        max=30,
    )

    retry_attempts: IntProperty(
        name="Retry Attempts",
        description="Number of connection retry attempts",
        default=3,
        min=1,
        max=10,
    )

    # Health Check Settings
    enable_health_monitoring: BoolProperty(
        name="Enable Health Monitoring",
        description="Monitor service health in background",
        default=True,
    )

    health_check_interval: IntProperty(
        name="Health Check Interval",
        description="Seconds between health checks",
        default=30,
        min=5,
        max=300,
    )

    # Logging
    log_level: EnumProperty(
        name="Log Level",
        description="Logging verbosity for debugging",
        items=[
            ("DEBUG", "Debug", "Detailed debug logging"),
            ("INFO", "Info", "Informational messages"),
            ("WARNING", "Warning", "Warnings only"),
            ("ERROR", "Error", "Errors only"),
        ],
        default="INFO",
    )

    def draw(self, context):
        layout = self.layout

        # Service Discovery Section
        box = layout.box()
        box.label(text="Service Discovery", icon="VIEWZOOM")
        box.prop(self, "auto_discover_on_startup")

        # Custom Ports Section
        box = layout.box()
        box.prop(self, "use_custom_ports")

        if self.use_custom_ports:
            col = box.column(align=True)
            col.label(text="Backend Services:")

            # ComfyUI
            row = col.row(align=True)
            row.label(text="ComfyUI:")
            row.prop(self, "comfyui_host", text="")
            row.prop(self, "comfyui_port", text="")

            # Wan2GP
            row = col.row(align=True)
            row.label(text="Wan2GP:")
            row.prop(self, "wan2gp_host", text="")
            row.prop(self, "wan2gp_port", text="")

            # RVC
            row = col.row(align=True)
            row.label(text="RVC:")
            row.prop(self, "rvc_host", text="")
            row.prop(self, "rvc_port", text="")

            # AudioLDM
            row = col.row(align=True)
            row.label(text="AudioLDM:")
            row.prop(self, "audioldm_host", text="")
            row.prop(self, "audioldm_port", text="")

        # Connection Settings
        box = layout.box()
        box.label(text="Connection Settings", icon="LINKED")
        col = box.column(align=True)
        col.prop(self, "connection_timeout")
        col.prop(self, "retry_attempts")

        # Health Monitoring
        box = layout.box()
        box.label(text="Health Monitoring", icon="HEART")
        box.prop(self, "enable_health_monitoring")
        if self.enable_health_monitoring:
            box.prop(self, "health_check_interval")

        # Logging
        box = layout.box()
        box.label(text="Logging", icon="INFO")
        box.prop(self, "log_level")

        # Actions
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("movie_director.discover_services", icon="VIEWZOOM")
        row.operator("movie_director.test_all_connections", icon="LINKED")


# Registration
def register():
    bpy.utils.register_class(MovieDirectorPreferences)


def unregister():
    bpy.utils.unregister_class(MovieDirectorPreferences)
