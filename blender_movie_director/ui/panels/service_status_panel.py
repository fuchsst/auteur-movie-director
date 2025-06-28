"""Service Status Panel for Blender Movie Director.

This panel displays the real-time status of all backend services and provides
controls for service discovery and management.
"""

import bpy
from bpy.types import Panel


class MOVIE_DIRECTOR_PT_service_status(Panel):
    """Backend Service Status Panel"""

    bl_label = "Backend Services"
    bl_idname = "MOVIE_DIRECTOR_PT_service_status"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Movie Director"
    bl_order = 1  # Show at top

    def draw(self, context):
        layout = self.layout
        props = context.scene.movie_director_props

        # Service Discovery Controls
        box = layout.box()
        box.label(text="Service Discovery", icon="VIEWZOOM")
        
        row = box.row()
        row.operator("movie_director.discover_services", text="Discover Services", icon="FILE_REFRESH")
        
        if props.discovery_in_progress:
            row.enabled = False
            box.label(text="Discovery in progress...", icon="TIME")
        
        if props.last_discovery_time:
            box.label(text=f"Last scan: {props.last_discovery_time}")

        # Service Status Display
        if len(props.backend_services) > 0:
            box = layout.box()
            box.label(text="Service Status", icon="LINKED")
            
            # Summary
            connected_count = sum(1 for s in props.backend_services if s.status == "connected")
            total_count = len(props.backend_services)
            
            row = box.row()
            if connected_count == total_count:
                row.label(text=f"All services connected ({connected_count}/{total_count})", icon="CHECKMARK")
            elif connected_count > 0:
                row.label(text=f"Partial connectivity ({connected_count}/{total_count})", icon="ERROR")
            else:
                row.label(text="No services connected", icon="CANCEL")
            
            # Individual Services
            for service in props.backend_services:
                self._draw_service_status(box, service)
        else:
            # No services discovered yet
            box = layout.box()
            box.label(text="No services discovered", icon="INFO")
            box.label(text="Click 'Discover Services' to scan")

        # Health Monitoring Settings
        box = layout.box()
        box.label(text="Health Monitoring", icon="HEART")
        box.prop(props, "enable_health_checks")
        if props.enable_health_checks:
            box.prop(props, "health_check_interval", text="Interval (seconds)")

    def _draw_service_status(self, layout, service):
        """Draw status for a single service"""
        # Service header with status icon
        row = layout.row()
        
        # Status icon
        if service.status == "connected":
            icon = "CHECKMARK"
        elif service.status == "connecting":
            icon = "TIME"
        elif service.status == "error":
            icon = "ERROR"
        else:
            icon = "CANCEL"
        
        # Service name and status
        row.label(text=service.name.upper(), icon=icon)
        
        # Show details toggle
        row.prop(service, "show_details", text="", icon="TRIA_DOWN" if service.show_details else "TRIA_RIGHT")
        
        # Refresh button
        refresh_op = row.operator("movie_director.refresh_service", text="", icon="FILE_REFRESH")
        refresh_op.service_name = service.name
        
        # Details section
        if service.show_details:
            col = layout.column(align=True)
            col.separator()
            
            # Connection info
            if service.status == "connected":
                col.label(text=f"URL: {service.url}")
                col.label(text=f"Version: {service.version}")
                
                if service.response_time > 0:
                    col.label(text=f"Response: {service.response_time}ms")
                
                # Capabilities
                if len(service.capabilities) > 0:
                    cap_text = ", ".join([cap.name for cap in service.capabilities])
                    col.label(text=f"Capabilities: {cap_text}")
                
                # Test connection button
                test_op = col.operator("movie_director.test_service_connection", text="Test Connection")
                test_op.service_name = service.name
                
            elif service.status == "error" and service.error_message:
                # Error details
                col.label(text="Error:", icon="ERROR")
                # Split long error messages
                error_lines = service.error_message.split('\n')
                for line in error_lines[:3]:  # Show max 3 lines
                    if len(line) > 50:
                        line = line[:47] + "..."
                    col.label(text=f"  {line}")
                
                # Test connection with custom URL
                col.separator()
                test_op = col.operator("movie_director.test_service_connection", text="Test Custom URL")
                test_op.service_name = service.name
                # Note: Custom URL would need to be set via preferences or a popup
            
            col.separator()


class MOVIE_DIRECTOR_PT_service_config(Panel):
    """Service Configuration Panel"""

    bl_label = "Service Configuration"
    bl_idname = "MOVIE_DIRECTOR_PT_service_config"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Movie Director"
    bl_parent_id = "MOVIE_DIRECTOR_PT_service_status"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        
        # Link to addon preferences
        box = layout.box()
        box.label(text="Port Configuration", icon="PREFERENCES")
        box.label(text="Configure custom ports in")
        box.label(text="addon preferences")
        
        # Quick access to preferences
        box.operator("preferences.addon_show", text="Open Preferences").module = "blender_movie_director"
        
        # Auto-discovery settings
        props = context.scene.movie_director_props
        box = layout.box()
        box.label(text="Discovery Settings", icon="VIEWZOOM")
        box.prop(props, "auto_discover", text="Auto-discover on startup")


def register():
    """Register service status panels"""
    bpy.utils.register_class(MOVIE_DIRECTOR_PT_service_status)
    bpy.utils.register_class(MOVIE_DIRECTOR_PT_service_config)


def unregister():
    """Unregister service status panels"""
    bpy.utils.unregister_class(MOVIE_DIRECTOR_PT_service_config)
    bpy.utils.unregister_class(MOVIE_DIRECTOR_PT_service_status)
