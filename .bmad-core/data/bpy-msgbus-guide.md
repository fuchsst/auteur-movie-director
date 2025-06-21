# bpy.msgbus Guide for Movie Director Addon

## Overview

`bpy.msgbus` provides Blender's message bus system for reactive programming and event-driven operations. For the Movie Director addon, the message bus enables automatic UI updates, asset synchronization, and responsive workflows based on data changes.

## Core Message Bus Concepts

### Message Bus Fundamentals
```python
import bpy
from bpy.msgbus import subscribe_rna, clear_by_owner

# Message bus allows subscribing to data changes
# When subscribed data changes, callback functions are automatically called
# This enables reactive UI and workflow automation
```

### Subscription Types
```python
# Property change subscriptions
def on_property_change(context):
    """Called when subscribed property changes"""
    print("Property changed!")

# RNA path subscriptions for specific properties
subscribe_rna(
    key=bpy.types.Scene.movie_director,  # What to watch
    owner=object(),                       # Subscription owner for cleanup
    notify=on_property_change,           # Callback function
    args=(bpy.context,)                  # Arguments to pass
)

# Object change subscriptions
def on_object_change():
    """Called when object data changes"""
    print("Object data changed!")

subscribe_rna(
    key=bpy.context.active_object,
    owner=object(),
    notify=on_object_change
)
```

## Movie Director Message Bus Patterns

### Asset Change Monitoring
```python
class AssetChangeManager:
    """Manage asset change subscriptions for Movie Director"""
    
    def __init__(self):
        self.subscription_owner = object()  # Unique owner for cleanup
        self.active_subscriptions = []
    
    def subscribe_to_character_changes(self, character_obj):
        """Subscribe to character asset property changes"""
        def on_character_change(context):
            self.handle_character_update(character_obj, context)
        
        # Subscribe to character properties
        if hasattr(character_obj, 'movie_director'):
            subscribe_rna(
                key=character_obj.movie_director,
                owner=self.subscription_owner,
                notify=on_character_change,
                args=(bpy.context,)
            )
            self.active_subscriptions.append(character_obj)
    
    def handle_character_update(self, character_obj, context):
        """Handle character asset updates"""
        print(f"Character {character_obj.name} updated")
        
        # Update Asset Browser preview if needed
        if character_obj.asset_data:
            character_obj.asset_generate_preview()
        
        # Invalidate dependent shots
        self.invalidate_character_shots(character_obj)
        
        # Update UI
        self.refresh_character_ui(context)
    
    def invalidate_character_shots(self, character_obj):
        """Mark shots using this character for regeneration"""
        character_name = character_obj.movie_director.character_name
        
        for obj in bpy.context.scene.objects:
            if (hasattr(obj, 'movie_director') and 
                obj.movie_director.asset_type == 'shot'):
                # Check if shot uses this character
                if self.shot_uses_character(obj, character_name):
                    obj.movie_director.generation_status = 'outdated'
    
    def cleanup_subscriptions(self):
        """Clean up all subscriptions"""
        clear_by_owner(self.subscription_owner)
        self.active_subscriptions.clear()
```

### Generation Progress Monitoring
```python
class GenerationProgressMonitor:
    """Monitor generation progress and update UI reactively"""
    
    def __init__(self):
        self.owner = object()
        self.setup_progress_subscriptions()
    
    def setup_progress_subscriptions(self):
        """Set up subscriptions for generation progress changes"""
        # Subscribe to main generation progress
        subscribe_rna(
            key=(bpy.types.Scene, "movie_director"),
            owner=self.owner,
            notify=self.on_progress_change,
            args=()
        )
    
    def on_progress_change(self):
        """Handle generation progress changes"""
        scene = bpy.context.scene
        if not hasattr(scene, 'movie_director'):
            return
        
        progress = scene.movie_director.generation_progress
        active = scene.movie_director.generation_active
        
        # Update status message
        if active and progress < 1.0:
            scene.movie_director.generation_status = f"Generating... {int(progress * 100)}%"
        elif progress >= 1.0:
            scene.movie_director.generation_status = "Generation Complete"
            scene.movie_director.generation_active = False
        
        # Force UI redraw
        self.force_ui_update()
    
    def force_ui_update(self):
        """Force UI update across all relevant areas"""
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type in {'VIEW_3D', 'PROPERTIES'}:
                    area.tag_redraw()
```

