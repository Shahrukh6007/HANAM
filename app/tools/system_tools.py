import platform
import os
import subprocess

def get_system_info() -> str:
    """Get basic information about the computer running HANAM."""
    total_memory = None

    try:
        import psutil
        total_memory = psutil.virtual_memory().total / (1024 ** 3)
    except ImportError:
        pass

    memory_info = (
        f"RAM: {total_memory:.1f} GB"
        if total_memory
        else "RAM: Information unavailable"
    )

    gpu_info = "GPU: Information unavailable"

    try:
        result = subprocess.run(
            [
                "powershell",
                "-Command",
                "Get-CimInstance Win32_VideoController | "
                "Select-Object -ExpandProperty Name"
            ],
            capture_output=True,
            text=True,
            timeout=5
        )

        gpus = [
            gpu.strip()
            for gpu in result.stdout.splitlines()
            if gpu.strip()
        ]

        if gpus:
            gpu_info = "GPU:\n" + "\n".join(f"- {gpu}" for gpu in gpus)
    except Exception:
        pass

    return (
        f"Operating System: {platform.system()} {platform.release()}\n"
        f"Machine: {platform.machine()}\n"
        f"Processor: {platform.processor()}\n"
        f"CPU Cores: {os.cpu_count()}\n"
        f"{memory_info}\n"
        f"{gpu_info}\n"
        f"Python Version: {platform.python_version()}"
    )
