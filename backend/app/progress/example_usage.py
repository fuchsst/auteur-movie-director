"""Example usage of progress tracking system"""

import asyncio
from typing import Dict, Any

from app.progress.tracker import ProgressTracker
from app.progress.integration import ProgressContext, create_progress_callback
from app.core.dependencies import get_progress_tracker


async def example_image_generation_task(task_id: str, params: Dict[str, Any]):
    """Example of using progress tracking with an image generation task"""
    
    # Get progress tracker
    tracker = await get_progress_tracker()
    
    # Use context manager for automatic progress tracking
    async with ProgressContext(
        tracker, 
        task_id, 
        template_id="stable-diffusion-xl",
        template_category="image_generation"
    ) as ctx:
        
        # Get callback for function runner
        progress_callback = ctx.get_callback()
        
        # Simulate task execution with progress updates
        
        # Queue stage
        await progress_callback('queue_position', {'position': 2, 'queue_size': 3})
        await asyncio.sleep(1)
        await progress_callback('queue_position', {'position': 1, 'queue_size': 3})
        await asyncio.sleep(1)
        await progress_callback('queue_position', {'position': 0, 'queue_size': 3})
        
        # Model loading
        for i in range(10):
            await progress_callback('model_loading', {
                'model_name': 'stable-diffusion-xl',
                'progress': (i + 1) / 10
            })
            await asyncio.sleep(0.1)
        
        # Main execution
        total_steps = params.get('steps', 30)
        for step in range(total_steps):
            # Generate preview at certain intervals
            preview_path = None
            if step in [7, 15, 22]:  # ~25%, 50%, 75%
                preview_path = f"/tmp/preview_{task_id}_{step}.png"
            
            await progress_callback('execution_progress', {
                'step': step + 1,
                'total_steps': total_steps,
                'preview_path': preview_path
            })
            
            # Simulate resource usage
            if step % 5 == 0:
                await progress_callback('resource_usage', {
                    'cpu_percent': 45.0 + step,
                    'memory_mb': 2048 + step * 10,
                    'gpu_percent': 85.0 + step / 2,
                    'gpu_memory_mb': 4096 + step * 20
                })
            
            await asyncio.sleep(0.2)
        
        # Post-processing
        operations = ['upscaling', 'color_correction', 'saving']
        for i, op in enumerate(operations):
            await progress_callback('post_processing', {
                'operation': op,
                'progress': (i + 1) / len(operations)
            })
            await asyncio.sleep(0.5)
        
        # Complete
        output_path = f"/workspace/renders/{task_id}/output.png"
        await progress_callback('complete', {'output_path': output_path})
        
        return output_path


async def example_batch_progress():
    """Example of tracking batch progress"""
    
    tracker = await get_progress_tracker()
    
    # Create multiple tasks
    batch_id = "batch-001"
    task_ids = []
    
    for i in range(5):
        task_id = f"batch-task-{i}"
        task_ids.append(task_id)
        
        # Start tasks concurrently
        asyncio.create_task(
            example_image_generation_task(
                task_id, 
                {'steps': 20 + i * 5}  # Vary steps
            )
        )
    
    # Monitor batch progress
    for _ in range(30):
        batch_progress = await tracker.get_batch_progress(batch_id, task_ids)
        
        print(f"Batch Progress: {batch_progress.overall_progress:.1f}%")
        print(f"Completed: {batch_progress.completed_tasks}/{batch_progress.total_tasks}")
        
        if batch_progress.completed_tasks == batch_progress.total_tasks:
            break
        
        await asyncio.sleep(1)


async def example_progress_subscription(task_id: str):
    """Example of subscribing to progress updates via WebSocket"""
    
    # This would typically be done from the frontend
    # Here's a pseudo-example of the WebSocket messages
    
    # Subscribe to task progress
    subscribe_msg = {
        'type': 'subscribe',
        'task_ids': [task_id]
    }
    
    # Would receive updates like:
    # {
    #     'type': 'progress.update',
    #     'task_id': 'task-123',
    #     'data': {
    #         'status': 'executing',
    #         'current_stage': 2,
    #         'overall_progress': 45.5,
    #         'eta': '2024-01-15T10:30:00',
    #         'stages': {...},
    #         'preview_url': '/api/v1/previews/preview_123.png'
    #     }
    # }


if __name__ == "__main__":
    # Example usage
    asyncio.run(example_image_generation_task("test-task-001", {'steps': 30}))