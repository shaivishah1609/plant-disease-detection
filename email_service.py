import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_CONFIG
import streamlit as st

class EmailService:
    def __init__(self):
        self.smtp_server = EMAIL_CONFIG['smtp_server']
        self.smtp_port = EMAIL_CONFIG['smtp_port']
        self.email = EMAIL_CONFIG['email']
        self.password = EMAIL_CONFIG['password']
        self.from_name = EMAIL_CONFIG['from_name']
    
    def send_reset_email(self, to_email, username, reset_token):
        """Send password reset email"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = "🔑 Password Reset - Plant Disease Detection"
            message["From"] = f"{self.from_name} <{self.email}>"
            message["To"] = to_email
            
            # HTML email template
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ text-align: center; color: #2e7d32; margin-bottom: 30px; }}
                    .content {{ line-height: 1.6; color: #333; }}
                    .reset-code {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; text-align: center; font-size: 24px; font-weight: bold; color: #2e7d32; margin: 20px 0; letter-spacing: 3px; }}
                    .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 12px; }}
                    .warning {{ background-color: #fff3cd; padding: 10px; border-radius: 5px; color: #856404; margin: 15px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🌱 Plant Disease Detection</h1>
                        <h2>Password Reset Request</h2>
                    </div>
                    
                    <div class="content">
                        <p>Hello <strong>{username}</strong>,</p>
                        
                        <p>We received a request to reset your password. Use the reset code below to create a new password:</p>
                        
                        <div class="reset-code">{reset_token}</div>
                        
                        <div class="warning">
                            <strong>⚠️ Security Notice:</strong>
                            <ul>
                                <li>This code expires in 1 hour</li>
                                <li>Don't share this code with anyone</li>
                                <li>If you didn't request this, ignore this email</li>
                            </ul>
                        </div>
                        
                        <p>To reset your password:</p>
                        <ol>
                            <li>Go back to the login page</li>
                            <li>Click "Forgot Password"</li>
                            <li>Enter this reset code</li>
                            <li>Create your new password</li>
                        </ol>
                        
                        <p>If you have any issues, please contact our support team.</p>
                        
                        <p>Best regards,<br>
                        <strong>Plant Disease Detection Team</strong></p>
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated email. Please do not reply.</p>
                        <p>© 2024 Plant Disease Detection System. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Attach HTML content
            html_part = MIMEText(html, "html")
            message.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email, self.password)
                server.sendmail(self.email, to_email, message.as_string())
            
            return True, "Reset email sent successfully!"
            
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    def send_welcome_email(self, to_email, username):
        """Send welcome email to new users"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = "🌱 Welcome to Plant Disease Detection!"
            message["From"] = f"{self.from_name} <{self.email}>"
            message["To"] = to_email
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ text-align: center; color: #2e7d32; margin-bottom: 30px; }}
                    .content {{ line-height: 1.6; color: #333; }}
                    .features {{ background-color: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🌱 Welcome to Plant Disease Detection!</h1>
                    </div>
                    
                    <div class="content">
                        <p>Hello <strong>{username}</strong>,</p>
                        
                        <p>Welcome to our AI-powered plant disease detection system! Your account has been successfully created.</p>
                        
                        <div class="features">
                            <h3>🚀 What you can do:</h3>
                            <ul>
                                <li>🔬 Detect 38+ plant diseases with 95.6% accuracy</li>
                                <li>📊 Get detailed confidence scores</li>
                                <li>📈 Track your scan history</li>
                                <li>📥 Export your data</li>
                                <li>🔒 Secure encrypted data storage</li>
                            </ul>
                        </div>
                        
                        <p>Ready to get started? Upload your first plant image and let our AI help you identify any diseases!</p>
                        
                        <p>Happy gardening!<br>
                        <strong>Plant Disease Detection Team</strong></p>
                    </div>
                    
                    <div class="footer">
                        <p>© 2024 Plant Disease Detection System. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            html_part = MIMEText(html, "html")
            message.attach(html_part)
            
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email, self.password)
                server.sendmail(self.email, to_email, message.as_string())
            
            return True, "Welcome email sent!"
            
        except Exception as e:
            return False, f"Failed to send welcome email: {str(e)}"