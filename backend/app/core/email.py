import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# 1. 這是 Email 模板 (保持不變)
def create_reset_email_template(email_to: str, token: str) -> str:
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    reset_url = f"{frontend_url}/reset-password?token={token}"
    
    # (我們使用和之前一樣的 HTML 模板)
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .container {{ width: 90%; margin: auto; padding: 20px; }}
            .header {{ font-size: 24px; color: #333; }}
            .content {{ margin-top: 20px; }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                margin-top: 20px;
                background-color: #007bff;
                color: #ffffff;
                text-decoration: none;
                border-radius: 5px;
            }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">重設您的 MovieIN 密碼</h1>
            <div class="content">
                <p>您好，</p>
                <p>我們收到了您的密碼重設請求。請點擊下方的按鈕來設定您的新密碼：</p>
                <a href="{reset_url}" class="button" style="color: #ffffff;">重設密碼</a>
                <p>如果您沒有請求重設密碼，請忽略此郵件。</p>
                <p>此連結將在 30 分鐘後過期。</p>
            </div>
            <div class="footer">
                <p>謝謝您, <br/>MovieIN 團隊</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

# 2. 這是「真正」的 SendGrid 寄信函式
def send_password_reset_email(email: str, token: str):
    """
    (同步) 使用 SendGrid API 發送密碼重設郵件。
    """
    
    # 從 .env 讀取金鑰和寄件人
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    MAIL_FROM_EMAIL = os.getenv("MAIL_FROM_EMAIL")

    if not SENDGRID_API_KEY or not MAIL_FROM_EMAIL:
        print("!!! 錯誤：SENDGRID_API_KEY 或 MAIL_FROM_EMAIL 未在 .env 中設定")
        return False

    message = Mail(
        from_email=MAIL_FROM_EMAIL,
        to_emails=email,
        subject='[MovieIN] 重設您的密碼 (Password Reset Request)',
        html_content=create_reset_email_template(email, token)
    )
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        # SendGrid 成功「接受」請求的狀態碼是 202
        if response.status_code == 202:
            print(f"--- [真實郵件已發送] ---")
            print(f"服務：SendGrid")
            print(f"收件人 (To): {email}")
            print(f"狀態：{response.status_code} (Accepted)")
            print(f"-------------------------")
            return True
        else:
            print(f"!!! SendGrid 郵件發送失敗: {response.status_code}")
            print(response.body)
            return False
            
    except Exception as e:
        print(f"!!! 郵件 API 執行失敗: {e}")
        return False