from typing import List, Callable
from .base import BaseBiometricProvider

class ProviderTool:
    """
    A generic wrapper that exposes provider methods as tools.
    Can be used by LangChain or other agent frameworks.
    """
    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func

    def __call__(self, *args, **kwargs):
        """Allow direct execution of the tool."""
        return self.func(*args, **kwargs)

    def run(self, *args, **kwargs):
        """Safety alias for execution, compatible with LangChain expectations."""
        return self.func(*args, **kwargs)

class ToolFactory:
    """
    Generates a standardized set of tools from any Biometric Provider.
    """
    @staticmethod
    def create_tools(provider: BaseBiometricProvider) -> List[ProviderTool]:
        return [
            ProviderTool(
                name="get_activities",
                description="Fetch activities from the provider within a date range (YYYY-MM-DD).",
                func=provider.get_activities
            ),
            ProviderTool(
                name="get_telemetry",
                description="Get detailed telemetry (HR, pace, power) for a specific activity ID.",
                func=provider.get_telemetry
            ),
            ProviderTool(
                name="upload_training_plan",
                description="Upload and schedule a structured training plan (workouts) to the provider device/account.",
                func=provider.upload_training_plan
            )
        ]
