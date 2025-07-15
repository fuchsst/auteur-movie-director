"""
GPU resource management for efficient device allocation
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from .models import GPUDevice, GPUAllocation, ResourceSpec
from .exceptions import InsufficientResourcesError

logger = logging.getLogger(__name__)


class GPUResourceManager:
    """Manages GPU device allocation"""
    
    def __init__(self):
        """Initialize GPU resource manager"""
        self.devices: List[GPUDevice] = []
        self.allocations: Dict[int, GPUAllocation] = {}
        self._lock = asyncio.Lock()
        self._monitor_task = None
        self._nvml_available = False
        self._init_nvml()
        
    def _init_nvml(self):
        """Initialize NVIDIA Management Library"""
        try:
            import pynvml
            pynvml.nvmlInit()
            self._nvml_available = True
            logger.info("NVML initialized successfully")
        except ImportError:
            logger.warning("pynvml not available - GPU monitoring disabled")
        except Exception as e:
            logger.warning(f"Failed to initialize NVML: {e}")
    
    async def start(self):
        """Start GPU monitoring"""
        await self._discover_devices()
        if self._nvml_available and not self._monitor_task:
            self._monitor_task = asyncio.create_task(self._monitor_devices())
    
    async def stop(self):
        """Stop GPU monitoring"""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _discover_devices(self) -> List[GPUDevice]:
        """Discover available GPU devices"""
        devices = []
        
        if not self._nvml_available:
            return devices
        
        try:
            import pynvml
            
            device_count = pynvml.nvmlDeviceGetCount()
            for i in range(device_count):
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    
                    # Get device info
                    name = pynvml.nvmlDeviceGetName(handle).decode()
                    memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    compute_capability = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
                    
                    # Get utilization
                    try:
                        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                        gpu_util = util.gpu
                    except:
                        gpu_util = 0.0
                    
                    # Get temperature
                    try:
                        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    except:
                        temp = None
                    
                    # Get power draw
                    try:
                        power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
                    except:
                        power = None
                    
                    device = GPUDevice(
                        index=i,
                        name=name,
                        memory_total_gb=memory.total / (1024**3),
                        memory_free_gb=memory.free / (1024**3),
                        compute_capability=f"{compute_capability[0]}.{compute_capability[1]}",
                        utilization_percent=gpu_util,
                        temperature_c=temp,
                        power_draw_w=power
                    )
                    
                    devices.append(device)
                    logger.info(f"Discovered GPU {i}: {name} ({device.memory_total_gb:.1f}GB, compute {device.compute_capability})")
                    
                except Exception as e:
                    logger.error(f"Failed to get info for GPU {i}: {e}")
                    
        except Exception as e:
            logger.error(f"GPU discovery failed: {e}")
        
        async with self._lock:
            self.devices = devices
        
        return devices
    
    async def allocate_gpu(self, 
                          memory_gb: float,
                          compute_capability: Optional[str] = None,
                          preferred_device: Optional[int] = None) -> Optional[int]:
        """
        Allocate GPU device for task.
        
        Args:
            memory_gb: Required GPU memory in GB
            compute_capability: Minimum compute capability required
            preferred_device: Preferred device index
            
        Returns:
            Device index if allocated, None if no suitable device
        """
        async with self._lock:
            # Check preferred device first
            if preferred_device is not None:
                if await self._try_allocate_device(preferred_device, memory_gb, compute_capability):
                    return preferred_device
            
            # Find suitable device
            candidates = []
            for device in self.devices:
                # Get allocated memory
                allocated = self.allocations.get(device.index, GPUAllocation(
                    device_index=device.index,
                    memory_gb=0
                )).memory_gb
                
                free_memory = device.memory_total_gb - allocated
                
                # Check requirements
                if free_memory < memory_gb:
                    continue
                
                if compute_capability and device.compute_capability < compute_capability:
                    continue
                
                # Score device (prefer less utilized)
                score = free_memory / device.memory_total_gb
                candidates.append((score, device.index))
            
            # Sort by score (higher is better)
            candidates.sort(reverse=True)
            
            # Try to allocate on best candidate
            for _, device_index in candidates:
                if await self._try_allocate_device(device_index, memory_gb, compute_capability):
                    return device_index
            
            return None
    
    async def _try_allocate_device(self,
                                  device_index: int,
                                  memory_gb: float,
                                  compute_capability: Optional[str]) -> bool:
        """Try to allocate on specific device"""
        if device_index >= len(self.devices):
            return False
        
        device = self.devices[device_index]
        
        # Check compute capability
        if compute_capability and device.compute_capability < compute_capability:
            return False
        
        # Check available memory
        if device_index in self.allocations:
            allocated = self.allocations[device_index].memory_gb
            free = device.memory_total_gb - allocated
        else:
            free = device.memory_total_gb
        
        if free < memory_gb:
            return False
        
        # Allocate
        if device_index not in self.allocations:
            self.allocations[device_index] = GPUAllocation(
                device_index=device_index,
                memory_gb=memory_gb
            )
        else:
            self.allocations[device_index].memory_gb += memory_gb
        
        logger.info(f"Allocated {memory_gb:.1f}GB on GPU {device_index}")
        return True
    
    async def allocate_multi_gpu(self,
                               count: int,
                               memory_per_gpu_gb: float,
                               compute_capability: Optional[str] = None) -> Optional[List[int]]:
        """
        Allocate multiple GPU devices.
        
        Args:
            count: Number of GPUs needed
            memory_per_gpu_gb: Memory required per GPU
            compute_capability: Minimum compute capability
            
        Returns:
            List of device indices if allocated, None if not enough devices
        """
        async with self._lock:
            allocated_devices = []
            
            # Try to allocate requested number of devices
            for _ in range(count):
                device_index = await self.allocate_gpu(
                    memory_gb=memory_per_gpu_gb,
                    compute_capability=compute_capability
                )
                
                if device_index is None:
                    # Rollback allocations
                    for idx in allocated_devices:
                        await self.release_gpu(idx, memory_per_gpu_gb)
                    return None
                
                allocated_devices.append(device_index)
            
            return allocated_devices
    
    async def release_gpu(self, device_index: int, memory_gb: float):
        """Release GPU allocation"""
        async with self._lock:
            if device_index in self.allocations:
                self.allocations[device_index].memory_gb -= memory_gb
                
                if self.allocations[device_index].memory_gb <= 0:
                    del self.allocations[device_index]
                
                logger.info(f"Released {memory_gb:.1f}GB on GPU {device_index}")
    
    async def release_task_gpus(self, task_id: str):
        """Release all GPU allocations for a task"""
        async with self._lock:
            for device_index, allocation in list(self.allocations.items()):
                if task_id in allocation.tasks:
                    allocation.tasks.remove(task_id)
                    # Note: This simplified version doesn't track memory per task
                    # In production, would need task->memory mapping
    
    async def get_gpu_status(self) -> Dict[str, Any]:
        """Get current GPU status"""
        async with self._lock:
            device_statuses = []
            
            for device in self.devices:
                allocated = self.allocations.get(device.index, GPUAllocation(
                    device_index=device.index,
                    memory_gb=0
                )).memory_gb
                
                device_statuses.append({
                    "index": device.index,
                    "name": device.name,
                    "compute_capability": device.compute_capability,
                    "memory_total_gb": device.memory_total_gb,
                    "memory_allocated_gb": allocated,
                    "memory_free_gb": device.memory_total_gb - allocated,
                    "utilization_percent": device.utilization_percent,
                    "temperature_c": device.temperature_c,
                    "power_draw_w": device.power_draw_w,
                    "allocation_percent": (allocated / device.memory_total_gb * 100) if device.memory_total_gb > 0 else 0
                })
            
            total_memory = sum(d.memory_total_gb for d in self.devices)
            total_allocated = sum(self.allocations.get(d.index, GPUAllocation(device_index=d.index, memory_gb=0)).memory_gb for d in self.devices)
            
            return {
                "devices": device_statuses,
                "summary": {
                    "device_count": len(self.devices),
                    "total_memory_gb": total_memory,
                    "allocated_memory_gb": total_allocated,
                    "free_memory_gb": total_memory - total_allocated,
                    "allocation_percent": (total_allocated / total_memory * 100) if total_memory > 0 else 0
                }
            }
    
    def estimate_gpu_requirements(self, resource_spec: ResourceSpec) -> Tuple[int, float]:
        """
        Estimate GPU requirements from resource specification.
        
        Args:
            resource_spec: Resource requirements
            
        Returns:
            Tuple of (gpu_count, memory_per_gpu_gb)
        """
        if resource_spec.gpu_count == 0:
            return (0, 0)
        
        # Calculate memory per GPU
        memory_per_gpu = resource_spec.gpu_memory_gb / max(1, resource_spec.gpu_count)
        
        return (resource_spec.gpu_count, memory_per_gpu)
    
    async def _monitor_devices(self):
        """Monitor GPU devices for changes"""
        while True:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                if not self._nvml_available:
                    continue
                
                import pynvml
                
                async with self._lock:
                    for device in self.devices:
                        try:
                            handle = pynvml.nvmlDeviceGetHandleByIndex(device.index)
                            
                            # Update memory info
                            memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
                            device.memory_free_gb = memory.free / (1024**3)
                            
                            # Update utilization
                            try:
                                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                                device.utilization_percent = util.gpu
                            except:
                                pass
                            
                            # Update temperature
                            try:
                                device.temperature_c = pynvml.nvmlDeviceGetTemperature(
                                    handle, pynvml.NVML_TEMPERATURE_GPU
                                )
                            except:
                                pass
                            
                            # Update power
                            try:
                                device.power_draw_w = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
                            except:
                                pass
                                
                        except Exception as e:
                            logger.error(f"Failed to update GPU {device.index} status: {e}")
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in GPU monitor: {e}")
                await asyncio.sleep(60)  # Back off on error