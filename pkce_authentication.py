import json
import jwt
import boto3
import logging
import requests
from jwt import PyJWKClient

# Setup Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Clients
cognito = boto3.client('cognito-idp')
dynamodb = boto3.client('dynamodb')
s3 = boto3.client('s3')

# Constants (Placeholders for sensitive information)
USER_POOL_ID = "<USER_POOL_ID>"
COGNITO_REGION = "<COGNITO_REGION>"
APP_CLIENT_ID = "<APP_CLIENT_ID>"
COGNITO_TOKEN_URL = f"https://login.example.com/oauth2/token"
COGNITO_JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
DYNAMODB_TABLE_NAME = "<DYNAMODB_TABLE_NAME>"
S3_BUCKET_NAME = "<S3_BUCKET_NAME>"

# Helper Functions
def validate_id_token(token):
    """ Validates JWT ID Token against Cognito JWKs """
    try:
        jwk_client = PyJWKClient(COGNITO_JWKS_URL)
        signing_key = jwk_client.get_signing_key_from_jwt(token).key

        decoded_token = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=APP_CLIENT_ID,
            options={"verify_aud": True} 
        )

        username = decoded_token.get("cognito:username", decoded_token.get("sub", "unknown_user"))
        return True, decoded_token, username

    except jwt.ExpiredSignatureError:
        return False, {}, "unknown_user"
    except jwt.InvalidTokenError:
        return False, {}, "unknown_user"
    except Exception as e:
        return False, {}, "unknown_user"

def exchange_code_for_tokens(auth_code, code_verifier):
    """ Exchanges Authorization Code for Tokens via Cognito """
    try:
        data = {
            "grant_type": "authorization_code",
            "client_id": APP_CLIENT_ID,
            "code": auth_code,
            "redirect_uri": "http://localhost/redirect.html",
            "code_verifier": code_verifier
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(COGNITO_TOKEN_URL, data=data, headers=headers)

        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def get_user_cognito_attributes(access_token):
    """ Fetches user attributes from Cognito """
    try:
        response = cognito.get_user(AccessToken=access_token)
        attributes = {attr["Name"]: attr["Value"] for attr in response["UserAttributes"]}
        return attributes, attributes.get("profile", "unknown_user")
    except Exception:
        return {}, "unknown_user"

def get_user_dynamodb_data(username):
    """ Fetches user-related data from DynamoDB """
    try:
        response = dynamodb.get_item(
            TableName=DYNAMODB_TABLE_NAME,
            Key={"TS_user_id": {"S": username}}
        )
        user_data = response.get("Item", {})
        return {k: list(v.values())[0] for k, v in user_data.items()} if user_data else {}
    except Exception:
        return {}

def generate_response(status_code, body, access_token=None, refresh_token=None):
    """ Returns API response with proper headers & cookies """
    if access_token:
        body["access_token"] = access_token
    if refresh_token:
        body["refresh_token"] = refresh_token
    response = {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    }
    if refresh_token:
        response["multiValueHeaders"] = {
            "Set-Cookie": [
                f"refresh_token={refresh_token}; Path=/; Max-Age=2592000; SameSite=None; Secure",
                f"has_refresh_token=true; Path=/; Max-Age=2592000; SameSite=None; Secure"
            ]
        }
    return response

def handle_login(event):
    """ Handles User Login Flow """
    try:
        body = json.loads(event.get("body", "{}"))
        authorization_code = body.get("authorization_code")
        code_verifier = body.get("code_verifier")
        if not authorization_code or not code_verifier:
            return generate_response(400, {"error": "Missing authorization code or verifier"})

        tokens = exchange_code_for_tokens(authorization_code, code_verifier)
        if not tokens:
            return generate_response(401, {"error": "Invalid authorization code"})

        id_token = tokens.get("id_token")
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        is_valid, decoded_id_token, username = validate_id_token(id_token)
        if not is_valid:
            return generate_response(401, {"error": "Invalid ID token"})

        email = decoded_id_token.get("email")
        return generate_response(
            200,
            {
                "message": "Login successful",
                "user_id": username,
                "email": email,
                "redirect": "http://localhost/dashboard"
            },
            access_token=access_token,
            refresh_token=refresh_token
        )
    except Exception:
        return generate_response(500, {"error": "Internal Server Error"})

def lambda_handler(event, context):
    """ Main Lambda Handler """
    http_method = event.get("httpMethod", "UNKNOWN")
    if http_method == "OPTIONS":
        return generate_response(200, {})
    if http_method == "POST":
        resource_path = event.get("resource", "Unknown")
        if resource_path == "/auth":
            return handle_login(event)
        return generate_response(404, {"error": "Resource Not Found"})
    return generate_response(405, {"error": "Method Not Allowed"})
