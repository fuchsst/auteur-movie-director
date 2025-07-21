# Story: STORY-098 - Basic Quality Dashboard

## Story Description
As a content creator, I need a simple dashboard to view my quality tier usage and basic system status so that I can understand my generation patterns without complex analytics.

## Acceptance Criteria
- [ ] Simple usage statistics display
- [ ] Basic quality tier counts per task type
- [ ] Recent generation history
- [ ] No predictive analytics or resource monitoring
- [ ] Clean, simple interface
- [ ] Data persistence for user-specific metrics

## Technical Details

### Simplified Dashboard API
```python
# backend/app/api/v1/simple_quality_dashboard.py
from fastapi import APIRouter, HTTPException
from typing import Dict, List
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/simple-dashboard", tags=["simple-dashboard"])

@router.get("/usage/{user_id}")
async def get_simple_usage(user_id: str) -> Dict:
    """Get simple usage statistics for user"""
    
    # Mock data structure - replace with actual storage
    usage_data = {
        "user_id": user_id,
        "total_generations": 42,
        "quality_distribution": {
            "low": 15,
            "standard": 20,
            "high": 7
        },
        "task_distribution": {
            "character_portrait": {
                "low": 8,
                "standard": 12,
                "high": 3
            },
            "scene_generation": {
                "low": 7,
                "standard": 8,
                "high": 4
            }
        },
        "last_7_days": [
            {"date": "2024-01-15", "count": 3, "quality": "standard"},
            {"date": "2024-01-16", "count": 5, "quality": "low"},
            {"date": "2024-01-17", "count": 2, "quality": "high"}
        ]
    }
    
    return usage_data

@router.get("/recent/{user_id}")
async def get_recent_activity(user_id: str, limit: int = 10) -> List[Dict]:
    """Get recent generation activity"""
    
    recent_activity = [
        {
            "task_id": "task_123",
            "task_type": "character_portrait",
            "quality_tier": "standard",
            "timestamp": "2024-01-17T10:30:00Z",
            "status": "completed"
        },
        {
            "task_id": "task_124",
            "task_type": "scene_generation",
            "quality_tier": "high",
            "timestamp": "2024-01-17T09:15:00Z",
            "status": "completed"
        }
    ]
    
    return recent_activity[:limit]
```

### Simple Frontend Dashboard
```svelte
<!-- frontend/src/lib/components/SimpleQualityDashboard.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';

  let usageData = null;
  let recentActivity = [];

  onMount(async () => {
    const userId = 'current_user'; // Get from auth
    
    const [usage, recent] = await Promise.all([
      fetch(`/api/v1/simple-dashboard/usage/${userId}`).then(r => r.json()),
      fetch(`/api/v1/simple-dashboard/recent/${userId}`).then(r => r.json())
    ]);
    
    usageData = usage;
    recentActivity = recent;
  });

  const qualityColors = {
    low: '#ff9800',
    standard: '#2196f3',
    high: '#4caf50'
  };
</script>

<div class="simple-dashboard">
  {#if usageData}
    <div class="stats-grid">
      <div class="stat-card">
        <h3>Total Generations</h3>
        <div class="stat-number">{usageData.total_generations}</div>
      </div>
      
      <div class="stat-card">
        <h3>Quality Distribution</h3>
        <div class="quality-bars">
          {#each Object.entries(usageData.quality_distribution) as [tier, count]}
            <div class="quality-bar">
              <span>{tier}</span>
              <div class="bar" style="width: {(count / usageData.total_generations) * 100}%; background-color: {qualityColors[tier]}">
                {count}
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>

    <div class="recent-activity">
      <h3>Recent Activity</h3>
      <div class="activity-list">
        {#each recentActivity as activity}
          <div class="activity-item">
            <span class="task-type">{activity.task_type}</span>
            <span class="quality-badge" style="background-color: {qualityColors[activity.quality_tier]}">
              {activity.quality_tier}
            </span>
            <span class="timestamp">{new Date(activity.timestamp).toLocaleString()}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .simple-dashboard {
    padding: 1rem;
    max-width: 800px;
    margin: 0 auto;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .stat-card {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }

  .stat-number {
    font-size: 2rem;
    font-weight: bold;
    color: #333;
  }

  .quality-bars {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .quality-bar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .quality-bar span {
    min-width: 60px;
    text-transform: capitalize;
  }

  .bar {
    height: 20px;
    border-radius: 10px;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    min-width: 30px;
  }

  .recent-activity {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }

  .activity-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid #eee;
  }

  .quality-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    color: white;
    font-size: 0.75rem;
    text-transform: uppercase;
  }

  .timestamp {
    font-size: 0.875rem;
    color: #666;
  }
</style>
```

### Data Storage Service
```python
# backend/app/services/simple_metrics_storage.py
import json
import os
from typing import Dict, List
from datetime import datetime

class SimpleMetricsStorage:
    def __init__(self, storage_dir: str = "./user_metrics"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def record_generation(
        self, 
        user_id: str, 
        task_type: str, 
        quality_tier: str,
        task_id: str
    ):
        """Record a simple generation metric"""
        
        user_file = os.path.join(self.storage_dir, f"{user_id}.json")
        
        # Load existing data
        data = {"generations": []}
        if os.path.exists(user_file):
            with open(user_file, 'r') as f:
                data = json.load(f)
        
        # Add new generation
        data["generations"].append({
            "task_id": task_id,
            "task_type": task_type,
            "quality_tier": quality_tier,
            "timestamp": datetime.now().isoformat()
        })
        
        # Save updated data
        with open(user_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_user_metrics(self, user_id: str) -> Dict:
        """Get simple metrics for user"""
        
        user_file = os.path.join(self.storage_dir, f"{user_id}.json")
        
        if not os.path.exists(user_file):
            return {
                "generations": [],
                "total": 0,
                "by_quality": {},
                "by_task": {}
            }
        
        with open(user_file, 'r') as f:
            data = json.load(f)
        
        # Calculate simple aggregations
        total = len(data["generations"])
        by_quality = {}
        by_task = {}
        
        for gen in data["generations"]:
            quality = gen["quality_tier"]
            task = gen["task_type"]
            
            by_quality[quality] = by_quality.get(quality, 0) + 1
            
            if task not in by_task:
                by_task[task] = {"low": 0, "standard": 0, "high": 0}
            by_task[task][quality] += 1
        
        return {
            "generations": data["generations"][-10:],  # Last 10
            "total": total,
            "by_quality": by_quality,
            "by_task": by_task
        }
```

## Test Requirements
- Basic usage statistics accuracy
- Recent activity display
- User preference persistence
- Simple UI functionality
- Data storage reliability

## Definition of Done
- Dashboard shows accurate usage counts
- Recent activity displays correctly
- UI is clean and simple
- Data persists across sessions
- No complex analytics or predictions