import json
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from teams_app.bot_handler import create_teams_bot
from teams_app.auth import require_teams_auth, validate_teams_activity

logger = logging.getLogger(__name__)


@api_view(['POST'])
@require_teams_auth
@validate_teams_activity
def teams_message_handler(request):
    """
    Main webhook endpoint for Teams bot messages.
    Receives activities from Teams and routes to bot handler.
    """
    try:
        activity = request.data

        if not activity:
            return Response({"status": "ok"}, status=status.HTTP_200_OK)

        activity_type = activity.get("type")
        logger.info(f"Received Teams activity: {activity_type}")

        bot = create_teams_bot()
        response = bot.handle_message(activity)

        if response:
            return Response(response, status=status.HTTP_200_OK)

        return Response({"status": "ok"}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in Teams message handler: {str(e)}")
        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def teams_file_upload_handler(request):
    """
    Handle file uploads from Teams.
    Receives file content and calls bot handler to process.
    """
    try:
        if 'file' not in request.FILES:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        file_obj = request.FILES['file']
        user_id = request.data.get('user_id', 'teams-user')

        file_content = file_obj.read()

        bot = create_teams_bot()
        response = bot.handle_file_upload(file_content, file_obj.name, user_id)

        return Response(response, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in Teams file upload handler: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def teams_receipt_status(request, receipt_id):
    """
    Get receipt status for Teams.
    Returns Adaptive Card formatted response.
    """
    try:
        bot = create_teams_bot()
        response = bot.get_receipt_status(receipt_id)

        return Response(response, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting receipt status for Teams: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def teams_health_check(request):
    """
    Health check endpoint for Teams bot.
    """
    return Response({
        "status": "ok",
        "service": "Expense Policy Agent Teams Bot",
        "version": "1.0.0"
    }, status=status.HTTP_200_OK)
