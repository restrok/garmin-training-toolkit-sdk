"""Tests for the Garmin provider interface and tool factory."""

from datetime import date
from typing import Any, List, Optional

from garmin_training_toolkit_sdk.core.base import (
    BaseBiometricProvider,
    SuccessReport,
)
from garmin_training_toolkit_sdk.core.factory import ToolFactory


def test_tool_factory() -> None:
    """Tests that the ToolFactory correctly generates tools from a provider."""

    # Mock a provider to test the factory
    class MockProvider(BaseBiometricProvider):
        """Mock implementation of BaseBiometricProvider for testing."""

        def get_activities(self, start_date: str, end_date: str) -> List[Any]:
            """Mock get_activities."""
            return []

        def get_telemetry(self, activity_id: int) -> Optional[Any]:
            """Mock get_telemetry."""
            return None

        def upload_training_plan(self, plan: Any) -> SuccessReport:
            """Mock upload_training_plan."""
            return SuccessReport(success=True, message="Done")

        def get_workout_templates(self) -> List[Any]:
            """Mock get_workout_templates."""
            return []

        def get_calendar_range(self, start_date: str, end_date: str) -> List[Any]:
            """Mock get_calendar_range."""
            return []

        def unschedule_workout(self, calendar_item_id: str) -> bool:
            """Mock unschedule_workout."""
            return True

        def delete_workout_template(self, workout_id: str) -> bool:
            """Mock delete_workout_template."""
            return True

        def get_sleep_history(self, start_date: str, end_date: str) -> List[Any]:
            """Mock get_sleep_history."""
            return []

        def get_hrv_history(self, start_date: str, end_date: str) -> List[Any]:
            """Mock get_hrv_history."""
            return []

        def get_user_profile(self) -> Optional[Any]:
            """Mock get_user_profile."""
            return None

    provider = MockProvider()
    tools = ToolFactory.create_tools(provider)

    # We now have 10 tools
    assert len(tools) == 10
    assert tools[0].name == "get_activities"
    assert tools[2].name == "upload_training_plan"
    assert tools[3].name == "get_workout_templates"
    assert tools[4].name == "get_calendar_range"
    assert tools[5].name == "unschedule_workout"
    assert tools[6].name == "delete_workout_template"
    assert tools[7].name == "get_sleep_history"
    assert tools[8].name == "get_hrv_history"
    assert tools[9].name == "get_user_profile"

    # Verify .run() attribute exists and is callable (for LangChain compatibility)
    assert hasattr(tools[0], "run")
    assert callable(tools[0].run)
    assert tools[0].run(date.today(), date.today()) == []


def test_protocol_import_path() -> None:
    """Verifies that models can be imported from the new protocol path."""
    from garmin_training_toolkit_sdk.protocol.activities import Activity

    assert Activity is not None
