from datetime import date
from garmin_training_toolkit_sdk.core.base import BaseBiometricProvider, SuccessReport
from garmin_training_toolkit_sdk.core.factory import ToolFactory

def test_tool_factory():
    # Mock a provider to test the factory
    class MockProvider(BaseBiometricProvider):
        def get_activities(self, start_date, end_date): return []
        def get_telemetry(self, activity_id): return None
        def upload_training_plan(self, plan): return SuccessReport(success=True, message="Done")
        def get_calendar_range(self, start_date, end_date): return []
        def unschedule_workout(self, calendar_item_id): return True
        def delete_workout_template(self, workout_id): return True
        def get_sleep_history(self, start_date, end_date): return []
        def get_hrv_history(self, start_date, end_date): return []
        def get_user_profile(self): return None

    provider = MockProvider()
    tools = ToolFactory.create_tools(provider)
    
    # We now have 9 tools (3 original + 1 calendar range + 2 deletion + 3 wellness)
    assert len(tools) == 9
    assert tools[0].name == "get_activities"
    assert tools[2].name == "upload_training_plan"
    assert tools[3].name == "get_calendar_range"
    assert tools[4].name == "unschedule_workout"
    assert tools[5].name == "delete_workout_template"
    assert tools[6].name == "get_sleep_history"
    assert tools[7].name == "get_hrv_history"
    assert tools[8].name == "get_user_profile"
    
    # Verify .run() attribute exists and is callable (for LangChain compatibility)
    assert hasattr(tools[0], "run")
    assert callable(tools[0].run)
    assert tools[0].run(date.today(), date.today()) == []

def test_protocol_import_path():
    # Verify we can import from the new protocol path
    from garmin_training_toolkit_sdk.protocol.activities import Activity
    assert Activity is not None
