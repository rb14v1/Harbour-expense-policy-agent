import logging
import jwt
from django.conf import settings
from functools import wraps
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class TeamsAuthValidator:
    """
    Validates Teams bot authentication.
    Verifies bot ID and optional JWT token.
    """

    TEAMS_ISSUER = "https://api.botframework.com"
    MICROSOFT_OPENID_CONFIG = "https://login.botframework.com/.well-known/openidconfiguration"

    @staticmethod
    def verify_teams_request(request):
        """
        Verify incoming Teams request is legitimate.
        Checks:
        1. Authorization header present
        2. Bot ID matches configured ID
        """
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header.startswith("Bearer "):
            return False, "Missing or invalid authorization header"

        token = auth_header[7:]

        try:
            if settings.DEBUG:
                logger.info("Skipping Teams token validation in DEBUG mode")
                return True, "OK"

            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )

            bot_id = payload.get("aud")
            configured_id = settings.TEAMS_APP_ID

            if bot_id != configured_id:
                logger.warning(f"Bot ID mismatch: {bot_id} != {configured_id}")
                return False, "Bot ID mismatch"

            return True, "OK"

        except jwt.InvalidTokenError as e:
            logger.error(f"Token validation failed: {str(e)}")
            return False, "Invalid token"

        except Exception as e:
            logger.error(f"Auth validation error: {str(e)}")
            return False, "Auth error"

    @staticmethod
    def validate_teams_activity(activity: dict) -> tuple:
        """
        Validate Teams activity structure.
        Ensures required fields are present.
        """
        required_fields = ["type", "channelId"]

        for field in required_fields:
            if field not in activity:
                return False, f"Missing required field: {field}"

        activity_type = activity.get("type")
        valid_types = ["message", "conversationUpdate", "invoke"]

        if activity_type not in valid_types:
            return False, f"Invalid activity type: {activity_type}"

        return True, "OK"


def require_teams_auth(view_func):
    """
    Decorator to require Teams authentication on a view.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        is_valid, message = TeamsAuthValidator.verify_teams_request(request)

        if not is_valid:
            logger.warning(f"Teams auth failed: {message}")
            return Response(
                {"error": message},
                status=status.HTTP_401_UNAUTHORIZED
            )

        return view_func(request, *args, **kwargs)

    return wrapper


def validate_teams_activity(view_func):
    """
    Decorator to validate Teams activity structure.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        activity = request.data

        is_valid, message = TeamsAuthValidator.validate_teams_activity(activity)

        if not is_valid:
            logger.warning(f"Activity validation failed: {message}")
            return Response(
                {"error": message},
                status=status.HTTP_400_BAD_REQUEST
            )

        return view_func(request, *args, **kwargs)

    return wrapper


def require_finance_auth(view_func):
    """
    Decorator to require Finance Department authorization on a view.
    Checks if the user belongs to the Finance Department.
    Handles both regular view functions and viewset methods.
    """
    @wraps(view_func)
    def wrapper(self_or_request, *args, **kwargs):
        # Determine if this is a viewset method (self, request, ...) or regular view (request, ...)
        if hasattr(self_or_request, 'request'):
            # This is a viewset method, self_or_request is the viewset (self)
            request = self_or_request.request
            # Insert self back as first argument
            actual_args = (self_or_request,) + args
        else:
            # This is a regular view function
            request = self_or_request
            actual_args = args

        # Get the owner/department from request
        owner = request.query_params.get('owner') or request.data.get('owner', '')

        # Check if user is part of finance-department
        if owner != 'finance-department':
            logger.warning(f"Finance auth failed: user {owner} is not finance-department")
            return Response(
                {"error": "Unauthorized. Finance Department access required."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Call the view function with appropriate arguments
        if hasattr(self_or_request, 'request'):
            return view_func(self_or_request, *args, **kwargs)
        else:
            return view_func(self_or_request, *args, **kwargs)

    return wrapper
