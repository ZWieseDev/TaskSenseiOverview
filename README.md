# TaskSensei - Automation & AI-Powered Business Efficiency

## 🚀 Overview

TaskSensei is an AI-driven automation platform designed to streamline business processes, enhance productivity, and integrate seamlessly with cloud-based services. This project leverages **AWS Lambda, Cognito, WebSockets, DynamoDB, and Stripe** to provide a **secure authentication system, AI-powered chatbot interactions, automated file management, and seamless payment handling.**

## 🌟 Key Features

- **Secure Authentication** using **PKCE Challenge Flow & AWS Cognito**
- **Real-time AI Chatbot** with **WebSockets & Vector Database for Context Retention**
- **User File Management** with **S3 Presigned URLs & KMS Encryption**
- **Dynamic User Data Storage** in **DynamoDB with Secure Access**
- **Stripe Integration** for **Membership Unlock & Payment Handling**
- **Serverless Architecture** powered by AWS Lambda for scalability

---

## 🏗 Architecture Diagram



### **System Components:**

1. **Authentication & User Management** - AWS Cognito handles user sign-up, authentication, and secure access tokens.
2. **Chatbot with AI Automation** - WebSocket-based AI bot dynamically interacts with users and triggers automation services.
3. **User File Storage** - S3 Bucket (with **KMS Encryption**) stores user files securely, using **Presigned URLs** for access.
4. **Database & Security** - DynamoDB stores structured user data, encrypted at rest.
5. **Payments & Membership Handling** - Stripe Checkout & Webhooks update user status upon successful transactions.

---

## 🔑 Authentication Flow (PKCE)

### **Step-by-Step Process:**

1. **The user initiates login** via **Cognito Authorization Code Flow**
2. **PKCE Challenge is generated** (code verifier & challenge)
3. **The user is redirected to Cognito login** and returns with the **authorization code**
4. **Backend exchange code for tokens** (Access Token, ID Token, Refresh Token)
5. **Tokens are validated & user data is retrieved from Cognito**
6. **User session is stored securely & maintained with refresh tokens**

🔗 **Related Code:**

- [PKCE Authentication - Lambda](./pkce_authentication.py)
- [PKCE Authentication - Frontend](./pkce_authentication.js)

---

## 📡 API Endpoints

### **Authentication**

| Endpoint   | Method | Description                                  |
| ---------- | ------ | -------------------------------------------- |
| `/auth`    | `POST` | Handles user login via Cognito PKCE flow     |
| `/refresh` | `POST` | Refreshes user session using a refresh token |

### **User Management**

| Endpoint        | Method | Description                           |
| --------------- | ------ | ------------------------------------- |
| `/user/profile` | `GET`  | Retrieves user profile from DynamoDB  |
| `/user/update`  | `POST` | Updates user profile data in DynamoDB |

### **File Management**

| Endpoint    | Method | Description                                  |
| ----------- | ------ | -------------------------------------------- |
| `/generate` | `POST` | Generates a presigned URL for S3 file upload |

### **WebSocket for AI Chatbot**

| Endpoint            | Method | Description                                |
| ------------------- | ------ | ------------------------------------------ |
| `$connect`          | `WS`   | Handles WebSocket connection establishment |
| `$disconnect`       | `WS`   | Handles WebSocket disconnection            |
| `sendMessage`       | `WS`   | Processes and sends messages via WebSocket |
| `websocket-handler` | `WS`   | Main handler for WebSocket communication   |

### **Payment System (Stripe)**

| Endpoint    | Method | Description                               |
| ----------- | ------ | ----------------------------------------- |
| `/checkout` | `POST` | Initiates Stripe checkout session         |
| `/webhook`  | `POST` | Listens for Stripe payment status updates |

---

## 🤖 AI Chatbot - WebSocket Flow

### **How It Works:**

1. **User connects to WebSocket API** via browser
2. **Messages are sent to AWS Lambda for processing**
3. **Lambda calls AI model** (vector database for chat history)
4. **AI responds & dynamically triggers automation workflows**

🔗 **Related Code:**

- [WebSocket Lambda Handler](./chatbot_lambda.py)
- [Frontend WebSocket Connection](./chatbot_frontend.js)

---

## 📂 File Storage & User Data

### **User Files Handling:**

- **Presigned URLs** allow **secure file uploads & downloads** without exposing credentials.
- **User data is stored in DynamoDB**, linked via Cognito `username`.
- **All data & files are encrypted at rest using KMS.**

🔗 **Related Code:**

- [S3 Presigned URL Generator](./s3_presigned.py)
- [DynamoDB User Data Handler](./dynamodb_handler.py)

---

## 💰 Payment & Membership System (Stripe)

### **How Payments Work:**

1. **User selects a membership plan** on the frontend
2. **Stripe Checkout session is created** via API call
3. **Stripe Webhook listens for success/failure**
4. **DynamoDB updates user membership status** upon successful payment

🔗 **Related Code:**

- [Stripe Payment API](./stripe_payment.py)
- [Webhook for Stripe Status Updates](./stripe_webhook.py)

---

## 🚀 Deployment

### **Deploying AWS Lambda Functions**

```sh
aws lambda update-function-code --function-name TaskSenseiAuth --zip-file fileb://lambda.zip
```

### **Deploying Cognito User Pool**

Use **Terraform** or manually configure via AWS Console.

### **Deploying WebSocket API Gateway**

1. **Create WebSocket API in AWS API Gateway**
2. **Link WebSocket to Lambda Handler**
3. **Deploy API & Test WebSocket Connection**

---

## 🔮 Future Enhancements

✅ **Add OAuth2 Login with Google & Microsoft** ✅ **Enhance AI Chatbot with Dynamic Context Awareness** ✅ **Introduce Subscription-Based Payments** ✅ **Automate Deployment with Terraform**

---

## 📜 License

This project is licensed under the **MIT License**.

---

## ✉️ Contact

For questions, contact [**your-email@example.com**](mailto\:your-email@example.com) or visit [TaskSensei.com](https://tasksensei.com).

