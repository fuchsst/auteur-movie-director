# User Story: Service Configuration UI

**Story ID:** STORY-006  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** UI Integration  
**Story Points:** 5  
**Priority:** High (P1)  

---

## Story Description

**As a** technical user with custom backend setups  
**I want** to configure backend service endpoints through the UI  
**So that** I can use non-standard ports or remote services  

## Acceptance Criteria

### Functional Requirements
- [ ] Access configuration through addon preferences
- [ ] Configure URL/port for each backend service
- [ ] Test connection button per service
- [ ] Save/load configuration presets
- [ ] Import/export configuration files
- [ ] Environment variable override support
- [ ] Reset to defaults option
- [ ] Validation of URL formats

### Technical Requirements
- [ ] Implement in AddonPreferences class
- [ ] Persist settings in Blender preferences
- [ ] Support both http:// and ws:// protocols
- [ ] IPv4 and IPv6 address support
- [ ] Port range validation (1-65535)
- [ ] Non-blocking connection tests
- [ ] Configuration migration support
- [ ] Thread-safe preference updates

### Quality Requirements
- [ ] Changes apply without addon restart
- [ ] Clear validation error messages
- [ ] Intuitive layout and grouping
- [ ] Responsive to preference window size
- [ ] Undo/redo support for changes
- [ ] Tooltips explain each setting
- [ ] Consistent with Blender preferences
- [ ] Fast connection test (<2s)

## Implementation Notes

### Technical Approach

**Addon Preferences Panel:**
```python
class MOVIE_DIRECTOR_Preferences(AddonPreferences):
    bl_idname = "movie_director"
    
    # ComfyUI settings
    comfyui_enabled: BoolProperty(
        name="Enable ComfyUI",
        default=True
    )
    comfyui_url: StringProperty(
        name="ComfyUI URL",
        default="ws://localhost:8188",
        description="WebSocket URL for ComfyUI server"
    )
    
    # Wan2GP settings
    wan2gp_enabled: BoolProperty(
        name="Enable Wan2GP",
        default=True
    )
    wan2gp_url: StringProperty(
        name="Wan2GP URL",
        default="http://localhost:7860",
        description="HTTP URL for Wan2GP Gradio interface"
    )
    
    # Configuration presets
    config_preset: EnumProperty(
        name="Configuration Preset",
        items=get_config_presets,
        description="Load predefined configurations"
    )
    
    def draw(self, context):
        layout = self.layout
        
        # Preset selector
        row = layout.row()
        row.prop(self, "config_preset")
        row.operator("movie_director.save_preset", icon='ADD')
        
        # Service configurations
        for service in BACKEND_SERVICES:
            self.draw_service_config(layout, service)
```

**Service Configuration UI:**
```python
def draw_service_config(self, layout, service_name):
    """Draw configuration for individual service"""
    box = layout.box()
    
    # Enable/disable service
    row = box.row()
    row.prop(self, f"{service_name}_enabled")
    
    # Connection settings
    if getattr(self, f"{service_name}_enabled"):
        col = box.column()
        col.prop(self, f"{service_name}_url")
        
        # Advanced settings
        if self.show_advanced:
            col.prop(self, f"{service_name}_timeout")
            col.prop(self, f"{service_name}_retry_count")
        
        # Test connection
        row = col.row()
        test_op = row.operator(
            "movie_director.test_connection",
            text=f"Test {service_name.upper()}"
        )
        test_op.service = service_name
        
        # Status indicator
        status = get_test_status(service_name)
        if status:
            row.label(text=status, icon=get_status_icon(status))
```

**Connection Test Operator:**
```python
class MOVIE_DIRECTOR_OT_test_connection(Operator):
    bl_idname = "movie_director.test_connection"
    bl_label = "Test Connection"
    bl_description = "Test connection to backend service"
    
    service: StringProperty()
    
    def execute(self, context):
        # Run async test
        asyncio.create_task(self.test_connection_async())
        return {'FINISHED'}
    
    async def test_connection_async(self):
        """Async connection test"""
        prefs = get_addon_preferences()
        url = getattr(prefs, f"{self.service}_url")
        
        try:
            # Test connection based on service type
            if self.service == "comfyui":
                await test_websocket_connection(url)
            else:
                await test_http_connection(url)
                
            self.report({'INFO'}, f"{self.service} connection successful")
        except Exception as e:
            self.report({'ERROR'}, f"{self.service} connection failed: {e}")
```

**Configuration Validation:**
```python
def validate_service_url(self, context):
    """Validate URL format and structure"""
    url = self.comfyui_url
    
    try:
        parsed = urlparse(url)
        
        # Check protocol
        if parsed.scheme not in ['http', 'https', 'ws', 'wss']:
            raise ValueError("Invalid protocol")
            
        # Check host
        if not parsed.hostname:
            raise ValueError("Missing hostname")
            
        # Check port
        if parsed.port and not (1 <= parsed.port <= 65535):
            raise ValueError("Invalid port number")
            
    except Exception as e:
        # Show validation error in UI
        self.url_error = str(e)
        return
        
    self.url_error = ""
```

**Environment Variable Support:**
```python
def get_service_url(service_name):
    """Get service URL with env var override"""
    env_var = f"MOVIE_DIRECTOR_{service_name.upper()}_URL"
    
    # Check environment first
    env_url = os.environ.get(env_var)
    if env_url:
        return env_url
        
    # Fall back to preferences
    prefs = get_addon_preferences()
    return getattr(prefs, f"{service_name}_url")
```

### Blender Integration
- Preferences accessible via Edit > Preferences > Add-ons
- Settings persist across Blender sessions
- Integrated with Blender's preset system
- Supports preference import/export

### Configuration Options
1. **Basic Settings**: URL, enabled state
2. **Advanced Settings**: Timeout, retry count, auth
3. **Presets**: Local, Remote, Development, Production
4. **Import/Export**: JSON configuration files

## Testing Strategy

### Unit Tests
```python
class TestServiceConfiguration(unittest.TestCase):
    def test_url_validation(self):
        # Test various URL formats
        # Verify validation logic
        
    def test_preference_persistence(self):
        # Change preferences
        # Verify saved correctly
        
    def test_env_var_override(self):
        # Set environment variables
        # Verify precedence
```

### Integration Tests
- Test with actual backend services
- Verify configuration changes apply
- Test preset loading
- Import/export functionality

## Dependencies
- STORY-001: Service Discovery (uses configured endpoints)
- Blender preferences system
- URL parsing libraries

## Related Stories
- Configuration used by STORY-002-004 (Backend clients)
- Status shown in STORY-005 (Connection Status Panel)
- Errors handled by STORY-007 (Error Notification)

## Definition of Done
- [ ] Preferences UI implemented
- [ ] All services configurable
- [ ] Connection tests functional
- [ ] URL validation working
- [ ] Presets save/load correctly
- [ ] Environment variables work
- [ ] Settings persist properly
- [ ] Documentation complete

---

**Sign-off:**
- [ ] Development Lead
- [ ] UI/UX Designer
- [ ] QA Engineer