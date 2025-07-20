"""
Load generation engine for performance testing.

Provides virtual users and task submission capabilities for simulating
realistic load patterns against the Function Runner Architecture.
"""

import asyncio
import logging
import random
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from app.integration.client import FunctionRunnerClient
from app.performance.scenarios import LoadScenario, TaskProfile

logger = logging.getLogger(__name__)


@dataclass
class LoadResults:
    """Results from a load testing scenario."""
    
    scenario_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    total_submitted: int = 0
    total_completed: int = 0
    total_errors: int = 0
    user_metrics: Dict[str, Any] = field(default_factory=dict)
    task_metrics: Dict[str, Any] = field(default_factory=dict)
    latency_distribution: Dict[str, List[float]] = field(default_factory=dict)
    error_details: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class UserBehavior:
    """Defines the behavior pattern for a virtual user."""
    
    task_profiles: List[TaskProfile]
    think_time_min: float = 1.0
    think_time_max: float = 5.0
    session_duration: Optional[float] = None
    error_retry_probability: float = 0.3
    
    def get_next_task(self) -> Optional[TaskProfile]:
        """Get the next task to execute based on frequency weights."""
        if not self.task_profiles:
            return None
        
        # Weight by frequency
        weights = [profile.frequency for profile in self.task_profiles]
        return random.choices(self.task_profiles, weights=weights)[0]
    
    def get_think_time(self) -> float:
        """Get think time between tasks."""
        return random.uniform(self.think_time_min, self.think_time_max)