### Workflow State Synchronization
```python
class WorkflowStateManager:
    """Synchronize workflow state across UI and agents"""
    
    def __init__(self):
        self.owner = object()
        self.setup_workflow_subscriptions()
    
    def setup_workflow_subscriptions(self):
        """Set up subscriptions for workflow state changes"""
        # Subscribe to backend connection status
        subscribe_rna(
            key=(bpy.types.Scene, "movie_director"),
            owner=self.owner,
            notify=self.on_backend_status_change
        )
        
        # Subscribe to VRAM usage changes
        subscribe_rna(
            key=(bpy.types.Scene, "movie_director"),
            owner=self.owner,
            notify=self.on_vram_change
        )
    
    def on_backend_status_change(self):
        """Handle backend connection status changes"""
        scene = bpy.context.scene
        movie_props = scene.movie_director
        
        # Check if backends are available
        backends_available = self.check_backend_availability()
        
        # Update UI state based on availability
        if not backends_available:
            movie_props.generation_status = "Backends Unavailable"
            self.disable_generation_operators()
        else:
            movie_props.generation_status = "Ready"
            self.enable_generation_operators()
    
    def on_vram_change(self):
        """Handle VRAM availability changes"""
        scene = bpy.context.scene
        movie_props = scene.movie_director
        
        # Update VRAM-dependent settings
        available_vram = movie_props.available_vram
        
        if available_vram < 8.0:
            movie_props.vram_budget_mode = 'conservative'
            movie_props.generation_status = "Low VRAM - Conservative Mode"
        elif available_vram >= 24.0:
            movie_props.vram_budget_mode = 'aggressive'
```

## Advanced Message Bus Patterns

### Cross-Agent Communication
```python
class AgentCoordinator:
    """Coordinate between different agents using message bus"""
    
    def __init__(self):
        self.owner = object()
        self.agent_states = {}
        self.setup_agent_subscriptions()
    
    def setup_agent_subscriptions(self):
        """Set up subscriptions for agent state changes"""
        # Subscribe to changes that affect multiple agents
        subscribe_rna(
            key=(bpy.types.Object, "movie_director"),
            owner=self.owner,
            notify=self.on_asset_change
        )
    
    def on_asset_change(self):
        """Handle asset changes that affect multiple agents"""
        # Determine which agents need to respond
        changed_asset = bpy.context.active_object
        if not changed_asset or not hasattr(changed_asset, 'movie_director'):
            return
        
        asset_type = changed_asset.movie_director.asset_type
        
        # Coordinate agent responses
        if asset_type == 'character':
            self.notify_character_dependent_agents(changed_asset)
        elif asset_type == 'style':
            self.notify_style_dependent_agents(changed_asset)
        elif asset_type == 'shot':
            self.notify_shot_dependent_agents(changed_asset)
    
    def notify_character_dependent_agents(self, character_obj):
        """Notify agents that depend on character changes"""
        # Cinematographer needs to regenerate shots using this character
        # Sound Designer needs to update voice synthesis
        # Editor needs to reassemble affected scenes
        
        character_name = character_obj.movie_director.character_name
        print(f"Character {character_name} changed - notifying dependent agents")
        
        # Mark affected shots for regeneration
        self.mark_character_shots_for_update(character_name)
```

