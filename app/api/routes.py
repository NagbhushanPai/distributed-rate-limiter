"""API Routes for Rate Limiter"""

import logging
from flask import Blueprint, request, jsonify
from app.services.rate_limiter import RateLimiterService
from app.core.constants import (
    ERROR_INVALID_USER_ID,
    ERROR_INVALID_TOKENS,
    STATUS_OK,
    STATUS_BAD_REQUEST,
    STATUS_SERVER_ERROR
)

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

# Initialize rate limiter service
rate_limiter = RateLimiterService()


@api_bp.route('/allow', methods=['POST'])
def allow():
    """
    Check if request is allowed under rate limit
    
    Query params or JSON:
        - user_id: Identifier (required)
        - tokens: Tokens to consume (optional, default: 1)
    """
    try:
        # Get parameters - use get_json() which safely returns None if no JSON
        json_data = request.get_json(silent=True) or {}
        user_id = request.args.get('user_id') or json_data.get('user_id')
        tokens = int(request.args.get('tokens', 1) or json_data.get('tokens', 1))
        
        if not user_id:
            return jsonify({"error": ERROR_INVALID_USER_ID}), STATUS_BAD_REQUEST
        
        if tokens < 1:
            return jsonify({"error": ERROR_INVALID_TOKENS}), STATUS_BAD_REQUEST
        
        result = rate_limiter.is_allowed(user_id, tokens)
        return jsonify(result), STATUS_OK
    
    except Exception as e:
        logger.error(f"Error in /allow endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), STATUS_SERVER_ERROR


@api_bp.route('/status', methods=['GET'])
def status():
    """Get rate limiter status"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": ERROR_INVALID_USER_ID}), STATUS_BAD_REQUEST
        
        status_info = rate_limiter.get_status(user_id)
        if status_info is None:
            return jsonify({"error": "Error retrieving status"}), STATUS_SERVER_ERROR
        
        return jsonify(status_info), STATUS_OK
    
    except Exception as e:
        logger.error(f"Error in /status endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), STATUS_SERVER_ERROR


@api_bp.route('/reset', methods=['POST'])
def reset():
    """Reset rate limiter"""
    try:
        user_id = request.args.get('user_id') or (request.json.get('user_id') if request.json else None)
        
        if not user_id:
            return jsonify({"error": ERROR_INVALID_USER_ID}), STATUS_BAD_REQUEST
        
        success = rate_limiter.reset(user_id)
        return jsonify({"success": success}), STATUS_OK
    
    except Exception as e:
        logger.error(f"Error in /reset endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), STATUS_SERVER_ERROR


@api_bp.route('/health', methods=['GET'])
def health():
    """Health check"""
    try:
        from app.redis.client import redis_client
        redis_client.ping()
        return jsonify({"status": "healthy"}), STATUS_OK
    except:
        return jsonify({"status": "unhealthy"}), 503


@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), STATUS_SERVER_ERROR
