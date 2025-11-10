import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_password_reset_email(email: str, token: str):
    """
    使用 SendGrid API 發送密碼重設郵件。
    
    開發模式（未設定 SENDGRID_API_KEY）：印在控制台
    生產模式（已設定 SENDGRID_API_KEY）：發送真實郵件
    """
    
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    MAIL_FROM_EMAIL = os.getenv("MAIL_FROM_EMAIL", "noreply@movivin.com")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    reset_url = f"{frontend_url}/reset-password?token={token}"
    
    # 開發模式：如果未設定 SENDGRID_API_KEY，就印在控制台
    if not SENDGRID_API_KEY:
        print("\n" + "="*60)
        print("📧 [開發模式] 密碼重設郵件（模擬）")
        print("="*60)
        print(f"收件人: {email}")
        print(f"主旨: [MovieIN] 重設您的密碼")
        print(f"重設連結: {reset_url}")
        print(f"Token: {token}")
        print(f"有效期限: 30 分鐘")
        print("="*60 + "\n")
        return True
    
    # 生產模式：發送真實郵件
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1>重設您的 MovieIN 密碼</h1>
            <p>您好，</p>
            <p>我們收到了您的密碼重設請求。請點擊下方按鈕設定新密碼：</p>
            <a href="{reset_url}" 
               style="display: inline-block; padding: 12px 24px; background-color: #007bff; 
                      color: white; text-decoration: none; border-radius: 5px; margin: 20px 0;">
                重設密碼
            </a>
            <p>如果您沒有請求重設密碼，請忽略此郵件。</p>
            <p>此連結將在 30 分鐘後過期。</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
            <p style="color: #888; font-size: 12px;">MovieIN 團隊</p>
        </div>
    </body>
    </html>
    """
    
    message = Mail(
        from_email=MAIL_FROM_EMAIL,
        to_emails=email,
        subject='[MovieIN] 重設您的密碼',
        html_content=html_content
    )
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        if response.status_code == 202:
            print(f"✅ 密碼重設郵件已發送至 {email}")
            return True
        else:
            print(f"❌ SendGrid 郵件發送失敗: {response.status_code}")
            print(response.body)
            return False
            
    except Exception as e:
        print(f"❌ 郵件發送異常: {e}")
        return False