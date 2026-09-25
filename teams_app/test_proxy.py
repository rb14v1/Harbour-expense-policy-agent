"""
Tests for Teams proxy endpoint.

Verifies that the Django proxy correctly forwards Authorization headers
to the FastAPI Teams SDK service.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from rest_framework import status


class TeamsMessagesProxyTests(TestCase):
    """Tests for teams_messages_proxy endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()
        self.proxy_url = '/api/messages'
        self.test_auth_header = 'Bearer test.jwt.token'

    @patch('teams_app.views.httpx.Client')
    @patch('teams_app.views.require_teams_auth')
    def test_authorization_header_forwarded_to_fastapi(self, mock_auth_decorator, mock_httpx_client):
        """Test that Authorization header is forwarded to FastAPI service."""
        # Mock the auth decorator to pass through without validation
        mock_auth_decorator.side_effect = lambda f: f

        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"status": "ok"}'
        mock_response.json.return_value = {"status": "ok"}

        # Mock the httpx client and its post method
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_httpx_client.return_value = mock_client_instance

        # Make request with Authorization header
        response = self.client.post(
            self.proxy_url,
            data='{"type": "message", "channelId": "test"}',
            content_type='application/json',
            HTTP_AUTHORIZATION=self.test_auth_header,
        )

        # Verify httpx.Client was used
        mock_httpx_client.assert_called_once()

        # Verify post was called with Authorization header
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args

        # Extract the headers parameter from the call
        self.assertIn('headers', call_args.kwargs, "headers parameter missing from httpx.Client.post()")
        self.assertIn('Authorization', call_args.kwargs['headers'], "Authorization not in headers")
        self.assertEqual(
            call_args.kwargs['headers']['Authorization'],
            self.test_auth_header,
            f"Authorization header mismatch. Expected: {self.test_auth_header}, Got: {call_args.kwargs['headers']['Authorization']}"
        )

        # Verify response is successful
        self.assertEqual(response.status_code, 200)

    @patch('teams_app.views.httpx.Client')
    @patch('teams_app.views.require_teams_auth')
    def test_no_authorization_header_sends_empty(self, mock_auth_decorator, mock_httpx_client):
        """Test that missing Authorization header results in empty headers dict."""
        # Mock the auth decorator to pass through
        mock_auth_decorator.side_effect = lambda f: f

        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"status": "ok"}'
        mock_response.json.return_value = {"status": "ok"}

        # Mock the httpx client
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_httpx_client.return_value = mock_client_instance

        # Make request WITHOUT Authorization header
        response = self.client.post(
            self.proxy_url,
            data='{"type": "message", "channelId": "test"}',
            content_type='application/json',
        )

        # Verify post was called with empty headers or no Authorization
        call_args = mock_client_instance.post.call_args
        if 'headers' in call_args.kwargs:
            # If headers dict exists, Authorization should not be in it or should be empty
            self.assertNotIn('Authorization', call_args.kwargs['headers'],
                           "Authorization should not be sent when header is missing")
        # Response should still succeed
        self.assertEqual(response.status_code, 200)

    @patch('teams_app.views.httpx.Client')
    @patch('teams_app.views.require_teams_auth')
    def test_fastapi_url_unchanged(self, mock_auth_decorator, mock_httpx_client):
        """Test that FastAPI URL is unchanged."""
        # Mock the auth decorator
        mock_auth_decorator.side_effect = lambda f: f

        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{}'
        mock_response.json.return_value = {}

        # Mock the httpx client
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_httpx_client.return_value = mock_client_instance

        # Make request
        self.client.post(
            self.proxy_url,
            data='{"type": "message", "channelId": "test"}',
            content_type='application/json',
            HTTP_AUTHORIZATION='Bearer token',
        )

        # Verify the URL is correct
        call_args = mock_client_instance.post.call_args
        self.assertEqual(call_args[0][0], 'http://localhost:8001/api/messages',
                        "FastAPI URL should remain unchanged")
