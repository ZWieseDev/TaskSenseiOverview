import json
import boto3
import requests
from datetime import datetime, timedelta, timezone

# ✅ Initialize AWS Clients
dynamodb = boto3.resource("dynamodb")
secrets_manager = boto3.client("secretsmanager")

# ✅ Table and Secrets (Placeholders for Security)
TABLE_NAME = "<DYNAMODB_TABLE_NAME>"
SECRET_ARN = "<SECRETS_MANAGER_ARN>"

table = dynamodb.Table(TABLE_NAME)
cached_webhook_url = None  # ✅ Cache to reduce Secrets Manager calls

# ✅ Function to initialize WebSocket API Client
def get_apigw_client(domain_name, stage):
    return boto3.client(
        "apigatewaymanagementapi",
        endpoint_url=f"https://{domain_name}/{stage}"
    )

# ✅ Function to retrieve Webhook URL from Secrets Manager (cached)
def get_webhook_url():
    global cached_webhook_url
    
    if cached_webhook_url:
        return cached_webhook_url

    try:
        response = secrets_manager.get_secret_value(SecretId=SECRET_ARN)
        secret_data = json.loads(response.get("SecretString", "{}"))
        webhook_url = secret_data.get("webhook_url", "")
        if webhook_url:
            cached_webhook_url = webhook_url  # ✅ Cache result for reuse
        return webhook_url
    except Exception:
        return ""

# ✅ Function to send event data to Make.com webhook
def send_to_make(event_data):
    make_url = get_webhook_url()
    if not make_url:
        return {"response": "Error: Missing Webhook URL"}
    
    try:
        response = requests.post(make_url, json=event_data, timeout=10)
        response.raise_for_status()
        return response.json() if response.content else {"response": "Success"}
    except requests.exceptions.RequestException:
        return {"response": "Request Error to Make.com"}

# ✅ Function to send messages via WebSocket
def send_to_websocket(domain, stage, connection_id, message):
    try:
        client = get_apigw_client(domain, stage)
        client.post_to_connection(ConnectionId=connection_id, Data=json.dumps({"response": message}))
    except Exception:
        pass

# ✅ Main WebSocket Lambda Handler
def lambda_handler(event, context):
    route_key = event.get("requestContext", {}).get("routeKey", "")
    
    if route_key == "$connect":
        return handle_connect(event)
    elif route_key == "$disconnect":
        return handle_disconnect(event)
    elif route_key == "sendMessage":
        return handle_message(event)
    
    return {"statusCode": 400, "body": "Invalid action"}

# ✅ WebSocket Connection Handlers
def handle_connect(event):
    return {"statusCode": 200, "body": "Connected"}

def handle_disconnect(event):
    return {"statusCode": 200, "body": "Disconnected"}

# ✅ Handles Incoming WebSocket Messages
def handle_message(event):
    connection_id = event["requestContext"]["connectionId"]
    domain_name = event["requestContext"]["domainName"]
    stage = event["requestContext"]["stage"]
    
    try:
        event_body = json.loads(event.get("body", "{}"))
        user_id = event_body.get("user_id")
        message = event_body.get("message")
        
        if not user_id or not message:
            return {"statusCode": 400, "body": "Missing user_id or message"}
        
        session_data = check_or_create_session(user_id, connection_id)
        update_chat_history(user_id, message)
        make_response = send_to_make(event_body)
        response_message = make_response.get("response", "No response from Make.com")
        send_to_websocket(domain_name, stage, connection_id, response_message)
        
        return {"statusCode": 200, "body": "Message processed successfully"}
    except Exception:
        return {"statusCode": 500, "body": "Internal Server Error"}

# ✅ Session Handling (DynamoDB)
def check_or_create_session(user_id, connection_id):
    now = datetime.now(timezone.utc)
    expiration_time = now - timedelta(days=7)
    
    response = table.get_item(Key={"TS_user_id": user_id})
    session_data = response.get("Item")
    
    if session_data:
        last_active = session_data.get("last_active")
        if last_active and datetime.fromisoformat(last_active) > expiration_time:
            table.update_item(
                Key={"TS_user_id": user_id},
                UpdateExpression="SET last_active = :now",
                ExpressionAttributeValues={":now": now.isoformat()}
            )
            return session_data
    
    new_session = {
        "TS_user_id": user_id,
        "connectionId": connection_id,
        "last_active": now.isoformat(),
        "chat_history": []
    }
    table.put_item(Item=new_session)
    return new_session

# ✅ Update Chat History
def update_chat_history(user_id, message):
    try:
        table.update_item(
            Key={"TS_user_id": user_id},
            UpdateExpression="SET chat_history = list_append(if_not_exists(chat_history, :empty_list), :new_message)",
            ExpressionAttributeValues={
                ":empty_list": [],
                ":new_message": [message]
            },
            ConditionExpression="attribute_exists(TS_user_id)"
        )
    except Exception:
        pass
