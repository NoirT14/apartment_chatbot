"""
JWT Authentication Middleware
Extract token từ request, verify và set schema vào context
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
import logging

from auth.jwt_handler import verify_keycloak_token, extract_building_id, get_schema_from_building_id
from schema.schema_context import set_current_schema, clear_schema, get_current_schema

logger = logging.getLogger(__name__)

# Public endpoints không cần authentication
PUBLIC_ENDPOINTS = [
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc"
]


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware để xử lý JWT authentication và set schema context
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request:
        1. Check nếu là public endpoint → skip auth
        2. Extract token từ Authorization header
        3. Verify token và extract building_id
        4. Map building_id → schema_name
        5. Set schema vào context
        """
        # Skip authentication cho public endpoints
        if request.url.path in PUBLIC_ENDPOINTS:
            clear_schema()
            return await call_next(request)
        
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            # Không có token → Set schema = None
            logger.info("No Authorization header found, setting schema to None")
            clear_schema()
            request.state.is_authenticated = False
            request.state.schema_name = None
            request.state.building_id = None
        else:
            # Có token → Verify và extract
            token = auth_header.split(" ")[1]
            
            try:
                # Verify token
                payload = verify_keycloak_token(token)
                
                # Extract building_id
                building_id = extract_building_id(payload)
                
                if building_id:
                    # Map building_id → schema_name
                    schema_name = get_schema_from_building_id(building_id)
                    
                    # Set vào context
                    set_current_schema(schema_name)
                    
                    # Store trong request state
                    request.state.is_authenticated = True
                    request.state.schema_name = schema_name
                    request.state.building_id = building_id
                    request.state.user_info = payload
                    
                    logger.info(f"Authenticated user with building_id: {building_id}, schema: {schema_name}")
                else:
                    # Token không có building_id
                    logger.warning("Token does not contain building_id")
                    clear_schema()
                    request.state.is_authenticated = False
                    request.state.schema_name = None
                    request.state.building_id = None
                    
            except ValueError as e:
                # Token invalid/expired
                logger.warning(f"Token validation failed: {str(e)}")
                clear_schema()
                request.state.is_authenticated = False
                request.state.schema_name = None
                request.state.building_id = None
            except Exception as e:
                # Unexpected error
                logger.error(f"Unexpected error in auth middleware: {str(e)}")
                clear_schema()
                request.state.is_authenticated = False
                request.state.schema_name = None
                request.state.building_id = None
        
        # Continue với request
        response = await call_next(request)
        return response

