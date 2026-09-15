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
