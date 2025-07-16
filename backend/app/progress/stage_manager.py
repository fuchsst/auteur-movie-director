"""Stage management for different function types"""

from typing import List, Dict, Optional
from .models import Stage, StageProgress, StageStatus


class StageManager:
    """Manages execution stages for different function types"""
    
    # Default stages for different function categories
    STAGE_DEFINITIONS = {
        'image_generation': [
            Stage('queue', 'Waiting in queue', weight=0.05),
            Stage('model_loading', 'Loading models', weight=0.15),
            Stage('generation', 'Generating image', weight=0.70),
            Stage('post_processing', 'Post-processing', weight=0.10)
        ],
        'video_generation': [
            Stage('queue', 'Waiting in queue', weight=0.02),
            Stage('model_loading', 'Loading models', weight=0.08),
            Stage('frame_generation', 'Generating frames', weight=0.80),
            Stage('video_encoding', 'Encoding video', weight=0.10)
        ],
        'audio_generation': [
            Stage('queue', 'Waiting in queue', weight=0.05),
            Stage('text_processing', 'Processing text', weight=0.10),
            Stage('synthesis', 'Synthesizing audio', weight=0.75),
            Stage('normalization', 'Normalizing audio', weight=0.10)
        ],
        'text_generation': [
            Stage('queue', 'Waiting in queue', weight=0.05),
            Stage('context_loading', 'Loading context', weight=0.10),
            Stage('generation', 'Generating text', weight=0.80),
            Stage('formatting', 'Formatting output', weight=0.05)
        ],
        'default': [
            Stage('queue', 'Waiting in queue', weight=0.05),
            Stage('preparation', 'Preparing execution', weight=0.15),
            Stage('execution', 'Processing', weight=0.70),
            Stage('finalization', 'Finalizing results', weight=0.10)
        ]
    }
    
    # Custom stage definitions per template
    TEMPLATE_STAGES: Dict[str, List[Stage]] = {}
    
    @classmethod
    def register_template_stages(cls, template_id: str, stages: List[Stage]):
        """Register custom stages for a specific template"""
        cls.TEMPLATE_STAGES[template_id] = stages
    
    @classmethod
    def get_stages_for_template(cls, template_id: str, category: str = 'default') -> List[Stage]:
        """Get stage definitions for a template"""
        # Check for custom template stages first
        if template_id in cls.TEMPLATE_STAGES:
            return cls.TEMPLATE_STAGES[template_id]
        
        # Fall back to category stages
        return cls.STAGE_DEFINITIONS.get(category, cls.STAGE_DEFINITIONS['default'])
    
    @classmethod
    def create_stage_progress(cls, stages: List[Stage]) -> Dict[int, StageProgress]:
        """Create initial stage progress objects"""
        stage_progress = {}
        
        for i, stage in enumerate(stages):
            stage_progress[i] = StageProgress(
                name=stage.name,
                status=StageStatus.PENDING,
                metadata={'description': stage.description, 'weight': stage.weight}
            )
        
        return stage_progress
    
    @classmethod
    def calculate_stage_weights(cls, stages: List[Stage]) -> Dict[int, float]:
        """Calculate normalized stage weights"""
        total_weight = sum(stage.weight for stage in stages)
        
        if total_weight == 0:
            # Equal weights if none specified
            weight = 1.0 / len(stages)
            return {i: weight for i in range(len(stages))}
        
        # Normalize weights
        return {
            i: stage.weight / total_weight 
            for i, stage in enumerate(stages)
        }
    
    @classmethod
    def get_stage_by_name(cls, stages: List[Stage], name: str) -> Optional[int]:
        """Find stage index by name"""
        for i, stage in enumerate(stages):
            if stage.name == name:
                return i
        return None
    
    @classmethod
    def should_skip_stage(cls, stage: Stage, context: Dict[str, any]) -> bool:
        """Determine if a stage should be skipped based on context"""
        # Optional stages can be skipped
        if stage.optional and context.get('skip_optional', False):
            return True
        
        # Check stage-specific skip conditions
        skip_conditions = {
            'post_processing': lambda ctx: ctx.get('skip_post_processing', False),
            'normalization': lambda ctx: ctx.get('skip_normalization', False),
            'formatting': lambda ctx: ctx.get('raw_output', False)
        }
        
        if stage.name in skip_conditions:
            return skip_conditions[stage.name](context)
        
        return False