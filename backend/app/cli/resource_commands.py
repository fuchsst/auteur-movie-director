"""
CLI commands for resource management
"""

import click
import asyncio
import json
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.columns import Columns
from rich import box

from app.resources import (
    ResourceMapper,
    GPUResourceManager,
    ResourceMonitor,
    QualityResourceScaler,
    ResourceSpec,
    AllocationStrategy
)

console = Console()


@click.group(name="resources")
def resource_commands():
    """Resource management commands"""
    pass


@resource_commands.command(name="status")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def resource_status(output_json: bool):
    """Show current resource status"""
    
    async def _get_status():
        # Initialize components
        resource_mapper = ResourceMapper()
        gpu_manager = GPUResourceManager()
        
        # Get status
        resource_status = await resource_mapper.get_resource_status()
        gpu_status = await gpu_manager.get_gpu_status()
        
        return resource_status, gpu_status
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task("Getting resource status...", total=None)
        resource_status, gpu_status = asyncio.run(_get_status())
    
    if output_json:
        console.print(json.dumps({
            "resources": resource_status,
            "gpus": gpu_status,
            "timestamp": datetime.now().isoformat()
        }, indent=2))
        return
    
    # Display resource summary
    summary = resource_status["summary"]
    console.print(Panel.fit(
        f"[bold]Resource Summary[/bold]\n"
        f"Total CPU: {summary['total']['cpu_cores']:.1f} cores\n"
        f"Total Memory: {summary['total']['memory_gb']:.1f} GB\n"
        f"Total GPUs: {summary['total']['gpu_count']}\n"
        f"Active Allocations: {resource_status['active_allocations']}\n"
        f"Active Reservations: {resource_status['active_reservations']}",
        title="System Resources",
        border_style="blue"
    ))
    
    # Display utilization
    util = summary["utilization"]
    console.print(Panel.fit(
        f"[bold]Utilization[/bold]\n"
        f"CPU: {util['cpu']:.1f}%\n"
        f"Memory: {util['memory']:.1f}%\n"
        f"GPU: {util['gpu']:.1f}%",
        title="Resource Utilization",
        border_style="green" if util['cpu'] < 80 else "yellow"
    ))
    
    # Display workers table
    if resource_status["workers"]:
        table = Table(title="Worker Resources", box=box.ROUNDED)
        table.add_column("Worker ID", style="cyan")
        table.add_column("CPU (cores)", justify="right")
        table.add_column("Memory (GB)", justify="right")
        table.add_column("GPU", justify="center")
        table.add_column("Utilization", justify="right")
        
        for worker in resource_status["workers"]:
            worker_id = worker["worker_id"]
            total = worker["total"]
            util = worker["utilization"]
            
            # Format utilization
            util_str = f"CPU: {util['cpu']:.0f}% MEM: {util['memory']:.0f}%"
            if total["gpu_count"] > 0:
                util_str += f" GPU: {util['gpu']:.0f}%"
            
            table.add_row(
                worker_id,
                f"{total['cpu_cores']:.1f}",
                f"{total['memory_gb']:.1f}",
                "✓" if total["gpu_count"] > 0 else "✗",
                util_str
            )
        
        console.print(table)
    
    # Display GPU status
    if gpu_status["devices"]:
        gpu_table = Table(title="GPU Devices", box=box.ROUNDED)
        gpu_table.add_column("Index", justify="center")
        gpu_table.add_column("Name", style="cyan")
        gpu_table.add_column("Memory", justify="right")
        gpu_table.add_column("Allocated", justify="right")
        gpu_table.add_column("Temp", justify="right")
        gpu_table.add_column("Power", justify="right")
        
        for device in gpu_status["devices"]:
            gpu_table.add_row(
                str(device["index"]),
                device["name"],
                f"{device['memory_total_gb']:.1f} GB",
                f"{device['allocation_percent']:.0f}%",
                f"{device['temperature_c']:.0f}°C" if device["temperature_c"] else "N/A",
                f"{device['power_draw_w']:.0f}W" if device["power_draw_w"] else "N/A"
            )
        
        console.print(gpu_table)


