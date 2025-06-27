# User Story: Error Notification System

**Story ID:** STORY-007  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** UI Integration  
**Story Points:** 3  
**Priority:** High (P1)  

---

## Story Description

**As a** user experiencing connection issues  
**I want** clear and actionable error notifications  
**So that** I can understand and resolve problems quickly  

## Acceptance Criteria

### Functional Requirements
- [ ] Display connection errors in non-intrusive notifications
- [ ] Show specific error details (not generic messages)
- [ ] Provide suggested solutions for common errors
- [ ] Allow copying error details for support
- [ ] Log errors with timestamps
- [ ] Group similar errors to avoid spam
- [ ] Support different severity levels (info, warning, error)
- [ ] Link to relevant documentation/help

### Technical Requirements
- [ ] Use Blender's report system appropriately
- [ ] Implement notification queue management
- [ ] Store error history in scene properties
- [ ] Rate limit duplicate notifications
- [ ] Format errors for readability
- [ ] Support multiline error messages
- [ ] Thread-safe error reporting
- [ ] Integrate with logging system

### Quality Requirements
- [ ] Notifications appear within 100ms
- [ ] No modal dialogs for non-critical errors
- [ ] Clear visual hierarchy by severity
- [ ] Accessible color choices
- [ ] Consistent error message format
- [ ] No notification overflow
- [ ] Errors persist for review
- [ ] Mobile-friendly if using Blender on tablets

## Implementation Notes

### Technical Approach

**Error Notification Manager:**
```python
class ErrorNotificationManager:
    def __init__(self):
        self.error_queue = deque(maxlen=100)
        self.last_errors = {}  # For deduplication
        self.error_handlers = {}
        
    def report_error(self, 
                    service: str,
                    error_type: str,
                    message: str,
                    severity: str = 'ERROR',
                    details: Dict = None):
        """Report an error with deduplication"""
        
        # Create error key for deduplication
        error_key = f"{service}:{error_type}:{message}"
        
        # Check for recent duplicate
        if error_key in self.last_errors:
            last_time = self.last_errors[error_key]
            if time.time() - last_time < 30:  # 30 second cooldown
                return
                
        # Record error
        error = {
            'timestamp': time.time(),
            'service': service,
            'type': error_type,
            'message': message,
            'severity': severity,
            'details': details or {}
        }
        
        self.error_queue.append(error)
        self.last_errors[error_key] = time.time()
        
        # Dispatch to handlers
        self._dispatch_error(error)
```

**Error Display Operator:**
```python
class MOVIE_DIRECTOR_OT_show_error_details(Operator):
    bl_idname = "movie_director.show_error_details"
    bl_label = "Error Details"
    bl_description = "Show detailed error information"
    
    error_index: IntProperty()
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=600)
    
    def draw(self, context):
        layout = self.layout
        error = get_error_by_index(self.error_index)
        
        # Error header
        col = layout.column()
        col.label(text=f"Error: {error['type']}", icon='ERROR')
        col.label(text=f"Service: {error['service']}")
        col.label(text=f"Time: {format_timestamp(error['timestamp'])}")
        
        # Error message
        box = layout.box()
        self.draw_wrapped_text(box, error['message'])
        
        # Suggested solutions
        if solutions := self.get_solutions(error):
            layout.label(text="Suggested Solutions:", icon='QUESTION')
            for solution in solutions:
                layout.label(text=f"• {solution}")
        
        # Copy button
        layout.operator("movie_director.copy_error", 
                       text="Copy Error Details").error_index = self.error_index
```

**Error Type Handlers:**
```python
ERROR_SOLUTIONS = {
    'connection_refused': [
        "Check if the backend service is running",
        "Verify the service URL and port are correct",
        "Check firewall settings",
        "Try restarting the backend service"
    ],
    'timeout': [
        "Service may be overloaded, try again later",
        "Check network connectivity",
        "Increase timeout in addon preferences",
        "Verify service is responding to health checks"
    ],
    'authentication_failed': [
        "Check API key or credentials",
        "Verify authentication is configured correctly",
        "Contact service administrator for access"
    ],
    'version_mismatch': [
        "Update backend service to compatible version",
        "Check addon documentation for version requirements",
        "Consider downgrading if necessary"
    ]
}

def get_error_solutions(error_type):
    """Get contextual solutions for error type"""
    return ERROR_SOLUTIONS.get(error_type, [
        "Check service documentation",
        "Verify configuration settings",
        "Contact support if issue persists"
    ])
```

**Blender Report Integration:**
```python
def report_to_blender(error):
    """Report error through Blender's system"""
    severity_map = {
        'INFO': {'INFO'},
        'WARNING': {'WARNING'},
        'ERROR': {'ERROR'}
    }
    
    # Format message for Blender
    message = f"{error['service']}: {error['message']}"
    
    # Report to operator context if available
    if context := bpy.context:
        context.window_manager.report(
            severity_map[error['severity']], 
            message
        )
    
    # Also log to console
    if error['severity'] == 'ERROR':
        print(f"[Movie Director Error] {message}")
```

**Error History Panel:**
```python
class MOVIE_DIRECTOR_PT_error_history(Panel):
    bl_label = "Error History"
    bl_idname = "MOVIE_DIRECTOR_PT_error_history"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Movie Director"
    bl_parent_id = "MOVIE_DIRECTOR_PT_connection_status"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        errors = get_recent_errors(limit=10)
        
        if not errors:
            layout.label(text="No recent errors", icon='CHECKMARK')
            return
            
        for i, error in enumerate(errors):
            row = layout.row()
            
            # Severity icon
            icon = self.get_severity_icon(error['severity'])
            row.label(icon=icon)
            
            # Error summary
            col = row.column()
            col.label(text=error['service'])
            col.label(text=truncate(error['message'], 40))
            
            # Details button
            row.operator("movie_director.show_error_details",
                        text="", icon='INFO').error_index = i
```

### Error Categories
1. **Connection Errors**: Network, timeout, refused
2. **Configuration Errors**: Invalid URL, missing service
3. **Authentication Errors**: API key, permissions
4. **Runtime Errors**: Out of memory, model errors
5. **Version Errors**: Incompatible versions

### User Experience
- Non-modal notifications by default
- Persistent error log for review
- One-click access to solutions
- Copy-paste for support tickets

## Testing Strategy

### Unit Tests
```python
class TestErrorNotification(unittest.TestCase):
    def test_error_deduplication(self):
        # Send duplicate errors
        # Verify only one shown
        
    def test_error_formatting(self):
        # Test various error types
        # Verify readable output
        
    def test_solution_mapping(self):
        # Test error solutions
        # Verify relevance
```

### UI Tests
- Test notification appearance
- Verify error history panel
- Test copy functionality
- Check accessibility

## Dependencies
- All backend client stories (STORY-002-004) generate errors
- STORY-005: Errors shown in status panel
- Blender's report system

## Related Stories
- Enhanced by STORY-008 (Health Monitoring)
- Supports all connection stories
- Used by troubleshooting documentation

## Definition of Done
- [ ] Error notifications working
- [ ] Deduplication functional
- [ ] Solutions provided for common errors
- [ ] Error history accessible
- [ ] Copy functionality works
- [ ] No notification spam
- [ ] Clear error formatting
- [ ] Documentation complete

---

**Sign-off:**
- [ ] Development Lead
- [ ] UI/UX Designer
- [ ] QA Engineer