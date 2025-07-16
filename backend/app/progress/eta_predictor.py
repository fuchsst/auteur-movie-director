"""ETA prediction for task completion"""

import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
from cachetools import TTLCache

from .models import TaskHistory


class ETAPredictor:
    """Predict task completion time based on historical data"""
    
    def __init__(self, cache_size: int = 1000, cache_ttl: int = 3600):
        self.history_cache = TTLCache(maxsize=cache_size, ttl=cache_ttl)
        self.template_stats: Dict[str, Dict] = defaultdict(dict)
    
    async def predict(
        self, 
        template_id: str, 
        current_stage: int,
        stage_progress: float, 
        total_stages: int,
        quality: str = 'standard',
        historical_data: Optional[List[TaskHistory]] = None
    ) -> Optional[datetime]:
        """Predict completion time for task"""
        
        # Try cache first
        cache_key = f"{template_id}:{quality}:{current_stage}:{int(stage_progress * 100)}"
        if cache_key in self.history_cache:
            return self.history_cache[cache_key]
        
        # Get similar tasks
        similar_tasks = self._filter_similar_tasks(
            historical_data or [], 
            template_id, 
            quality
        )
        
        if len(similar_tasks) < 3:
            # Fallback to simple estimate if not enough data
            eta = self._simple_estimate(
                current_stage, 
                stage_progress, 
                total_stages
            )
        else:
            # Calculate based on historical data
            remaining_time = self._calculate_remaining_time(
                similar_tasks, 
                current_stage, 
                stage_progress,
                total_stages
            )
            
            # Apply confidence factor
            confidence = self._calculate_confidence(similar_tasks)
            adjusted_time = remaining_time * (1 + (1 - confidence) * 0.5)
            
            eta = datetime.now() + timedelta(seconds=adjusted_time)
        
        # Cache result
        self.history_cache[cache_key] = eta
        return eta
    
    def _filter_similar_tasks(
        self, 
        historical_data: List[TaskHistory],
        template_id: str, 
        quality: str
    ) -> List[TaskHistory]:
        """Filter tasks with similar characteristics"""
        similar = []
        
        for task in historical_data:
            if task.template_id == template_id and task.quality == quality and task.success:
                similar.append(task)
        
        # Sort by completion time (most recent first)
        similar.sort(key=lambda t: t.completed_at, reverse=True)
        
        # Use only recent tasks (last 100 or last 7 days)
        cutoff_date = datetime.now() - timedelta(days=7)
        recent_similar = [
            task for task in similar[:100] 
            if task.completed_at > cutoff_date
        ]
        
        return recent_similar
    
    def _calculate_remaining_time(
        self, 
        similar_tasks: List[TaskHistory],
        current_stage: int, 
        stage_progress: float,
        total_stages: int
    ) -> float:
        """Calculate remaining time based on similar tasks"""
        
        # Get stage durations from similar tasks
        stage_durations = defaultdict(list)
        
        for task in similar_tasks:
            for stage_id, duration in task.stage_durations.items():
                stage_durations[stage_id].append(duration)
        
        # Calculate percentile durations for each stage
        percentile_durations = {}
        for stage_id, durations in stage_durations.items():
            if durations:
                # Use 75th percentile for more conservative estimates
                percentile_durations[stage_id] = self._percentile(durations, 75)
        
        # Calculate remaining time
        remaining = 0.0
        
        # Remaining time in current stage
        if current_stage in percentile_durations:
            remaining += percentile_durations[current_stage] * (1 - stage_progress)
        else:
            # Estimate based on average stage duration
            avg_duration = sum(percentile_durations.values()) / len(percentile_durations) if percentile_durations else 60
            remaining += avg_duration * (1 - stage_progress)
        
        # Time for remaining stages
        for stage_id in range(current_stage + 1, total_stages):
            if stage_id in percentile_durations:
                remaining += percentile_durations[stage_id]
            else:
                # Estimate based on average
                avg_duration = sum(percentile_durations.values()) / len(percentile_durations) if percentile_durations else 60
                remaining += avg_duration
        
        return remaining
    
    def _calculate_confidence(self, similar_tasks: List[TaskHistory]) -> float:
        """Calculate confidence in prediction based on data quality"""
        if not similar_tasks:
            return 0.0
        
        # Factors affecting confidence
        confidence = 1.0
        
        # Number of samples
        if len(similar_tasks) < 10:
            confidence *= len(similar_tasks) / 10
        
        # Recency of data
        latest = similar_tasks[0].completed_at
        oldest = similar_tasks[-1].completed_at
        data_age = (datetime.now() - oldest).days
        
        if data_age > 30:
            confidence *= 0.8
        elif data_age > 7:
            confidence *= 0.9
        
        # Variance in durations
        durations = [task.total_duration for task in similar_tasks]
        if len(durations) > 1:
            cv = statistics.stdev(durations) / statistics.mean(durations)  # Coefficient of variation
            if cv > 0.5:
                confidence *= 0.7
            elif cv > 0.3:
                confidence *= 0.85
        
        return min(max(confidence, 0.1), 1.0)
    
    def _simple_estimate(
        self, 
        current_stage: int, 
        stage_progress: float,
        total_stages: int
    ) -> datetime:
        """Simple time estimate when no historical data available"""
        # Default stage durations (in seconds)
        default_durations = {
            0: 5,      # Queue
            1: 30,     # Preparation/Loading
            2: 120,    # Main execution
            3: 20      # Finalization
        }
        
        remaining = 0.0
        
        # Current stage
        current_duration = default_durations.get(current_stage, 60)
        remaining += current_duration * (1 - stage_progress)
        
        # Remaining stages
        for stage in range(current_stage + 1, total_stages):
            remaining += default_durations.get(stage, 60)
        
        return datetime.now() + timedelta(seconds=remaining)
    
    async def record_completion(
        self, 
        task_id: str, 
        template_id: str,
        quality: str,
        stage_durations: Dict[int, float],
        total_duration: float,
        resource_config: Dict[str, any]
    ):
        """Record task completion for future predictions"""
        history = TaskHistory(
            task_id=task_id,
            template_id=template_id,
            quality=quality,
            stage_durations=stage_durations,
            total_duration=total_duration,
            resource_config=resource_config,
            completed_at=datetime.now(),
            success=True
        )
        
        # Update template statistics
        self._update_template_stats(template_id, quality, history)
        
        # TODO: Store in database for long-term analysis
        # await self._store_history(history)
    
    def _update_template_stats(
        self, 
        template_id: str, 
        quality: str,
        history: TaskHistory
    ):
        """Update running statistics for template"""
        key = f"{template_id}:{quality}"
        
        if key not in self.template_stats:
            self.template_stats[key] = {
                'count': 0,
                'total_duration': 0,
                'stage_durations': defaultdict(float)
            }
        
        stats = self.template_stats[key]
        stats['count'] += 1
        stats['total_duration'] += history.total_duration
        
        for stage_id, duration in history.stage_durations.items():
            stats['stage_durations'][stage_id] += duration
    
    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (len(sorted_data) - 1) * percentile / 100
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))