@resource_commands.command(name="allocate")
@click.option("--cpu", default=1.0, help="CPU cores required")
@click.option("--memory", default=1.0, help="Memory in GB")
@click.option("--gpu", default=0, help="Number of GPUs")
@click.option("--gpu-memory", default=0.0, help="GPU memory in GB")
@click.option("--quality", default="standard", help="Quality level")
@click.option("--task-id", required=True, help="Task identifier")
@click.option("--duration", default=300, help="Duration estimate in seconds")
@click.option("--strategy", type=click.Choice(["best_fit", "first_fit", "load_balance", "pack", "spread"]), 
              default="load_balance", help="Allocation strategy")
def allocate_resources(cpu: float, memory: float, gpu: int, gpu_memory: float,
                      quality: str, task_id: str, duration: int, strategy: str):
    """Allocate resources for a task"""
    
    async def _allocate():
        # Initialize components
        resource_mapper = ResourceMapper(AllocationStrategy(strategy))
        gpu_manager = GPUResourceManager()
        await resource_mapper.start()
        await gpu_manager.start()
        
        try:
            # Create resource spec
            base_requirements = ResourceSpec(
                cpu_cores=cpu,
                memory_gb=memory,
                gpu_count=gpu,
                gpu_memory_gb=gpu_memory
            )
            
            # Scale for quality
            scaler = QualityResourceScaler()
            requirements = scaler.scale_requirements(base_requirements, quality)
            
            # Find worker
            worker_id = await resource_mapper.find_worker(requirements)
            
            if not worker_id:
                console.print("[red]Error:[/red] No suitable worker found")
                return None
            
            # Allocate resources
            allocation = await resource_mapper.allocate(
                worker_id=worker_id,
                requirements=requirements,
                task_id=task_id,
                duration_estimate=duration
            )
            
            # Allocate GPU if needed
            if requirements.gpu_count > 0:
                gpu_devices = await gpu_manager.allocate_multi_gpu(
                    count=requirements.gpu_count,
                    memory_per_gpu_gb=requirements.gpu_memory_gb / requirements.gpu_count
                )
                allocation.gpu_devices = gpu_devices or []
            
            return allocation
            
        finally:
            await resource_mapper.stop()
            await gpu_manager.stop()
    
    with console.status("Allocating resources..."):
        allocation = asyncio.run(_allocate())
    
    if allocation:
        console.print(Panel.fit(
            f"[bold green]Allocation Successful[/bold green]\n"
            f"Allocation ID: {allocation.id}\n"
            f"Worker: {allocation.worker_id}\n"
            f"Resources: CPU={allocation.resources.cpu_cores:.1f}, "
            f"Memory={allocation.resources.memory_gb:.1f}GB\n"
            f"GPU Devices: {allocation.gpu_devices if allocation.gpu_devices else 'None'}\n"
            f"Expires: {allocation.expires_at.isoformat() if allocation.expires_at else 'Never'}",
            title="Resource Allocation",
            border_style="green"
        ))


@resource_commands.command(name="release")
@click.argument("allocation_id")
def release_resources(allocation_id: str):
    """Release allocated resources"""
    
    async def _release():
        resource_mapper = ResourceMapper()
        await resource_mapper.start()
        
        try:
            await resource_mapper.release(allocation_id)
            return True
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            return False
        finally:
            await resource_mapper.stop()
    
    with console.status("Releasing resources..."):
        success = asyncio.run(_release())
    
    if success:
        console.print(f"[green]✓[/green] Released allocation {allocation_id}")


