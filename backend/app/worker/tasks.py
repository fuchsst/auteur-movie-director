"""
Celery Tasks for Function Runner Workers

Defines tasks that can be executed by different worker types with proper
resource allocation and progress tracking.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from celery import current_task
from celery.exceptions import Retry

from app.worker.celery_config import app
from app.redis_client import redis_client

logger = logging.getLogger(__name__)


class TaskProgressReporter:
    """Helper class for reporting task progress"""
    
    def __init__(self, task_id: str, project_id: Optional[str] = None):
        self.task_id = task_id
        self.project_id = project_id
    
    async def report(self, progress: float, message: str, **kwargs):
        """Report task progress"""
        progress_data = {
            'task_id': self.task_id,
            'progress': progress,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        }
        
        if self.project_id:
            await redis_client.publish_progress(
                self.project_id, 
                self.task_id, 
                progress_data
            )
        
        # Also publish to task-specific channel
        channel = f"task:progress:{self.task_id}"
        await redis_client.publish(channel, json.dumps(progress_data))


@app.task(bind=True, name='function_runner.execute_generation')
def execute_generation(self, task_payload: Dict[str, Any]):
    """
    Execute AI generation task with progress reporting
    
    This task handles the complete generation pipeline:
    1. Resource allocation and validation
    2. Pipeline initialization
    3. Generation execution
    4. Output processing and storage
    5. Cleanup and result reporting
    """
    task_id = self.request.id
    pipeline_id = task_payload.get('pipeline_id', 'unknown')
    node_type = task_payload.get('node_type', 'unknown')
    parameters = task_payload.get('parameters', {})
    config = task_payload.get('config', {})
    
    # Extract context information
    node_id = parameters.get('node_id', 'unknown')
    project_id = parameters.get('project_id', 'unknown')
    output_path = parameters.get('output_path', '/workspace/outputs')
    
    logger.info(f"Starting generation task {task_id} for {node_type} using {pipeline_id}")
    
    # Create progress reporter
    async def report_progress(progress: float, message: str, status: str = "running", **kwargs):
        reporter = TaskProgressReporter(task_id, project_id)
        await reporter.report(
            progress=progress,
            message=message,
            status=status,
            node_id=node_id,
            pipeline_id=pipeline_id,
            **kwargs
        )
    
    try:
        # Generation pipeline stages
        stages = [
            (5, "Validating task parameters"),
            (10, "Allocating computational resources"),
            (15, "Loading model configuration"),
            (20, "Preparing workspace environment"),
            (25, "Initializing generation pipeline"),
            (30, "Loading model weights"),
            (40, "Processing input parameters"),
            (50, "Executing generation algorithm"),
            (70, "Post-processing outputs"),
            (85, "Saving results to workspace"),
            (95, "Cleaning up resources"),
        ]
        
        # Execute stages with progress reporting
        for progress, message in stages:
            asyncio.run(report_progress(progress, message))
            
            # Simulate processing time based on stage
            if "generation algorithm" in message.lower():
                # Main generation takes longer
                time.sleep(2.0)
            elif "loading model" in message.lower():
                # Model loading takes some time
                time.sleep(1.0)
            else:
                # Other stages are quick
                time.sleep(0.3)
        
        # Create output directory
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate result based on node type
        result_data = _generate_mock_result(
            task_id=task_id,
            node_id=node_id,
            node_type=node_type,
            pipeline_id=pipeline_id,
            parameters=parameters,
            config=config,
            output_dir=output_dir
        )
        
        # Save result metadata
        result_file = output_dir / f"{node_id}_metadata.json"
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        # Report successful completion
        asyncio.run(report_progress(
            100, 
            "Generation completed successfully", 
            status="completed",
            result=result_data
        ))
        
        logger.info(f"Generation task {task_id} completed successfully")
        return result_data
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Generation task {task_id} failed: {error_msg}")
        
        # Report failure
        asyncio.run(report_progress(
            0, 
            f"Generation failed: {error_msg}", 
            status="failed",
            error=error_msg
        ))
        
        raise


@app.task(bind=True, name='function_runner.process_file')
def process_file(self, file_path: str, operation: str, **kwargs):
    """
    Process file with specified operation
    
    Suitable for CPU workers handling file processing tasks.
    """
    task_id = self.request.id
    
    logger.info(f"Processing file {file_path} with operation {operation}")
    
    try:
        # Simulate file processing
        time.sleep(1.0)
        
        result = {
            'task_id': task_id,
            'file_path': file_path,
            'operation': operation,
            'processed_at': datetime.utcnow().isoformat(),
            'status': 'completed'
        }
        
        logger.info(f"File processing task {task_id} completed")
        return result
        
    except Exception as e:
        logger.error(f"File processing task {task_id} failed: {e}")
        raise


@app.task(bind=True, name='function_runner.upload_file')
def upload_file(self, source_path: str, destination: str, **kwargs):
    """
    Upload file to destination
    
    Suitable for I/O workers handling file operations.
    """
    task_id = self.request.id
    
    logger.info(f"Uploading file from {source_path} to {destination}")
    
    try:
        # Simulate file upload
        time.sleep(0.5)
        
        result = {
            'task_id': task_id,
            'source_path': source_path,
            'destination': destination,
            'uploaded_at': datetime.utcnow().isoformat(),
            'status': 'completed'
        }
        
        logger.info(f"File upload task {task_id} completed")
        return result
        
    except Exception as e:
        logger.error(f"File upload task {task_id} failed: {e}")
        raise


@app.task(bind=True, name='function_runner.health_check')
def health_check(self):
    """
    Worker health check task
    
    Can be executed by any worker type for monitoring.
    """
    import psutil
    
    task_id = self.request.id
    worker_hostname = self.request.hostname
    
    try:
        # Collect system metrics
        metrics = {
            'task_id': task_id,
            'worker_hostname': worker_hostname,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'healthy',
            'system': {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            }
        }
        
        logger.debug(f"Health check completed for worker {worker_hostname}")
        return metrics
        
    except Exception as e:
        logger.error(f"Health check failed for worker {worker_hostname}: {e}")
        return {
            'task_id': task_id,
            'worker_hostname': worker_hostname,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'unhealthy',
            'error': str(e)
        }


@app.task(bind=True, name='function_runner.benchmark_worker')
def benchmark_worker(self, duration: int = 10):
    """
    Benchmark worker performance
    
    Useful for worker capacity planning and performance monitoring.
    """
    task_id = self.request.id
    worker_hostname = self.request.hostname
    
    logger.info(f"Starting {duration}s benchmark on worker {worker_hostname}")
    
    try:
        import psutil
        
        start_time = time.time()
        
        # CPU benchmark
        cpu_scores = []
        memory_usage = []
        
        while time.time() - start_time < duration:
            # Simple CPU workload
            result = sum(i * i for i in range(10000))
            cpu_scores.append(result)
            
            # Monitor memory
            memory_usage.append(psutil.virtual_memory().percent)
            
            time.sleep(0.1)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        benchmark_result = {
            'task_id': task_id,
            'worker_hostname': worker_hostname,
            'duration': actual_duration,
            'cpu_operations': len(cpu_scores),
            'operations_per_second': len(cpu_scores) / actual_duration,
            'avg_memory_usage': sum(memory_usage) / len(memory_usage),
            'max_memory_usage': max(memory_usage),
            'completed_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Benchmark completed on worker {worker_hostname}: {benchmark_result['operations_per_second']:.2f} ops/sec")
        return benchmark_result
        
    except Exception as e:
        logger.error(f"Benchmark failed on worker {worker_hostname}: {e}")
        raise


def _generate_mock_result(
    task_id: str,
    node_id: str,
    node_type: str,
    pipeline_id: str,
    parameters: Dict[str, Any],
    config: Dict[str, Any],
    output_dir: Path
) -> Dict[str, Any]:
    """Generate mock result data based on node type"""
    
    base_result = {
        'task_id': task_id,
        'node_id': node_id,
        'node_type': node_type,
        'pipeline_id': pipeline_id,
        'generated_at': datetime.utcnow().isoformat(),
        'parameters': parameters,
        'config': config
    }
    
    if node_type == 'image_generation':
        # Create mock image output
        image_file = output_dir / f"{node_id}_generated.png"
        image_file.write_text("Mock PNG image data")
        
        base_result.update({
            'outputs': {
                'image': {
                    'path': str(image_file),
                    'format': 'PNG',
                    'width': parameters.get('width', 1024),
                    'height': parameters.get('height', 1024),
                    'size_bytes': len("Mock PNG image data")
                }
            },
            'metadata': {
                'generation_time': 5.2,
                'model_version': '1.0.0',
                'seed': parameters.get('seed', 42),
                'steps': config.get('steps', 30)
            }
        })
        
    elif node_type == 'video_generation':
        # Create mock video output
        video_file = output_dir / f"{node_id}_generated.mp4"
        video_file.write_text("Mock MP4 video data")
        
        base_result.update({
            'outputs': {
                'video': {
                    'path': str(video_file),
                    'format': 'MP4',
                    'duration': parameters.get('duration', 10.0),
                    'fps': parameters.get('fps', 24),
                    'resolution': f"{parameters.get('width', 1920)}x{parameters.get('height', 1080)}",
                    'size_bytes': len("Mock MP4 video data")
                }
            },
            'metadata': {
                'generation_time': 45.8,
                'model_version': '1.0.0',
                'frames_generated': int(parameters.get('duration', 10.0) * parameters.get('fps', 24))
            }
        })
        
    elif node_type == 'audio_generation':
        # Create mock audio output
        audio_file = output_dir / f"{node_id}_generated.wav"
        audio_file.write_text("Mock WAV audio data")
        
        base_result.update({
            'outputs': {
                'audio': {
                    'path': str(audio_file),
                    'format': 'WAV',
                    'duration': parameters.get('duration', 30.0),
                    'sample_rate': parameters.get('sample_rate', 44100),
                    'channels': parameters.get('channels', 2),
                    'size_bytes': len("Mock WAV audio data")
                }
            },
            'metadata': {
                'generation_time': 12.3,
                'model_version': '1.0.0',
                'quality': config.get('quality', 'standard')
            }
        })
        
    else:
        # Generic output
        output_file = output_dir / f"{node_id}_output.txt"
        output_file.write_text("Mock output data")
        
        base_result.update({
            'outputs': {
                'result': {
                    'path': str(output_file),
                    'size_bytes': len("Mock output data")
                }
            },
            'metadata': {
                'generation_time': 2.1,
                'model_version': '1.0.0'
            }
        })
    
    return base_result


# Task registration for monitoring
@app.task(bind=True, name='function_runner.register_task_types')
def register_task_types(self):
    """Register available task types for monitoring"""
    task_types = {
        'generation_tasks': [
            'function_runner.execute_generation'
        ],
        'processing_tasks': [
            'function_runner.process_file'
        ],
        'io_tasks': [
            'function_runner.upload_file'
        ],
        'monitoring_tasks': [
            'function_runner.health_check',
            'function_runner.benchmark_worker'
        ]
    }
    
    return {
        'registered_at': datetime.utcnow().isoformat(),
        'task_types': task_types,
        'worker_hostname': self.request.hostname
    }