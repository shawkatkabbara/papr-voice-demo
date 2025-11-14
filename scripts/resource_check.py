#!/usr/bin/env python3
"""
Resource checking utility for deciding between CoreML on-device vs API backend processing.

Usage:
    from resource_check import should_use_ondevice_processing

    can_use, reason = should_use_ondevice_processing()
    if can_use:
        print(f"✅ Using CoreML on-device: {reason}")
    else:
        print(f"⚠️  Using API backend: {reason}")
"""

import shutil
import psutil
import os


def get_disk_space_gb(path="/"):
    """
    Get free disk space in GB for the given path.

    Args:
        path: Path to check (default: root "/" for macOS/Linux)

    Returns:
        float: Free space in GB
    """
    try:
        usage = shutil.disk_usage(path)
        return usage.free / (1024**3)
    except Exception as e:
        print(f"Warning: Could not get disk space: {e}")
        return 0


def get_available_ram_gb():
    """
    Get available RAM in GB.

    Returns:
        tuple: (available_gb: float, used_percent: float)
    """
    try:
        mem = psutil.virtual_memory()
        return mem.available / (1024**3), mem.percent
    except Exception as e:
        print(f"Warning: Could not get memory info: {e}")
        return 0, 100


def should_use_ondevice_processing(
    min_disk_gb=30,
    min_ram_gb=6,
    max_memory_pressure_percent=85,
    verbose=True
):
    """
    Determines if system has enough resources for CoreML on-device processing.

    CoreML requires:
    - 30GB+ free disk space for ANE compilation artifacts
    - 6GB+ available RAM for model runtime
    - <85% memory pressure to avoid swapping

    Args:
        min_disk_gb: Minimum free disk space in GB (default: 30)
        min_ram_gb: Minimum available RAM in GB (default: 6)
        max_memory_pressure_percent: Maximum memory usage % (default: 85)
        verbose: Print detailed status (default: True)

    Returns:
        tuple: (should_use_ondevice: bool, reason: str)
    """
    checks = []

    # Check disk space
    free_gb = get_disk_space_gb()
    disk_ok = free_gb >= min_disk_gb
    checks.append({
        "name": "Disk Space",
        "ok": disk_ok,
        "value": f"{free_gb:.1f}GB free",
        "required": f"{min_disk_gb}GB+"
    })

    # Check available RAM
    available_gb, memory_percent = get_available_ram_gb()
    ram_ok = available_gb >= min_ram_gb
    checks.append({
        "name": "Available RAM",
        "ok": ram_ok,
        "value": f"{available_gb:.1f}GB available",
        "required": f"{min_ram_gb}GB+"
    })

    # Check memory pressure
    pressure_ok = memory_percent <= max_memory_pressure_percent
    checks.append({
        "name": "Memory Pressure",
        "ok": pressure_ok,
        "value": f"{memory_percent:.1f}% used",
        "required": f"<{max_memory_pressure_percent}%"
    })

    # Determine if we should use on-device
    all_ok = all(check["ok"] for check in checks)

    # Build detailed reason
    if all_ok:
        reason = "System has sufficient resources for CoreML on-device processing"
    else:
        failed = [c for c in checks if not c["ok"]]
        failures = ", ".join([f"{c['name']}: {c['value']} (need {c['required']})" for c in failed])
        reason = f"Insufficient resources: {failures}"

    if verbose:
        print("\n" + "=" * 80)
        print("🔍 RESOURCE CHECK FOR COREML ON-DEVICE PROCESSING")
        print("=" * 80)
        for check in checks:
            status = "✅" if check["ok"] else "❌"
            print(f"{status} {check['name']}: {check['value']} (need {check['required']})")
        print("-" * 80)
        if all_ok:
            print(f"✅ DECISION: Use CoreML on-device processing")
        else:
            print(f"⚠️  DECISION: Use API backend (falling back due to resource constraints)")
        print(f"   Reason: {reason}")
        print("=" * 80 + "\n")

    return all_ok, reason


def configure_processing_mode():
    """
    Automatically configure PAPR_ONDEVICE_PROCESSING based on system resources.
    Sets environment variable and returns the decision.

    Returns:
        tuple: (using_ondevice: bool, reason: str)
    """
    can_use_ondevice, reason = should_use_ondevice_processing(verbose=True)

    if can_use_ondevice:
        os.environ["PAPR_ONDEVICE_PROCESSING"] = "true"
        print("🚀 Configured for CoreML on-device processing")
    else:
        os.environ["PAPR_ONDEVICE_PROCESSING"] = "false"
        print("☁️  Configured for API backend processing")

    return can_use_ondevice, reason


if __name__ == "__main__":
    # Run as standalone script to check resources
    print("\n🔍 Checking system resources for CoreML on-device processing...\n")

    can_use, reason = should_use_ondevice_processing(verbose=True)

    if can_use:
        print("\n✅ Recommendation: Enable CoreML on-device processing")
        print("   Set in .env: PAPR_ONDEVICE_PROCESSING=true")
    else:
        print("\n⚠️  Recommendation: Use API backend processing")
        print("   Set in .env: PAPR_ONDEVICE_PROCESSING=false")
        print(f"\n💡 To enable on-device processing:")
        print("   1. Free up disk space (need 30GB+)")
        print("   2. Close memory-intensive applications")
        print("   3. Consider upgrading RAM if <16GB total")
