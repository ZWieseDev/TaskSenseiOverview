import json
import boto3
import stripe
import os

# ✅ Load environment variables (Placeholders for security)
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "<STRIPE_SECRET>")
STRIPE_SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL", "<SUCCESS_URL>")
STRIPE_CANCEL_URL = os.getenv("STRIPE_CANCEL_URL", "<CANCEL_URL>")

# ✅ Initialize Stripe API Key
stripe.api_key = STRIPE_SECRET_KEY

# ✅ Main Lambda Handler
def lambda_handler(event, context):
    """ ✅ Handles Stripe Checkout Session Creation """
    try:
        # ✅ Parse event body
        body = event.get("body", "{}")
        body = json.loads(body) if isinstance(body, str) else body

        # ✅ Extract required values
        user_id = body.get("user_id")
        plan = body.get("plan", "pro")  # Default to "pro" plan

        if not user_id:
            return generate_response(400, {"error": "Missing user_id"})

        # ✅ Create Stripe Checkout Session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "TaskSensei Subscription",
                        "description": f"{plan.capitalize()} Plan Subscription",
                    },
                    "unit_amount": 3900,  # $39.00 in cents
                    "recurring": {"interval": "month"}
                },
                "quantity": 1
            }],
            success_url=f"{STRIPE_SUCCESS_URL}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=STRIPE_CANCEL_URL
        )

        return generate_response(200, {"sessionId": session.id})
    except Exception:
        return generate_response(500, {"error": "Internal Server Error"})

# ✅ Helper Function: Generates API Gateway Response with CORS
def generate_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true"
        },
        "body": json.dumps(body)
    }