class VirtualUser:
    """Simulates a real user generating load against the system."""
    
    def __init__(self, 
                 user_id: str,
                 behavior: UserBehavior,
                 client_config: Optional[Dict[str, Any]] = None):
        """
        Initialize a virtual user.
        
        Args:
            user_id: Unique identifier for this user
            behavior: User behavior configuration
            client_config: Configuration for the FunctionRunnerClient
        """
        self.user_id = user_id
        self.behavior = behavior
        self.client = FunctionRunnerClient(**(client_config or {}))
        
        self.active = True
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Metrics
        self.tasks_submitted = 0
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.total_latency = 0.0
        self.latencies: List[float] = []
        self.errors: List[Dict[str, Any]] = []
        
        # Task tracking
        self.pending_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: Dict[str, Dict[str, Any]] = {}
        
        logger.debug(f"Virtual user {user_id} initialized")
    
    async def start(self):
        """Start the virtual user's activity."""
        self.start_time = datetime.now()
        logger.debug(f"User {self.user_id} started at {self.start_time}")
        
        try:
            while self.active:
                # Check if session should end
                if self.behavior.session_duration:
                    elapsed = (datetime.now() - self.start_time).total_seconds()
                    if elapsed >= self.behavior.session_duration:
                        break
                
                # Get next task
                task_profile = self.behavior.get_next_task()
                if not task_profile:
                    await asyncio.sleep(self.behavior.get_think_time())
                    continue
                
                # Execute task
                await self._execute_task(task_profile)
                
                # Think time
                think_time = self.behavior.get_think_time()
                await asyncio.sleep(think_time)
                
        except Exception as e:
            logger.error(f"User {self.user_id} encountered error: {e}")
            self.errors.append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'type': 'user_error'
            })
        finally:
            self.end_time = datetime.now()
            logger.debug(f"User {self.user_id} finished at {self.end_time}")
    
    async def _execute_task(self, task_profile: TaskProfile):
        """Execute a single task based on the profile."""
        try:
            # Select quality level
            quality = self._select_quality(task_profile.quality_distribution)
            
            # Generate inputs
            inputs = self._generate_inputs(task_profile.template_id, quality)
            
            # Submit task
            task_id = str(uuid.uuid4())
            submit_start = time.time()
            
            response = await self.client.submit_task(
                template_id=task_profile.template_id,
                inputs=inputs,
                quality=quality,
                metadata={"user_id": self.user_id, "task_id": task_id}
            )
            submit_latency = time.time() - submit_start
            
            # Track submission
            self.tasks_submitted += 1
            self.total_latency += submit_latency
            self.latencies.append(submit_latency)
            
            self.pending_tasks[task_id] = {
                'template_id': task_profile.template_id,
                'quality': quality,
                'submit_time': datetime.now(),
                'submit_latency': submit_latency
            }
            
            # Track completion asynchronously
            asyncio.create_task(self._track_task_completion(task_id))
            
            logger.debug(f"User {self.user_id} submitted task {task_id} "
                        f"({task_profile.template_id}) in {submit_latency:.3f}s")
            
        except Exception as e:
            self.tasks_failed += 1
            self.errors.append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'type': 'task_submission_error',
                'template_id': task_profile.template_id
            })
            logger.error(f"User {self.user_id} task submission failed: {e}")
    
    async def _track_task_completion(self, task_id: str):
        """Track the completion of a submitted task."""
        try:
            max_wait = 300  # 5 minutes max wait
            check_interval = 1.0
            
            start_wait = time.time()
            while time.time() - start_wait < max_wait:
                try:
                    status = await self.client.get_task_status(task_id)
                    
                    if status.get('status') == 'completed':
                        self.tasks_completed += 1
                        
                        # Move from pending to completed
                        if task_id in self.pending_tasks:
                            task_info = self.pending_tasks.pop(task_id)
                            task_info['complete_time'] = datetime.now()
                            task_info['total_latency'] = time.time() - start_wait
                            self.completed_tasks[task_id] = task_info
                        
                        logger.debug(f"User {self.user_id} task {task_id} completed")
                        return
                    
                    elif status.get('status') == 'failed':
                        self.tasks_failed += 1
                        
                        if task_id in self.pending_tasks:
                            task_info = self.pending_tasks.pop(task_id)
                            task_info['failed_time'] = datetime.now()
                            self.completed_tasks[task_id] = task_info
                        
                        self.errors.append({
                            'timestamp': datetime.now().isoformat(),
                            'error': status.get('error', 'Task failed'),
                            'type': 'task_failure',
                            'task_id': task_id
                        })
                        
                        logger.warning(f"User {self.user_id} task {task_id} failed")
                        return
                    
                except Exception as e:
                    logger.error(f"Error checking task {task_id} status: {e}")
                
                await asyncio.sleep(check_interval)
            
            # Timeout
            self.tasks_failed += 1
            self.errors.append({
                'timestamp': datetime.now().isoformat(),
                'error': 'Task timeout',
                'type': 'task_timeout',
                'task_id': task_id
            })
            
        except Exception as e:
            logger.error(f"Error tracking task {task_id}: {e}")
    
    def _select_quality(self, quality_distribution: Dict[str, float]) -> str:
        """Select quality level based on distribution."""
        qualities = list(quality_distribution.keys())
        weights = list(quality_distribution.values())
        return random.choices(qualities, weights=weights)[0]
    
    def _generate_inputs(self, template_id: str, quality: str) -> Dict[str, Any]:
        """Generate appropriate inputs for the given template and quality."""
        
        # Mock input generators - in real implementation, these would be more sophisticated
        generators = {
            'image_generation_v1': lambda q: {
                'prompt': f"A beautiful landscape photo, {quality} quality",
                'width': 1024 if q == 'high' else 512,
                'height': 1024 if q == 'high' else 512,
                'steps': 50 if q == 'high' else 20
            },
            'text_generation_v1': lambda q: {
                'prompt': f"Write a short story about {quality} quality",
                'max_tokens': 500 if q == 'high' else 200,
                'temperature': 0.7
            },
            'video_generation_v1': lambda q: {
                'prompt': f"A short animation, {quality} quality",
                'duration': 5 if q == 'high' else 2,
                'fps': 30 if q == 'high' else 15
            },
            'audio_generation_v1': lambda q: {
                'prompt': f"Generate background music, {quality} quality",
                'duration': 30 if q == 'high' else 10,
                'sample_rate': 44100 if q == 'high' else 22050
            },
            'high_res_image_generation_v1': lambda q: {
                'prompt': f"Ultra high resolution photo, {quality} quality",
                'width': 2048,
                'height': 2048,
                'steps': 100
            },
            'long_video_generation_v1': lambda q: {
                'prompt': f"Long form video content, {quality} quality",
                'duration': 60,
                'fps': 30
            },
            'complex_text_generation_v1': lambda q: {
                'prompt': f"Generate detailed technical documentation, {quality} quality",
                'max_tokens': 2000,
                'temperature': 0.8
            }
        }
        
        generator = generators.get(template_id)
        if generator:
            return generator(quality)
        
        # Fallback generic input
        return {
            'prompt': f'Generate content with {quality} quality',
            'template': template_id
        }
    
    def stop(self):
        """Stop the virtual user's activity."""
        self.active = False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this user."""
        return {
            'user_id': self.user_id,
            'tasks_submitted': self.tasks_submitted,
            'tasks_completed': self.tasks_completed,
            'tasks_failed': self.tasks_failed,
            'success_rate': (
                self.tasks_completed / self.tasks_submitted 
                if self.tasks_submitted > 0 else 0
            ),
            'avg_latency': (
                self.total_latency / self.tasks_submitted 
                if self.tasks_submitted > 0 else 0
            ),
            'latencies': self.latencies,
            'errors': self.errors,
            'session_duration': (
                (self.end_time - self.start_time).total_seconds()
                if self.start_time and self.end_time else None
            )
        }


class LoadGenerator:
    """Generates load by orchestrating multiple virtual users."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the load generator.
        
        Args:
            config: Configuration options for the load generator
        """
        self.config = config or {}
        self.client_config = self.config.get('client', {})
        
        self.active_users: List[VirtualUser] = []
        self.results: Optional[LoadResults] = None
        
        logger.info("Load generator initialized")
    
    async def run_scenario(self, scenario: LoadScenario) -> LoadResults:
        """
        Execute a complete load testing scenario.
        
        Args:
            scenario: The load scenario to execute
            
        Returns:
            Comprehensive load testing results
        """
        logger.info(f"Starting scenario: {scenario.name}")
        
        self.results = LoadResults(
            scenario_name=scenario.name,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=0.0
        )
        
        try:
            # Create user behavior
            behavior = UserBehavior(
                task_profiles=scenario.tasks,
                think_time_min=self.config.get('think_time_min', 1.0),
                think_time_max=self.config.get('think_time_max', 5.0),
                session_duration=scenario.duration_seconds
            )
            
            # Handle spike configuration if provided
            if scenario.spike_config:
                await self._run_spike_scenario(scenario, behavior)
            else:
                await self._run_standard_scenario(scenario, behavior)
            
            # Collect final results
            self.results.end_time = datetime.now()
            self.results.duration_seconds = (
                self.results.end_time - self.results.start_time
            ).total_seconds()
            
            # Aggregate user metrics
            await self._aggregate_results()
            
            logger.info(f"Scenario {scenario.name} completed: "
                       f"{self.results.total_submitted} submitted, "
                       f"{self.results.total_completed} completed, "
                       f"{self.results.total_errors} errors")
            
            return self.results
            
        except Exception as e:
            logger.error(f"Scenario {scenario.name} failed: {e}")
            raise
    
    async def _run_standard_scenario(self, scenario: LoadScenario, behavior: UserBehavior):
        """Run a standard load scenario with gradual ramp-up."""
        
        # Ramp up users
        await self._ramp_up_users(scenario.users, scenario.ramp_up_seconds, behavior)
        
        # Run for duration
        await asyncio.sleep(scenario.duration_seconds - scenario.ramp_up_seconds)
        
        # Ramp down users
        await self._ramp_down_users()
    
    async def _run_spike_scenario(self, scenario: LoadScenario, behavior: UserBehavior):
        """Run a spike testing scenario."""
        
        spike_config = scenario.spike_config
        
        # Initial load
        await self._ramp_up_users(scenario.users, scenario.ramp_up_seconds, behavior)
        
        # Wait for spike time
        await asyncio.sleep(spike_config.spike_at_seconds - scenario.ramp_up_seconds)
        
        # Apply spike
        logger.info(f"Applying spike: +{spike_config.spike_users} users")
        await self._apply_spike(spike_config.spike_users, spike_config.spike_ramp_seconds, behavior)
        
        # Hold spike
        await asyncio.sleep(spike_config.spike_duration_seconds)
        
        # Remove spike
        logger.info("Removing spike load")
        await self._remove_spike_users(spike_config.spike_users)
        
        # Continue with base load
        remaining_time = (
            scenario.duration_seconds 
            - spike_config.spike_at_seconds 
            - spike_config.spike_duration_seconds
            - scenario.ramp_up_seconds
        )
        
        if remaining_time > 0:
            await asyncio.sleep(remaining_time)
        
        # Ramp down
        await self._ramp_down_users()
    
    async def _ramp_up_users(self, target_users: int, ramp_seconds: int, behavior: UserBehavior):
        """Gradually ramp up the number of active users."""
        
        if ramp_seconds <= 0:
            # Immediate ramp-up
            for i in range(target_users):
                await self._add_user(behavior)
            return
        
        # Gradual ramp-up
        users_per_second = target_users / ramp_seconds
        
        for second in range(ramp_seconds):
            users_to_add = int(users_per_second * (second + 1)) - len(self.active_users)
            
            for _ in range(users_to_add):
                await self._add_user(behavior)
            
            await asyncio.sleep(1)
    
    async def _add_user(self, behavior: UserBehavior):
        """Add a new virtual user."""
        user_id = f"user_{len(self.active_users)}_{int(time.time())}"
        user = VirtualUser(user_id, behavior, self.client_config)
        
        self.active_users.append(user)
        
        # Start user in background
        asyncio.create_task(user.start())
        
        logger.debug(f"Added user {user_id} (total: {len(self.active_users)})")
    
    async def _apply_spike(self, spike_users: int, ramp_seconds: int, behavior: UserBehavior):
        """Apply spike load."""
        
        users_per_second = spike_users / ramp_seconds
        
        for second in range(ramp_seconds):
            users_to_add = int(users_per_second * (second + 1))
            
            for _ in range(users_to_add):
                await self._add_user(behavior)
            
            await asyncio.sleep(1)
    
    async def _remove_spike_users(self, spike_users: int):
        """Remove spike users."""
        
        # Remove spike users from the end
        users_to_remove = min(spike_users, len(self.active_users))
        
        for _ in range(users_to_remove):
            if self.active_users:
                user = self.active_users.pop()
                user.stop()
    
    async def _ramp_down_users(self):
        """Gradually ramp down all users."""
        
        ramp_duration = min(30, len(self.active_users))  # Max 30 seconds
        
        while self.active_users:
            batch_size = max(1, len(self.active_users) // ramp_duration)
            
            for _ in range(batch_size):
                if self.active_users:
                    user = self.active_users.pop()
                    user.stop()
            
            await asyncio.sleep(1)
    
    async def _aggregate_results(self):
        """Aggregate results from all virtual users."""
        
        if not self.results:
            return
        
        # Wait for all users to complete
        await asyncio.sleep(2)  # Brief wait for final metrics
        
        # Collect metrics from all users
        user_metrics = []
        for user in self.active_users:
            user_metrics.append(user.get_metrics())
        
        # Aggregate
        if user_metrics:
            self.results.total_submitted = sum(m['tasks_submitted'] for m in user_metrics)
            self.results.total_completed = sum(m['tasks_completed'] for m in user_metrics)
            self.results.total_errors = sum(m['tasks_failed'] for m in user_metrics)
            
            # Collect latency data
            all_latencies = []
            for m in user_metrics:
                all_latencies.extend(m['latencies'])
            
            self.results.latency_distribution = {
                'all': all_latencies,
                'p50': self._calculate_percentile(all_latencies, 50),
                'p95': self._calculate_percentile(all_latencies, 95),
                'p99': self._calculate_percentile(all_latencies, 99),
            }
            
            # Store user metrics
            self.results.user_metrics = {
                'total_users': len(user_metrics),
                'individual_metrics': user_metrics
            }
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate a percentile value."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def stop(self):
        """Stop all active users."""
        for user in self.active_users:
            user.stop()