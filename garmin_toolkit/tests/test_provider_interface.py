import pytest
from datetime import date
from garmin_training_toolkit_sdk.core.base import BaseBiometricProvider, SuccessReport
from garmin_training_toolkit_sdk.core.garmin import GarminProvider
from garmin_training_toolkit_sdk.core.factory import ToolFactory
from garmin_training_toolkit_sdk.protocol.workouts import WorkoutPlan, create_simple_hr_workout

def test_provider_interface():
    # Check if GarminProvider correctly implements the ABC
    # We won't instantiate it with a real client here to avoid auth errors in CI,
    # but we can check if it has the required methods.
    assert issubclass(GarminProvider, BaseBiometricProvider)

def test_tool_factory():
    # Mock a provider to test the factory
    class MockProvider(BaseBiometricProvider):
        def get_activities(self, start_date, end_date): return []
        def get_telemetry(self, activity_id): return None
        def upload_training_plan(self, plan): return SuccessReport(success=True, message="Done")
        def get_calendar_range(self, start_date, end_date): return []

    provider = MockProvider()
    tools = ToolFactory.create_tools(provider)

    assert len(tools) == 3
    assert tools[0].name == "get_activities"
    assert tools[2].name == "upload_training_plan"

    # Verify .run() attribute exists and is callable (for LangChain compatibility)
    assert hasattr(tools[0], "run")
    assert callable(tools[0].run)
    assert tools[0].run(date.today(), date.today()) == []
    assert tools[2].name == "upload_training_plan"

def test_protocol_import_path():
    # Verify we can import from the new protocol path
    from garmin_training_toolkit_sdk.protocol.activities import Activity
    assert Activity is not None
