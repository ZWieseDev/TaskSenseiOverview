import json
import boto3
import os

# ✅ Initialize AWS Clients
dynamodb = boto3.resource("dynamodb")

# ✅ Environment Variables (Placeholders for Security)
TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "<DYNAMODB_USERS_TABLE>")

# ✅ Main Lambda Handler
def lambda_handler(event, context):
    """ ✅ Handles Stripe Webhook Events """
    try:
        # ✅ Extract event type directly (NO "body" field in Stripe webhook)
        event_type = event.get("type", "unknown")
        data_object = event.get("data", {}).get("object", {})

        # ✅ Extract necessary details
        metadata = data_object.get("metadata", {})
        user_id = metadata.get("user_id", "unknown_user")
        plan = metadata.get("plan", "unknown_plan")
        payment_status = data_object.get("status", "unpaid")

        # ✅ Handle successful checkout session
        if event_type == "checkout.session.completed" and payment_status == "paid":
            update_subscription_status(user_id, plan)

        return generate_response(200, {"message": "Webhook processed successfully"})
    except Exception:
        return generate_response(500, {"error": "Internal Server Error"})

# ✅ Function to update user subscription in DynamoDB
def update_subscription_status(user_id, plan):
    """ ✅ Updates subscription plan and payment status in DynamoDB. """
    table = dynamodb.Table(TABLE_NAME)
    table.update_item(
        Key={"TS_user_id": user_id},
        UpdateExpression="SET plan = :plan, payment_status = :status",
        ExpressionAttributeValues={":plan": plan, ":status": "active"}
    )

# ✅ Helper Function: Generates API Gateway Response
def generate_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(body)
    }
