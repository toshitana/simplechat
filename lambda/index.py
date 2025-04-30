# lambda/index.py
import json
import urllib.request
import re  # ユーザー情報抽出で使う場合のみ

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        # Cognitoで認証されたユーザー情報を取得（必要なら残す）
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")

        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        print("Processing message:", message)

        # 会話履歴を使用
        messages = conversation_history.copy()

        # ユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": message
        })

        # 外部APIエンドポイント
        url = "https://085c-34-16-238-128.ngrok-free.app/generate"

        # リクエストボディ
        data = {
            "prompt": message,
            "max_new_tokens": 128,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
        }

        # JSONに変換し、バイト列にエンコード
        json_data = json.dumps(data).encode("utf-8")

        # ヘッダー
        headers = {
            "Content-Type": "application/json"
        }

        # リクエスト作成
        req = urllib.request.Request(url, data=json_data, headers=headers, method="POST")

        # リクエスト送信
        try:
            with urllib.request.urlopen(req) as res:
                response_body = res.read()
                response_json = json.loads(response_body)
                response = response_json["generated_text"]
                print("External API response:", response)
                if not response:
                    raise Exception("No response content from the external API")
        except Exception as api_error:
            print("External API error:", str(api_error))
            raise

        # アシスタントの応答を会話履歴に追加
        messages.append({
            "role": "assistant",
            "content": response
        })

        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": response,
                "conversationHistory": messages
            })
        }

    except Exception as error:
        print("Error:", str(error))

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