### Dynamic UI Updates
```python
class DynamicUIManager:
    """Manage dynamic UI updates based on data changes"""
    
    def __init__(self):
        self.owner = object()
        self.ui_state = {}
        self.setup_ui_subscriptions()
    
    def setup_ui_subscriptions(self):
        """Set up subscriptions for UI-relevant changes"""
        # Subscribe to active object changes
        subscribe_rna(
            key=bpy.context.view_layer,
            owner=self.owner,
            notify=self.on_selection_change
        )
        
        # Subscribe to mode changes
        subscribe_rna(
            key=bpy.context,
            owner=self.owner,
            notify=self.on_mode_change
        )
    
    def on_selection_change(self):
        """Handle active object selection changes"""
        active_obj = bpy.context.active_object
        
        # Update panel visibility based on selected object
        if active_obj and hasattr(active_obj, 'movie_director'):
            asset_type = active_obj.movie_director.asset_type
            self.show_asset_panels(asset_type)
        else:
            self.show_default_panels()
        
        # Force UI redraw
        self.redraw_ui_areas(['VIEW_3D', 'PROPERTIES'])
    
    def on_mode_change(self):
        """Handle mode changes that affect UI"""
        current_mode = bpy.context.mode
        
        # Show/hide panels based on mode
        if current_mode == 'OBJECT':
            self.enable_generation_ui()
        else:
            self.disable_generation_ui()
    
    def redraw_ui_areas(self, area_types):
        """Force redraw of specific UI areas"""
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type in area_types:
                    area.tag_redraw()
```

## Integration with Addon Lifecycle

### Message Bus Setup and Cleanup
```python
class MovieDirectorMessageBus:
    """Main message bus manager for Movie Director addon"""
    
    def __init__(self):
        self.managers = []
        self.setup_message_bus()
    
    def setup_message_bus(self):
        """Initialize all message bus managers"""
        self.asset_manager = AssetChangeManager()
        self.progress_monitor = GenerationProgressMonitor()
        self.workflow_manager = WorkflowStateManager()
        self.ui_manager = DynamicUIManager()
        
        self.managers = [
            self.asset_manager,
            self.progress_monitor,
            self.workflow_manager,
            self.ui_manager
        ]
    
    def cleanup_message_bus(self):
        """Clean up all message bus subscriptions"""
        for manager in self.managers:
            if hasattr(manager, 'cleanup_subscriptions'):
                manager.cleanup_subscriptions()
            elif hasattr(manager, 'owner'):
                clear_by_owner(manager.owner)

# Global message bus instance
message_bus_manager = None

def register():
    """Register addon and set up message bus"""
    global message_bus_manager
    
    # Register classes first
    register_classes(CLASSES)
    
    # Set up message bus
    message_bus_manager = MovieDirectorMessageBus()

def unregister():
    """Unregister addon and clean up message bus"""
    global message_bus_manager
    
    # Clean up message bus first
    if message_bus_manager:
        message_bus_manager.cleanup_message_bus()
        message_bus_manager = None
    
    # Unregister classes
    unregister_classes(CLASSES)
```

## Best Practices

### 1. Always Clean Up Subscriptions
```python
# GOOD: Proper cleanup with owner
class MyManager:
    def __init__(self):
        self.owner = object()
        
    def setup_subscriptions(self):
        subscribe_rna(key=..., owner=self.owner, notify=...)
    
    def cleanup(self):
        clear_by_owner(self.owner)

# AVOID: No cleanup (causes memory leaks)
def bad_subscription():
    subscribe_rna(key=..., owner=None, notify=...)  # Never cleaned up!
```

### 2. Use Lightweight Callbacks
```python
# GOOD: Lightweight callback
def on_property_change():
    # Quick update
    update_ui_flag = True

# AVOID: Heavy operations in callbacks
def bad_callback():
    regenerate_all_assets()  # Too expensive!
    recalculate_entire_scene()  # Blocks UI!
```

### 3. Handle Callback Errors Gracefully
```python
# GOOD: Error handling in callbacks
def safe_callback():
    try:
        perform_update()
    except Exception as e:
        print(f"Error in message bus callback: {e}")

# AVOID: Unhandled exceptions
def unsafe_callback():
    risky_operation()  # May crash if it fails
```

### 4. Use Specific Subscription Keys
```python
# GOOD: Specific property subscription
subscribe_rna(
    key=(bpy.types.Scene, "movie_director", "generation_progress"),
    owner=owner,
    notify=callback
)

# AVOID: Overly broad subscriptions
subscribe_rna(
    key=bpy.types.Scene,  # Too broad - triggers on any scene change
    owner=owner,
    notify=callback
)
```

This message bus guide enables reactive and responsive behavior in the Movie Director addon, ensuring that UI updates, agent coordination, and workflow state management happen automatically in response to data changes.