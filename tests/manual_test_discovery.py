#!/usr/bin/env python3
"""Manual test script for service discovery functionality.

This script can be run standalone to test service discovery without Blender.
Usage: ./scripts/run-script.sh tests/manual_test_discovery.py
"""

import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from blender_movie_director.backend.service_discovery import ServiceDiscoveryManager, ServiceInfo

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def print_service_info(service_info: ServiceInfo):
    """Pretty print service information."""
    status = "✅ Available" if service_info.is_available else "❌ Not Available"
    print(f"\n  {service_info.name}: {status}")
    print(f"    URL: {service_info.protocol}://{service_info.host}:{service_info.port}")

    if service_info.is_available:
        print(f"    Version: {service_info.version or 'unknown'}")
        if service_info.capabilities:
            print(f"    Capabilities: {', '.join(service_info.capabilities)}")
    else:
        print(f"    Error: {service_info.error_message}")


async def test_service_discovery():
    """Test service discovery functionality."""
    print("🔍 Starting service discovery test...\n")

    # Create discovery manager
    discovery_manager = ServiceDiscoveryManager()

    # Test 1: Basic discovery
    print("Test 1: Discovering all services on default ports")
    print("-" * 50)

    results = await discovery_manager.discover_all_services()

    print(f"\nDiscovered {len(results)} services:")
    for _service_name, service_info in results.items():
        print_service_info(service_info)

    # Test 2: Custom ports
    print("\n\nTest 2: Testing with custom ports")
    print("-" * 50)

    custom_ports = {"comfyui": 8080, "wan2gp": 7777}

    print(f"Custom ports: {custom_ports}")
    results = await discovery_manager.discover_all_services(custom_ports)

    print(f"\nDiscovered {len(results)} services:")
    for service_name, service_info in results.items():
        if service_name in custom_ports:
            print_service_info(service_info)

    # Test 3: Available services
    print("\n\nTest 3: Getting only available services")
    print("-" * 50)

    available = discovery_manager.get_available_services()
    print(f"\nAvailable services: {len(available)}")
    for service_name, _service_info in available.items():
        print(f"  - {service_name}: {discovery_manager.get_service_url(service_name)}")

    # Test 4: Refresh single service
    print("\n\nTest 4: Refreshing a single service")
    print("-" * 50)

    if "comfyui" in results:
        print("\nRefreshing ComfyUI...")
        refreshed = await discovery_manager.refresh_service("comfyui")
        if refreshed:
            print_service_info(refreshed)

    # Summary
    print("\n\n📊 Discovery Summary")
    print("-" * 50)
    available_count = len([s for s in results.values() if s.is_available])
    print(f"Total services: {len(results)}")
    print(f"Available: {available_count}")
    print(f"Unavailable: {len(results) - available_count}")


async def test_individual_service(service_name: str, port: int = None):
    """Test discovery of a specific service."""
    print(f"\n🔍 Testing {service_name} discovery...")

    discovery_manager = ServiceDiscoveryManager()

    if port:
        print(f"Using custom port: {port}")
        await discovery_manager.discover_all_services({service_name: port})
    else:
        await discovery_manager.refresh_service(service_name)

    service_info = discovery_manager.get_service_info(service_name)
    if service_info:
        print_service_info(service_info)
    else:
        print(f"❌ {service_name} not found")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test service discovery")
    parser.add_argument(
        "--service",
        choices=["comfyui", "wan2gp", "rvc", "audioldm"],
        help="Test a specific service",
    )
    parser.add_argument("--port", type=int, help="Custom port for the service")

    args = parser.parse_args()

    # Run appropriate test
    if args.service:
        asyncio.run(test_individual_service(args.service, args.port))
    else:
        asyncio.run(test_service_discovery())

    print("\n✅ Test complete!")


if __name__ == "__main__":
    main()
