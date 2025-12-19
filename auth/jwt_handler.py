"""
JWT Token Handler
Xử lý verify và decode JWT token từ Keycloak
"""
import jwt
from typing import Optional, Dict
import os
from dotenv import load_dotenv

load_dotenv()

# Keycloak configuration từ environment variables
KEYCLOAK_URL = os.getenv('KEYCLOAK_URL', '')
KEYCLOAK_REALM = os.getenv('KEYCLOAK_REALM', '')
KEYCLOAK_PUBLIC_KEY = os.getenv('KEYCLOAK_PUBLIC_KEY', '')


def verify_keycloak_token(token: str) -> Dict:
    """
    Verify JWT token với Keycloak
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        jwt.ExpiredSignatureError: Token đã hết hạn
        jwt.InvalidTokenError: Token không hợp lệ
    """
    try:
        print(f"🔍 [JWT HANDLER] Attempting to decode token...")
        print(f"🔍 [JWT HANDLER] KEYCLOAK_PUBLIC_KEY exists: {bool(KEYCLOAK_PUBLIC_KEY)}")
        
        # Option 1: Verify với public key (nếu có)
        if KEYCLOAK_PUBLIC_KEY:
            print(f"🔍 [JWT HANDLER] Using public key verification")
            # Decode và verify token
            payload = jwt.decode(
                token,
                KEYCLOAK_PUBLIC_KEY,
                algorithms=['RS256'],
                options={"verify_signature": True}
            )
            print(f"✅ [JWT HANDLER] Token verified with public key")
            return payload
        
        # Option 2: Decode không verify (tạm thời cho development)
        # Trong production nên verify với Keycloak public key hoặc JWKS
        print(f"🔍 [JWT HANDLER] Using decode without verification (development mode)")
        payload = jwt.decode(
            token,
            options={"verify_signature": False}  # Tắt verify tạm thời
        )
        print(f"✅ [JWT HANDLER] Token decoded without verification")
        return payload
        
    except jwt.ExpiredSignatureError as e:
        print(f"❌ [JWT HANDLER] Token expired: {str(e)}")
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        print(f"❌ [JWT HANDLER] Invalid token: {str(e)}")
        raise ValueError(f"Invalid token: {str(e)}")
    except Exception as e:
        print(f"❌ [JWT HANDLER] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise ValueError(f"Error decoding token: {str(e)}")


def extract_building_id(token_payload: Dict) -> Optional[str]:
    """
    Extract building_id từ token payload
    
    Args:
        token_payload: Decoded JWT payload
        
    Returns:
        building_id hoặc None nếu không có
    """
    # building_id có thể ở trong:
    # - token_payload['building_id']
    # - token_payload['realm_access']['roles'] (nếu dùng roles)
    # - token_payload['resource_access'] (nếu dùng resource access)
    
    print(f"🔍 Searching for building_id in token payload...")
    print(f"🔍 Available keys: {list(token_payload.keys())}")
    
    building_id = token_payload.get('building_id')
    print(f"🔍 Direct 'building_id' field: {building_id}")
    
    # Nếu không có trực tiếp, check các field khác
    if not building_id:
        # Check trong custom claims
        custom_claims = token_payload.get('custom_claims', {})
        if custom_claims:
            building_id = custom_claims.get('building_id')
            print(f"🔍 Found in custom_claims: {building_id}")
        
        # Check trong resource_access
        if not building_id:
            resource_access = token_payload.get('resource_access', {})
            print(f"🔍 Checking resource_access: {resource_access}")
        
        # Check trong realm_access roles
        if not building_id:
            realm_access = token_payload.get('realm_access', {})
            roles = realm_access.get('roles', []) if isinstance(realm_access, dict) else []
            print(f"🔍 Checking realm_access roles: {roles}")
            
            # Có thể building_id là một role
            for role in roles:
                if 'building' in role.lower():
                    building_id = role
                    print(f"🔍 Found building_id in role: {building_id}")
                    break
    
    print(f"🏢 Final building_id: {building_id}")
    return building_id


def get_schema_from_building_id(building_id: str) -> str:
    """
    Map building_id thành schema name
    
    Theo yêu cầu: building_id = schema_name
    
    Args:
        building_id: Building ID từ token
        
    Returns:
        Schema name (hiện tại = building_id)
    """
    # Vì building_id = schema_name, nên return trực tiếp
    return building_id

