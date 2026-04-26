import json
import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from garmin_training_toolkit_sdk.utils import get_authenticated_client, _refresh_garmin_session

class TestAuthSelfHealing(unittest.TestCase):
    def setUp(self):
        self.token_file = Path("test_tokens.json")
        self.tokens = {"di_token": "old_token", "di_refresh_token": "old_refresh_token"}

    @patch("garmin_training_toolkit_sdk.utils.find_token_file")
    @patch("garmin_training_toolkit_sdk.utils.save_tokens")
    @patch("garminconnect.Garmin")
    @patch("builtins.open", new_callable=mock_open, read_data='{"di_token": "old_token"}')
    @patch("pathlib.Path.exists")
    def test_get_authenticated_client_success_first_try(self, mock_exists, mock_file, mock_garmin, mock_save, mock_find):
        mock_exists.return_value = True
        mock_find.return_value = self.token_file
        
        # Mock client behavior
        client_instance = mock_garmin.return_value
        client_instance.get_userprofile_settings.return_value = {"displayName": "Test User"}
        
        client = get_authenticated_client(self.token_file)
        
        self.assertEqual(client, client_instance)
        client_instance.get_userprofile_settings.assert_called_once()
        # Should not have called refresh
        mock_save.assert_not_called()

    @patch("garmin_training_toolkit_sdk.utils.find_token_file")
    @patch("garmin_training_toolkit_sdk.utils.save_tokens")
    @patch("garminconnect.Garmin")
    @patch("builtins.open", new_callable=mock_open, read_data='{"di_token": "old_token"}')
    @patch("pathlib.Path.exists")
    def test_get_authenticated_client_self_healing_success(self, mock_exists, mock_file, mock_garmin, mock_save, mock_find):
        mock_exists.return_value = True
        mock_find.return_value = self.token_file
        
        # Mock client behavior: first instance fails with 401, second succeeds
        fail_client = MagicMock()
        fail_client.get_userprofile_settings.side_effect = Exception("401 Unauthorized")
        
        # Mock the refresh process
        # _refresh_garmin_session is called, it creates a new Garmin instance
        refresh_client = MagicMock()
        refresh_client.client.dumps.return_value = json.dumps({"di_token": "new_token"})
        
        # Success client after refresh
        success_client = MagicMock()
        success_client.get_userprofile_settings.return_value = {"displayName": "Test User"}
        
        # Garmin() calls
        # 1. First call in get_authenticated_client
        # 2. Second call in _refresh_garmin_session (iterating DI_CLIENT_IDS)
        # 3. Third call in get_authenticated_client after successful refresh
        mock_garmin.side_effect = [fail_client, refresh_client, success_client]
        
        client = get_authenticated_client(self.token_file)
        
        self.assertEqual(client, success_client)
        fail_client.get_userprofile_settings.assert_called_once()
        mock_save.assert_called_once()
        # success_client is just returned, not tested again in the implementation
        success_client.get_userprofile_settings.assert_not_called()

    @patch("garmin_training_toolkit_sdk.utils.find_token_file")
    @patch("garmin_training_toolkit_sdk.utils._refresh_garmin_session")
    @patch("garminconnect.Garmin")
    @patch("builtins.open", new_callable=mock_open, read_data='{"di_token": "old_token"}')
    @patch("pathlib.Path.exists")
    def test_get_authenticated_client_self_healing_fails(self, mock_exists, mock_file, mock_garmin, mock_refresh, mock_find):
        mock_exists.return_value = True
        mock_find.return_value = self.token_file
        
        # Mock client behavior: fails with 401
        fail_client = MagicMock()
        fail_client.get_userprofile_settings.side_effect = Exception("401 Unauthorized")
        mock_garmin.return_value = fail_client
        
        # Mock refresh failure
        mock_refresh.return_value = False
        
        with self.assertRaises(Exception) as cm:
            get_authenticated_client(self.token_file)
        
        self.assertIn("401 Unauthorized", str(cm.exception))
        mock_refresh.assert_called_once()

    @patch("garmin_training_toolkit_sdk.utils.save_tokens")
    @patch("garminconnect.Garmin")
    @patch("builtins.open", new_callable=mock_open, read_data='{"di_token": "old_token"}')
    @patch("pathlib.Path.exists")
    def test_refresh_garmin_session_iteration(self, mock_exists, mock_file, mock_garmin, mock_save):
        mock_exists.return_value = True
        
        # Mock behavior: first 2 IDs fail, 3rd succeeds
        client1 = MagicMock()
        client1.client._refresh_di_token.side_effect = Exception("Failed")
        client2 = MagicMock()
        client2.client._refresh_di_token.side_effect = Exception("Failed")
        client3 = MagicMock()
        client3.client.dumps.return_value = json.dumps({"di_token": "new_token"})
        
        mock_garmin.side_effect = [client1, client2, client3]
        
        result = _refresh_garmin_session(self.token_file)
        
        self.assertTrue(result)
        self.assertEqual(mock_garmin.call_count, 3)
        self.assertEqual(client3.client.di_client_id, "GARMIN_CONNECT_MOBILE_ANDROID_DI") # 3rd ID in DI_CLIENT_IDS
        mock_save.assert_called_once()

if __name__ == "__main__":
    unittest.main()
