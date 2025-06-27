# User Story: Connection Status Panel

**Story ID:** STORY-005  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** UI Integration  
**Story Points:** 5  
**Priority:** Critical (P0)  

---

## Story Description

**As a** Blender user  
**I want** to see the connection status of all backend services  
**So that** I know which AI generation features are available  

## Acceptance Criteria

### Functional Requirements
- [ ] Display status for all 4 backend services (ComfyUI, Wan2GP, RVC, AudioLDM)
- [ ] Show separate status for LLM integration (API key validity)
- [ ] Show connection state: Connected (green), Connecting (yellow), Disconnected (red)
- [ ] Display service version/capability info when connected
- [ ] Show available LLM models when configured
- [ ] Provide "Refresh" button to re-check connections
- [ ] Show last connection attempt timestamp
- [ ] Indicate if service is required vs optional
- [ ] Collapsible details section per service
- [ ] Overall system health indicator

### Technical Requirements
- [ ] Implement as Blender Panel class
- [ ] Use bpy.props for status storage
- [ ] Real-time updates via bpy.app.timers
- [ ] Non-blocking UI updates
- [ ] Custom icon/color indicators
- [ ] Responsive layout for different panel widths
- [ ] Proper panel registration/unregistration
- [ ] Thread-safe status updates

### Quality Requirements
- [ ] UI updates within 100ms of status change
- [ ] No flickering during updates
- [ ] Clear visual hierarchy
- [ ] Tooltips for all status indicators
- [ ] Keyboard navigation support
- [ ] Consistent with Blender UI guidelines
- [ ] Works in all Blender workspace layouts
- [ ] Accessible color choices

## Implementation Notes

### Technical Approach

**Main Status Panel:**
```python
class MOVIE_DIRECTOR_PT_connection_status(Panel):
    bl_label = "Backend Services"
    bl_idname = "MOVIE_DIRECTOR_PT_connection_status"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Movie Director"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.movie_director_props
        
        # Overall status
        row = layout.row()
        row.scale_y = 1.5
        status_icon = self.get_overall_status_icon(props)
        row.label(text="System Status", icon=status_icon)
        
        # Refresh button
        row.operator("movie_director.refresh_connections", 
                    text="", icon='FILE_REFRESH')
        
        # Backend services
        layout.label(text="Backend Services:", icon='LINKED')
        for service in props.backend_services:
            self.draw_service_status(layout, service)
            
        # LLM Integration
        layout.separator()
        layout.label(text="LLM Integration:", icon='TEXT')
        self.draw_llm_status(layout, props.llm_status)
```

**Service Status Display:**
```python
def draw_service_status(self, layout, service):
    """Draw individual service status"""
    box = layout.box()
    row = box.row()
    
    # Status icon and name
    icon = self.get_status_icon(service.status)
    row.label(text=service.name, icon=icon)
    
    # Connection state
    status_text = service.status.title()
    if service.status == 'connected':
        row.label(text=status_text, icon='CHECKMARK')
    elif service.status == 'connecting':
        row.label(text=status_text, icon='TIME')
    else:
        row.label(text=status_text, icon='X')
    
    # Expandable details
    if service.show_details:
        col = box.column(align=True)
        col.label(text=f"URL: {service.url}")
        col.label(text=f"Version: {service.version}")
        col.label(text=f"Last Check: {service.last_check}")
        
        if service.error_message:
            col.label(text=f"Error: {service.error_message}", 
                     icon='ERROR')
                     
def draw_llm_status(self, layout, llm_status):
    """Draw LLM integration status"""
    box = layout.box()
    row = box.row()
    
    # LLM status icon and name
    icon = 'CHECKMARK' if llm_status.configured else 'X'
    row.label(text="Language Models", icon='TEXT')
    
    # Configuration state
    if llm_status.configured:
        row.label(text="Configured", icon='CHECKMARK')
    else:
        row.label(text="Not Configured", icon='X')
    
    # Expandable details
    if llm_status.show_details:
        col = box.column(align=True)
        
        if llm_status.configured:
            col.label(text=f"Active Model: {llm_status.active_model}")
            col.label(text=f"Available Models: {llm_status.model_count}")
            col.label(text=f"Providers: {llm_status.providers}")
        else:
            col.label(text="No API keys configured", icon='INFO')
            col.label(text="Set environment variables:")
            col.label(text="  - OPENAI_API_KEY")
            col.label(text="  - ANTHROPIC_API_KEY")
            col.label(text="  - AZURE_API_KEY")
```

