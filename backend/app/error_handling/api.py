"""API endpoints for error handling system"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends

from ..core.dependencies import get_error_handler
from .integration import ErrorHandlingIntegration
from .models import ErrorAnalysisReport

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/errors", tags=["error-handling"])


@router.get("/analysis")
async def get_error_analysis(
    window_minutes: int = Query(5, ge=1, le=60),
    error_handler: ErrorHandlingIntegration = Depends(get_error_handler)
) -> Dict[str, Any]:
    """Get comprehensive error analysis"""
    try:
        analysis = await error_handler.get_error_analysis()
        return {
            "status": "success",
            "data": analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get error analysis: {str(e)}")


@router.get("/stats")
async def get_error_stats(
    error_handler: ErrorHandlingIntegration = Depends(get_error_handler)
) -> Dict[str, Any]:
    """Get current error statistics"""
    try:
        stats = error_handler.analytics.get_error_stats()
        return {
            "status": "success",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get error stats: {str(e)}")


@router.get("/circuit-breakers")
async def get_circuit_breaker_status(
    error_handler: ErrorHandlingIntegration = Depends(get_error_handler)
) -> Dict[str, Any]:
    """Get circuit breaker status"""
    try:
        breaker_stats = error_handler.circuit_breakers.get_all_stats()
        health_status = error_handler.circuit_breakers.get_health_status()
        
        return {
            "status": "success",
            "data": {
                "breakers": breaker_stats,
                "health": health_status
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get circuit breaker status: {str(e)}")


@router.post("/circuit-breakers/{service}/reset")
async def reset_circuit_breaker(
    service: str,
    error_handler: ErrorHandlingIntegration = Depends(get_error_handler)
) -> Dict[str, Any]:
    """Reset a circuit breaker"""
    try:
        breaker = error_handler.circuit_breakers.get_breaker(service)
        await breaker.reset()
        
        return {
            "status": "success",
            "message": f"Circuit breaker '{service}' reset successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to reset circuit breaker: {str(e)}")


@router.get("/recovery/stats")
async def get_recovery_stats(
    error_handler: ErrorHandlingIntegration = Depends(get_error_handler)
) -> Dict[str, Any]:
    """Get recovery statistics"""
    try:
        stats = error_handler.recovery.get_recovery_stats()
        return {
            "status": "success",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get recovery stats: {str(e)}")


@router.get("/compensation/stats")
async def get_compensation_stats(
    error_handler: ErrorHandlingIntegration = Depends(get_error_handler)
) -> Dict[str, Any]:
    """Get compensation statistics"""
    try:
        stats = error_handler.compensation.get_compensation_stats()
        failed = error_handler.compensation.get_failed_compensations()
        
        return {
            "status": "success",
            "data": {
                "stats": stats,
                "failed_compensations": failed
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get compensation stats: {str(e)}")


@router.get("/self-healing/stats")
async def get_self_healing_stats(
    error_handler: ErrorHandlingIntegration = Depends(get_error_handler)
) -> Dict[str, Any]:
    """Get self-healing statistics"""
    try:
        stats = error_handler.self_healing.get_healing_stats()
        return {
            "status": "success",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get self-healing stats: {str(e)}")


@router.post("/self-healing/diagnose")
async def trigger_diagnosis(
    error_handler: ErrorHandlingIntegration = Depends(get_error_handler)
) -> Dict[str, Any]:
    """Trigger immediate system diagnosis and healing"""
    try:
        results = await error_handler.self_healing.diagnose_and_heal()
        
        return {
            "status": "success",
            "data": {
                "healing_attempts": len(results),
                "results": [
                    {
                        "issue_id": r.issue_id,
                        "action": r.action,
                        "success": r.success,
                        "reason": r.reason
                    }
                    for r in results
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to trigger diagnosis: {str(e)}")


@router.get("/alerts/thresholds")
async def get_alert_thresholds(
    error_handler: ErrorHandlingIntegration = Depends(get_error_handler)
) -> Dict[str, Any]:
    """Get current alert thresholds"""
    try:
        thresholds = error_handler.analytics.alert_thresholds
        return {
            "status": "success",
            "data": thresholds,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get alert thresholds: {str(e)}")


@router.put("/alerts/thresholds")
async def update_alert_thresholds(
    thresholds: Dict[str, float],
    error_handler: ErrorHandlingIntegration = Depends(get_error_handler)
) -> Dict[str, Any]:
    """Update alert thresholds"""
    try:
        # Validate threshold keys
        valid_keys = set(error_handler.analytics.alert_thresholds.keys())
        invalid_keys = set(thresholds.keys()) - valid_keys
        
        if invalid_keys:
            raise HTTPException(
                400,
                f"Invalid threshold keys: {invalid_keys}. Valid keys: {valid_keys}"
            )
        
        # Update thresholds
        error_handler.analytics.alert_thresholds.update(thresholds)
        
        return {
            "status": "success",
            "message": "Alert thresholds updated",
            "data": error_handler.analytics.alert_thresholds,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to update alert thresholds: {str(e)}")


@router.get("/task/{task_id}/history")
async def get_task_error_history(
    task_id: str,
    error_handler: ErrorHandlingIntegration = Depends(get_error_handler)
) -> Dict[str, Any]:
    """Get error history for a specific task"""
    try:
        history = error_handler.context_manager.get_history(task_id)
        
        if not history:
            return {
                "status": "success",
                "data": {
                    "task_id": task_id,
                    "errors": [],
                    "recovery_attempts": []
                },
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "status": "success",
            "data": {
                "task_id": task_id,
                "errors": [e.model_dump() for e in history.errors],
                "recovery_attempts": [r.model_dump() for r in history.recovery_attempts],
                "total_retries": history.total_retries,
                "last_error_time": history.last_error_time.isoformat() if history.last_error_time else None
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get task error history: {str(e)}")


@router.get("/health")
async def get_error_handling_health(
    error_handler: ErrorHandlingIntegration = Depends(get_error_handler)
) -> Dict[str, Any]:
    """Get overall health of error handling system"""
    try:
        # Get various health indicators
        breaker_health = error_handler.circuit_breakers.get_health_status()
        recovery_stats = error_handler.recovery.get_recovery_stats()
        healing_stats = error_handler.self_healing.get_healing_stats()
        error_stats = error_handler.analytics.get_error_stats()
        
        # Calculate overall health score
        health_score = (
            breaker_health['health_percentage'] * 0.3 +
            recovery_stats.get('success_rate', 0) * 100 * 0.3 +
            healing_stats.get('success_rate', 0) * 100 * 0.2 +
            (100 - min(error_stats.get('recent_error_rate', 0) * 100, 100)) * 0.2
        )
        
        return {
            "status": "success",
            "data": {
                "health_score": round(health_score, 2),
                "status": "healthy" if health_score > 80 else "degraded" if health_score > 60 else "unhealthy",
                "components": {
                    "circuit_breakers": breaker_health,
                    "recovery_success_rate": recovery_stats.get('success_rate', 0),
                    "healing_success_rate": healing_stats.get('success_rate', 0),
                    "recent_error_rate": error_stats.get('recent_error_rate', 0)
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get error handling health: {str(e)}")


# WebSocket endpoint for real-time error monitoring
@router.websocket("/ws")
async def websocket_error_monitoring(websocket):
    """WebSocket endpoint for real-time error monitoring"""
    await websocket.accept()
    
    try:
        # This would subscribe to error events and stream them
        # For now, just a placeholder
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()