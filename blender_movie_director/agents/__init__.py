"""
AI Film Crew Agents

BMAD-architected agent system implementing specialized film crew roles.
Each agent represents a familiar production role and collaborates via CrewAI.
"""

from . import (
    art_director,
    casting_director,
    cinematographer,
    editor,
    producer,
    screenwriter,
    sound_designer,
)


def register():
    """Register all agent modules"""
    producer.register()
    screenwriter.register()
    casting_director.register()
    art_director.register()
    cinematographer.register()
    sound_designer.register()
    editor.register()

    print("BMAD Film Crew Agents registered")


def unregister():
    """Unregister all agent modules"""
    editor.unregister()
    sound_designer.unregister()
    cinematographer.unregister()
    art_director.unregister()
    casting_director.unregister()
    screenwriter.unregister()
    producer.unregister()

    print("BMAD Film Crew Agents unregistered")