@resource_commands.command(name="quality")
@click.argument("quality", default="all")
@click.option("--base-cpu", default=1.0, help="Base CPU cores")
@click.option("--base-memory", default=1.0, help="Base memory in GB")
@click.option("--base-gpu-memory", default=8.0, help="Base GPU memory in GB")
def show_quality_scaling(quality: str, base_cpu: float, base_memory: float, base_gpu_memory: float):
    """Show quality level scaling information"""
    
    scaler = QualityResourceScaler()
    
    if quality == "all":
        # Show all quality levels
        qualities = ["draft", "standard", "high", "ultra"]
    else:
        qualities = [quality]
    
    base_spec = ResourceSpec(
        cpu_cores=base_cpu,
        memory_gb=base_memory,
        gpu_count=1,
        gpu_memory_gb=base_gpu_memory
    )
    
    table = Table(title="Quality Level Resource Scaling", box=box.ROUNDED)
    table.add_column("Quality", style="cyan")
    table.add_column("CPU Cores", justify="right")
    table.add_column("Memory (GB)", justify="right")
    table.add_column("GPU Memory (GB)", justify="right")
    table.add_column("Time Factor", justify="right")
    table.add_column("Priority", justify="center")
    
    for q in qualities:
        info = scaler.get_quality_info(q)
        if not info["valid"]:
            console.print(f"[red]Error:[/red] {info['error']}")
            continue
        
        scaled = scaler.scale_requirements(base_spec, q)
        multipliers = info["multipliers"]
        
        table.add_row(
            q.capitalize(),
            f"{scaled.cpu_cores:.1f}",
            f"{scaled.memory_gb:.1f}",
            f"{scaled.gpu_memory_gb:.1f}",
            f"{multipliers['time']:.1f}x",
            str(info["priority"])
        )
    
    console.print(table)
    
    # Show descriptions
    console.print("\n[bold]Quality Level Descriptions:[/bold]")
    for q in qualities:
        info = scaler.get_quality_info(q)
        if info["valid"]:
            console.print(f"• [cyan]{q.capitalize()}:[/cyan] {info['description']}")


@resource_commands.command(name="metrics")
@click.option("--duration", default=60, help="Duration in minutes")
@click.option("--worker", help="Specific worker ID")
def show_metrics(duration: int, worker: Optional[str]):
    """Show resource utilization metrics"""
    
    async def _get_metrics():
        resource_mapper = ResourceMapper()
        monitor = ResourceMonitor(resource_mapper)
        
        await monitor.start()
        await asyncio.sleep(1)  # Let it collect some data
        
        try:
            summary = await monitor.get_utilization_summary()
            trends = await monitor.get_resource_trends(duration)
            
            return summary, trends
            
        finally:
            await monitor.stop()
    
    with console.status("Collecting metrics..."):
        summary, trends = asyncio.run(_get_metrics())
    
    # Display summary
    console.print(Panel.fit(
        f"[bold]Utilization Summary[/bold]\n"
        f"Workers: {summary.get('workers', 0)}\n"
        f"Average CPU: {summary.get('average_cpu_percent', 0):.1f}%\n"
        f"Average Memory: {summary.get('average_memory_percent', 0):.1f}%\n"
        f"Average GPU: {summary.get('average_gpu_percent', 0):.1f}%\n"
        f"GPU Workers: {summary.get('gpu_workers', 0)}",
        title="Resource Metrics",
        border_style="blue"
    ))
    
    # Display trends if available
    if trends["trends"]["cpu"]:
        console.print("\n[bold]CPU Usage Trend:[/bold]")
        for point in trends["trends"]["cpu"][-5:]:  # Last 5 points
            timestamp = datetime.fromisoformat(point["timestamp"]).strftime("%H:%M:%S")
            value = point["value"]
            bar = "█" * int(value / 5)  # Simple bar chart
            console.print(f"{timestamp} [{bar:<20}] {value:.1f}%")


@resource_commands.command(name="predict")
@click.argument("task_type")
def predict_resources(task_type: str):
    """Predict resource needs for a task type"""
    
    async def _predict():
        resource_mapper = ResourceMapper()
        monitor = ResourceMonitor(resource_mapper)
        
        prediction = await monitor.predict_resource_needs(task_type)
        return prediction
    
    with console.status("Analyzing historical data..."):
        prediction = asyncio.run(_predict())
    
    if not prediction:
        console.print(f"[yellow]Warning:[/yellow] Insufficient data to predict resources for '{task_type}'")
        return
    
    console.print(Panel.fit(
        f"[bold]Resource Prediction for {task_type}[/bold]\n"
        f"CPU Cores: {prediction.predicted_resources.cpu_cores:.1f}\n"
        f"Memory: {prediction.predicted_resources.memory_gb:.1f} GB\n"
        f"GPU: {prediction.predicted_resources.gpu_count}\n"
        f"GPU Memory: {prediction.predicted_resources.gpu_memory_gb:.1f} GB\n"
        f"Confidence: {prediction.confidence:.0%}\n"
        f"Based on: {prediction.based_on_samples} samples\n"
        f"Est. Duration: {prediction.predicted_duration_seconds:.0f} seconds",
        title="Resource Prediction",
        border_style="green" if prediction.confidence > 0.7 else "yellow"
    ))