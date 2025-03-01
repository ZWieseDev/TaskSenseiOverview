import json
import boto3
import jwt
from jwt import PyJWKClient
import os

# ✅ Initialize AWS Clients
cognito_client = boto3.client("cognito-idp")
dynamodb = boto3.client("dynamodb")

# ✅ Environment Variables (Placeholders for Security)
USER_POOL_ID = os.getenv("USER_POOL_ID", "<COGNITO_USER_POOL_ID>")
COGNITO_REGION = os.getenv("COGNITO_REGION", "<AWS_REGION>")
COGNITO_JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "<DYNAMODB_USERS_TABLE>")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID", "<COGNITO_APP_CLIENT>")

# ✅ Main Lambda Handler
def lambda_handler(event, context):
    """ ✅ Handles updating user profile information """
    try:
        headers = event.get("headers", {})
        access_token = headers.get("Authorization")
        
        if not access_token:
            return {"statusCode": 401, "body": json.dumps({"error": "Unauthorized - Missing Token"})}

        # ✅ Validate Access Token
        user_id, error = validate_access_token(access_token)
        if error:
            return {"statusCode": 401, "body": json.dumps({"error": error})}

        # ✅ Extract request body
        body = json.loads(event.get("body", "{}"))
        allowed_updates = ["name", "email", "phone_number", "custom:subscription_status"]
        updates = {key: value for key, value in body.items() if key in allowed_updates}

        if not updates:
            return {"statusCode": 400, "body": json.dumps({"error": "No valid fields to update."})}

        # ✅ Update Cognito User Attributes
        update_cognito_user(user_id, updates)

        # ✅ (Optional) Update DynamoDB if extra metadata is stored
        if "extra_data" in body:
            update_dynamodb_user(user_id, body["extra_data"])

        return {"statusCode": 200, "body": json.dumps({"message": "User profile updated successfully!"})}
    
    except Exception:
        return {"statusCode": 500, "body": json.dumps({"error": "Internal Server Error"})}

# ✅ Function to Validate the Access Token
def validate_access_token(token):
    """ ✅ Validates Cognito access token and extracts the user ID. """
    try:
        jwk_client = PyJWKClient(COGNITO_JWKS_URL)
        signing_key = jwk_client.get_signing_key_from_jwt(token).key

        decoded_token = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            options={"verify_aud": True},
        )
        return decoded_token.get("sub"), None
    except jwt.ExpiredSignatureError:
        return None, "Token expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"

# ✅ Function to Update Cognito User Attributes
def update_cognito_user(user_id, updates):
    """ ✅ Updates user attributes in Cognito. """
    attribute_list = [{"Name": key, "Value": value} for key, value in updates.items()]
    
    cognito_client.admin_update_user_attributes(
        UserPoolId=USER_POOL_ID,
        Username=user_id,
        UserAttributes=attribute_list
    )

# ✅ Function to Update DynamoDB (Optional)
def update_dynamodb_user(user_id, extra_data):
    """ ✅ Updates user data in DynamoDB if needed. """
    dynamodb.update_item(
        TableName=TABLE_NAME,
        Key={"user_id": {"S": user_id}},
        UpdateExpression="SET extra_data = :data",
        ExpressionAttributeValues={":data": {"S": json.dumps(extra_data)}}
    )
