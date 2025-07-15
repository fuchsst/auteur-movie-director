"""
Resource mapper for allocating tasks to workers based on resource requirements
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from .models import (
    ResourceSpec,
    WorkerResources,
    ResourceAllocation,
    ResourceReservation,
    ResourceConstraints,
    AllocationStrategy
)
from .exceptions import InsufficientResourcesError, ResourceConflictError

logger = logging.getLogger(__name__)


class ResourceMapper:
    """Maps function requirements to worker resources"""
    
    def __init__(self, strategy: AllocationStrategy = AllocationStrategy.LOAD_BALANCE):
        """
        Initialize resource mapper.
        
        Args:
            strategy: Default allocation strategy
        """
        self.workers: Dict[str, WorkerResources] = {}
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.reservations: Dict[str, ResourceReservation] = {}
        self.strategy = strategy
        self._lock = asyncio.Lock()
        self._cleanup_task = None
        
    async def start(self):
        """Start the resource mapper"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())
    
    async def stop(self):
        """Stop the resource mapper"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def register_worker(self, worker_id: str, resources: ResourceSpec):
        """Register a worker with its available resources"""
        async with self._lock:
            self.workers[worker_id] = WorkerResources(
                worker_id=worker_id,
                total=resources
            )
            logger.info(f"Registered worker {worker_id} with resources: {resources}")
    
    async def unregister_worker(self, worker_id: str):
        """Unregister a worker"""
        async with self._lock:
            if worker_id in self.workers:
                # Check for active allocations
                active_allocations = [
                    alloc_id for alloc_id, alloc in self.allocations.items()
                    if alloc.worker_id == worker_id
                ]
                
                if active_allocations:
                    raise ResourceConflictError(
                        f"Cannot unregister worker {worker_id} with active allocations: {active_allocations}"
                    )
                
                del self.workers[worker_id]
                logger.info(f"Unregistered worker {worker_id}")
    
    async def find_worker(self, 
                         requirements: ResourceSpec,
                         constraints: Optional[ResourceConstraints] = None,
                         strategy: Optional[AllocationStrategy] = None) -> Optional[str]:
        """
        Find suitable worker for requirements.
        
        Args:
            requirements: Resource requirements
            constraints: Optional allocation constraints
            strategy: Override default allocation strategy
            
        Returns:
            Worker ID if found, None otherwise
        """
        async with self._lock:
            # Get candidate workers
            candidates = self._get_candidates(requirements, constraints)
            
            if not candidates:
                logger.warning(f"No candidates found for requirements: {requirements}")
                return None
            
            # Apply allocation strategy
            use_strategy = strategy or self.strategy
            selected = self._select_worker(candidates, requirements, use_strategy)
            
            if selected:
                logger.info(f"Selected worker {selected} for requirements: {requirements}")
            
            return selected
    
    async def reserve_resources(self,
                               worker_id: str,
                               requirements: ResourceSpec,
                               duration_seconds: int = 300,
                               priority: int = 0) -> str:
        """
        Reserve resources on a worker.
        
        Args:
            worker_id: Worker to reserve on
            requirements: Resources to reserve
            duration_seconds: Reservation duration
            priority: Reservation priority
            
        Returns:
            Reservation ID
        """
        async with self._lock:
            if worker_id not in self.workers:
                raise ValueError(f"Unknown worker: {worker_id}")
            
            worker = self.workers[worker_id]
            if not worker.can_allocate(requirements):
                raise InsufficientResourcesError(
                    f"Worker {worker_id} cannot fulfill requirements: {requirements}"
                )
            
            # Create reservation
            reservation_id = str(uuid.uuid4())
            reservation = ResourceReservation(
                id=reservation_id,
                worker_id=worker_id,
                resources=requirements,
                reserved_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=duration_seconds),
                priority=priority
            )
            
            # Update worker reserved resources
            worker.reserved = worker.reserved + requirements
            self.reservations[reservation_id] = reservation
            
            logger.info(f"Created reservation {reservation_id} on worker {worker_id}")
            return reservation_id
    
    async def allocate(self,
                      worker_id: str,
                      requirements: ResourceSpec,
                      task_id: str,
                      reservation_id: Optional[str] = None,
                      duration_estimate: Optional[int] = None) -> ResourceAllocation:
        """
        Allocate resources on a worker.
        
        Args:
            worker_id: Worker to allocate on
            requirements: Resources to allocate
            task_id: Task requesting allocation
            reservation_id: Optional reservation to convert
            duration_estimate: Estimated duration in seconds
            
        Returns:
            Resource allocation
        """
        async with self._lock:
            if worker_id not in self.workers:
                raise ValueError(f"Unknown worker: {worker_id}")
            
            worker = self.workers[worker_id]
            
            # If using reservation, verify and remove it
            if reservation_id:
                if reservation_id not in self.reservations:
                    raise ValueError(f"Unknown reservation: {reservation_id}")
                
                reservation = self.reservations[reservation_id]
                if reservation.worker_id != worker_id:
                    raise ValueError(f"Reservation {reservation_id} is for different worker")
                
                # Remove reservation
                worker.reserved = worker.reserved - reservation.resources
                del self.reservations[reservation_id]
            
            # Check availability
            if not worker.can_allocate(requirements):
                raise InsufficientResourcesError(
                    f"Worker {worker_id} cannot fulfill requirements: {requirements}"
                )
            
            # Create allocation
            allocation_id = str(uuid.uuid4())
            allocation = ResourceAllocation(
                id=allocation_id,
                worker_id=worker_id,
                task_id=task_id,
                resources=requirements,
                allocated_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=duration_estimate) if duration_estimate else None
            )
            
            # Update worker allocated resources
            worker.allocated = worker.allocated + requirements
            self.allocations[allocation_id] = allocation
            
            logger.info(f"Created allocation {allocation_id} for task {task_id} on worker {worker_id}")
            return allocation
    
    async def release(self, allocation_id: str):
        """Release an allocation"""
        async with self._lock:
            if allocation_id not in self.allocations:
                logger.warning(f"Unknown allocation: {allocation_id}")
                return
            
            allocation = self.allocations[allocation_id]
            worker_id = allocation.worker_id
            
            if worker_id in self.workers:
                worker = self.workers[worker_id]
                worker.allocated = worker.allocated - allocation.resources
            
            del self.allocations[allocation_id]
            logger.info(f"Released allocation {allocation_id}")
    
    async def get_resource_status(self) -> Dict[str, Any]:
        """Get current resource utilization status"""
        async with self._lock:
            total = ResourceSpec()
            allocated = ResourceSpec()
            reserved = ResourceSpec()
            
            worker_statuses = []
            for worker_id, worker in self.workers.items():
                total = total + worker.total
                allocated = allocated + worker.allocated
                reserved = reserved + worker.reserved
                
                worker_statuses.append({
                    "worker_id": worker_id,
                    "total": worker.total.to_dict(),
                    "allocated": worker.allocated.to_dict(),
                    "reserved": worker.reserved.to_dict(),
                    "available": worker.available.to_dict(),
                    "utilization": worker.utilization
                })
            
            return {
                "summary": {
                    "total": total.to_dict(),
                    "allocated": allocated.to_dict(),
                    "reserved": reserved.to_dict(),
                    "available": (total - allocated - reserved).to_dict(),
                    "utilization": {
                        'cpu': (allocated.cpu_cores / total.cpu_cores * 100) if total.cpu_cores > 0 else 0,
                        'memory': (allocated.memory_gb / total.memory_gb * 100) if total.memory_gb > 0 else 0,
                        'gpu': (allocated.gpu_count / total.gpu_count * 100) if total.gpu_count > 0 else 0,
                    }
                },
                "workers": worker_statuses,
                "active_allocations": len(self.allocations),
                "active_reservations": len(self.reservations)
            }
    
    def _get_candidates(self, 
                       requirements: ResourceSpec,
                       constraints: Optional[ResourceConstraints]) -> List[str]:
        """Get workers that can fulfill requirements"""
        candidates = []
        
        for worker_id, resources in self.workers.items():
            # Check basic resource availability
            if not resources.can_allocate(requirements):
                continue
            
            # Check constraints
            if constraints:
                if constraints.preferred_worker and worker_id != constraints.preferred_worker:
                    continue
                if constraints.exclude_workers and worker_id in constraints.exclude_workers:
                    continue
                if constraints.require_gpu_type:
                    # Would need GPU device info to check this properly
                    pass
                if constraints.require_compute_capability:
                    if not resources.total.gpu_compute_capability:
                        continue
                    if resources.total.gpu_compute_capability < constraints.require_compute_capability:
                        continue
            
            candidates.append(worker_id)
        
        return candidates
    
    def _select_worker(self, 
                      candidates: List[str], 
                      requirements: ResourceSpec,
                      strategy: AllocationStrategy) -> Optional[str]:
        """Select best worker from candidates based on strategy"""
        if not candidates:
            return None
        
        if strategy == AllocationStrategy.FIRST_FIT:
            # Return first available worker
            return candidates[0]
        
        elif strategy == AllocationStrategy.BEST_FIT:
            # Find worker with least waste
            best_worker = None
            min_waste = float('inf')
            
            for worker_id in candidates:
                worker = self.workers[worker_id]
                available = worker.available
                
                # Calculate waste (excess resources)
                cpu_waste = available.cpu_cores - requirements.cpu_cores
                mem_waste = available.memory_gb - requirements.memory_gb
                total_waste = cpu_waste + mem_waste
                
                if total_waste < min_waste:
                    min_waste = total_waste
                    best_worker = worker_id
            
            return best_worker
        
        elif strategy == AllocationStrategy.LOAD_BALANCE:
            # Select worker with lowest utilization
            scores = []
            
            for worker_id in candidates:
                worker = self.workers[worker_id]
                score = self._calculate_allocation_score(worker, requirements)
                scores.append((score, worker_id))
            
            # Sort by score (higher is better)
            scores.sort(reverse=True)
            return scores[0][1] if scores else None
        
        elif strategy == AllocationStrategy.PACK:
            # Select worker with highest utilization that can still fit
            best_worker = None
            max_utilization = -1
            
            for worker_id in candidates:
                worker = self.workers[worker_id]
                utilization = worker.utilization
                avg_util = (utilization['cpu'] + utilization['memory']) / 2
                
                if avg_util > max_utilization:
                    max_utilization = avg_util
                    best_worker = worker_id
            
            return best_worker
        
        elif strategy == AllocationStrategy.SPREAD:
            # Select worker with lowest utilization
            best_worker = None
            min_utilization = 101
            
            for worker_id in candidates:
                worker = self.workers[worker_id]
                utilization = worker.utilization
                avg_util = (utilization['cpu'] + utilization['memory']) / 2
                
                if avg_util < min_utilization:
                    min_utilization = avg_util
                    best_worker = worker_id
            
            return best_worker
        
        # Default to first fit
        return candidates[0]
    
    def _calculate_allocation_score(self, 
                                   worker: WorkerResources,
                                   requirements: ResourceSpec) -> float:
        """Calculate allocation score for load balancing"""
        available = worker.available
        
        # Factors:
        # 1. Resource fit (prefer workers with just enough resources)
        # 2. Current utilization (prefer less loaded workers)
        # 3. Resource fragmentation (prefer keeping resources together)
        
        # Resource fit score (0-1, where 1 is perfect fit)
        cpu_fit = 1.0 - min(1.0, abs(available.cpu_cores - requirements.cpu_cores) / (available.cpu_cores + 0.01))
        mem_fit = 1.0 - min(1.0, abs(available.memory_gb - requirements.memory_gb) / (available.memory_gb + 0.01))
        fit_score = (cpu_fit + mem_fit) / 2
        
        # Utilization score (0-1, where 1 is low utilization)
        utilization = worker.utilization
        util_score = 1.0 - ((utilization['cpu'] + utilization['memory']) / 200)
        
        # GPU bonus (prefer GPU workers for GPU tasks)
        gpu_bonus = 0.2 if requirements.gpu_count > 0 and worker.total.gpu_count > 0 else 0
        
        # GPU fit penalty (avoid using GPU workers for non-GPU tasks)
        gpu_penalty = -0.1 if requirements.gpu_count == 0 and worker.total.gpu_count > 0 else 0
        
        return fit_score * 0.4 + util_score * 0.6 + gpu_bonus + gpu_penalty
    
    async def _cleanup_expired(self):
        """Cleanup expired allocations and reservations"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                async with self._lock:
                    # Cleanup expired reservations
                    expired_reservations = [
                        res_id for res_id, res in self.reservations.items()
                        if res.is_expired
                    ]
                    
                    for res_id in expired_reservations:
                        reservation = self.reservations[res_id]
                        if reservation.worker_id in self.workers:
                            worker = self.workers[reservation.worker_id]
                            worker.reserved = worker.reserved - reservation.resources
                        del self.reservations[res_id]
                        logger.info(f"Cleaned up expired reservation {res_id}")
                    
                    # Cleanup expired allocations
                    expired_allocations = [
                        alloc_id for alloc_id, alloc in self.allocations.items()
                        if alloc.is_expired
                    ]
                    
                    for alloc_id in expired_allocations:
                        await self.release(alloc_id)
                        logger.info(f"Cleaned up expired allocation {alloc_id}")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")