"""
Function Runner API Client (Python)

Provides Python client for interacting with Function Runner integration APIs
for backend services and performance testing.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
import uuid

logger = logging.getLogger(__name__)


class FunctionRunnerClient:
    """
    Python client for Function Runner integration API.
    Used by backend services and performance testing.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        """
        Initialize the Function Runner client.
        
        Args:
            base_url: Base URL for the API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _ensure_session(self):
        """Ensure session is created."""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
    
    async def list_templates(self) -> List[Dict[str, Any]]:
        """
        List available function templates.
        
        Returns:
            List of template configurations
        """
        await self._ensure_session()
        
        async with self.session.get(f"{self.base_url}/api/v1/functions/templates") as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_template(self, template_id: str) -> Dict[str, Any]:
        """
        Get specific template details.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Template configuration
        """
        await self._ensure_session()
        
        async with self.session.get(
            f"{self.base_url}/api/v1/functions/templates/{template_id}"
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def submit_task(
        self,
        template_id: str,
        inputs: Dict[str, Any],
        quality: str = "standard",
        project_id: Optional[str] = None,
        shot_id: Optional[str] = None,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Submit a task for execution.
        
        Args:
            template_id: Function template to use
            inputs: Input parameters
            quality: Quality preset (low, standard, high, ultra)
            project_id: Associated project ID
            shot_id: Associated shot ID
            priority: Task priority (0-100)
            metadata: Additional metadata
            
        Returns:
            Task submission response with task_id
        """
        await self._ensure_session()
        
        payload = {
            "template_id": template_id,
            "inputs": inputs,
            "quality": quality,
            "priority": priority,
            "metadata": metadata or {}
        }
        
        if project_id:
            payload["project_id"] = project_id
        if shot_id:
            payload["shot_id"] = shot_id
            
        async with self.session.post(
            f"{self.base_url}/api/v1/integration/tasks",
            json=payload
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get current task status and progress.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status information
        """
        await self._ensure_session()
        
        async with self.session.get(
            f"{self.base_url}/api/v1/integration/tasks/{task_id}/status"
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """
        Get completed task result.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task result data
        """
        await self._ensure_session()
        
        async with self.session.get(
            f"{self.base_url}/api/v1/integration/tasks/{task_id}/result"
        ) as response:
            if response.status == 404:
                return {"status": "not_found"}
            response.raise_for_status()
            return await response.json()
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if cancelled successfully
        """
        await self._ensure_session()
        
        async with self.session.post(
            f"{self.base_url}/api/v1/integration/tasks/{task_id}/cancel"
        ) as response:
            return response.status == 200
    
    async def get_active_tasks(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of active tasks.
        
        Args:
            user_id: Filter by user ID
            project_id: Filter by project ID
            
        Returns:
            List of active tasks
        """
        await self._ensure_session()
        
        params = {}
        if user_id:
            params["user_id"] = user_id
        if project_id:
            params["project_id"] = project_id
            
        async with self.session.get(
            f"{self.base_url}/api/v1/integration/tasks/active",
            params=params
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("tasks", [])
    
    async def get_integration_health(self) -> Dict[str, Any]:
        """
        Get integration system health status.
        
        Returns:
            Health status information
        """
        await self._ensure_session()
        
        async with self.session.get(
            f"{self.base_url}/api/v1/integration/health"
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_integration_stats(self) -> Dict[str, Any]:
        """
        Get integration system statistics.
        
        Returns:
            System statistics
        """
        await self._ensure_session()
        
        async with self.session.get(
            f"{self.base_url}/api/v1/integration/stats"
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def wait_for_task_completion(
        self,
        task_id: str,
        timeout: int = 300,
        poll_interval: float = 1.0
    ) -> Dict[str, Any]:
        """
        Wait for task completion with polling.
        
        Args:
            task_id: Task identifier
            timeout: Maximum wait time in seconds
            poll_interval: Polling interval in seconds
            
        Returns:
            Final task result
        """
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            try:
                status = await self.get_task_status(task_id)
                state = status.get("status", "unknown")
                
                if state == "completed":
                    return await self.get_task_result(task_id)
                elif state == "failed":
                    return status
                elif state == "cancelled":
                    return {"status": "cancelled"}
                    
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Error checking task status: {e}")
                await asyncio.sleep(poll_interval)
        
        return {"status": "timeout", "message": "Task timeout"}