**Status Properties:**
```python
class BackendServiceStatus(PropertyGroup):
    name: StringProperty(name="Service Name")
    status: EnumProperty(
        name="Status",
        items=[
            ('disconnected', "Disconnected", ""),
            ('connecting', "Connecting", ""),
            ('connected', "Connected", ""),
            ('error', "Error", "")
        ],
        default='disconnected'
    )
    url: StringProperty(name="Service URL")
    version: StringProperty(name="Version")
    last_check: StringProperty(name="Last Check")
    error_message: StringProperty(name="Error Message")
    show_details: BoolProperty(name="Show Details", default=False)
    is_required: BoolProperty(name="Required Service", default=True)

class LLMIntegrationStatus(PropertyGroup):
    configured: BoolProperty(name="Configured", default=False)
    active_model: StringProperty(name="Active Model", default="None")
    model_count: IntProperty(name="Model Count", default=0)
    providers: StringProperty(name="Providers", default="")
    show_details: BoolProperty(name="Show Details", default=False)
    last_check: StringProperty(name="Last Check")
```

**Real-time Updates:**
```python
def connection_status_timer():
    """Timer function for UI updates"""
    # Get current backend connection states
    backend_states = get_backend_states()
    
    # Update backend service properties
    for service, state in backend_states.items():
        update_service_property(service, state)
    
    # Get LLM integration status
    llm_state = get_llm_status()
    update_llm_property(llm_state)
    
    # Trigger UI redraw
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()
    
    return 1.0  # Repeat every second

# Register timer on addon enable
bpy.app.timers.register(connection_status_timer)
```

### Blender UI Integration
- Panel in 3D Viewport sidebar
- Also available in Properties panel
- Custom colors using theme colors
- Icons from Blender's icon set

### Visual Design
- Backend Services:
  - Green checkmark: Connected
  - Yellow clock: Connecting
  - Red X: Disconnected
  - Orange warning: Error state
- LLM Integration:
  - Green checkmark: API keys configured
  - Red X: No API keys
  - Shows model count when configured
- Overall health uses traffic light metaphor

### User Interactions
- Click service name to toggle details
- Refresh button for manual check
- Hover for detailed tooltips
- Copy error messages to clipboard

## Testing Strategy

### Unit Tests
```python
class TestConnectionPanel(unittest.TestCase):
    def test_panel_registration(self):
        # Verify panel registers correctly
        # Check all properties initialized
        
    def test_status_updates(self):
        # Mock status changes
        # Verify UI reflects changes
        
    def test_timer_function(self):
        # Test timer execution
        # Verify no UI blocking
```

### UI Tests
- Manual testing in all workspace layouts
- Verify responsive design
- Test with different DPI settings
- Accessibility testing

## Dependencies
- STORY-001: Service Discovery (provides backend status data)
- STORY-002-003: Backend clients (provide connection state)
- STORY-004: LLM Integration Layer (provides model availability)
- STORY-010: Health Check Service (provides status updates)
- Blender 3.6+ for UI features

## Related Stories
- Expanded by STORY-008 (Health Monitoring Dashboard)
- Used by STORY-007 (Error Notification System)
- Configuration in STORY-006 (Service Configuration UI)

## Definition of Done
- [ ] Panel displays all service statuses
- [ ] Real-time updates working
- [ ] Visual indicators clear and consistent
- [ ] Refresh functionality works
- [ ] Details expansion smooth
- [ ] No UI performance impact
- [ ] Follows Blender UI guidelines
- [ ] User documentation complete

---

**Sign-off:**
- [ ] Development Lead
- [ ] UI/UX Designer
- [ ] QA Engineer