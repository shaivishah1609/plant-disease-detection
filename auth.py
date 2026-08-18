import streamlit as st
import re
from database import DatabaseManager
import time

class AuthManager:
    def __init__(self):
        try:
            self.db = DatabaseManager()
        except Exception as e:
            print(f"Warning: Database initialization failed: {str(e)}")
            self.db = None
    
    def validate_email_format(self, email):
        """Validate email format"""
        try:
            # Simple email validation
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(pattern, email):
                return True, ""
            else:
                return False, "Invalid email format"
        except:
            return False, "Invalid email format"
    
    def validate_password_strength(self, password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r"\d", password):
            return False, "Password must contain at least one number"
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"
        
        return True, "Strong password"
    
    def validate_username(self, username):
        """Validate username"""
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 20:
            return False, "Username must be less than 20 characters"
        
        if not re.match("^[a-zA-Z0-9_]+$", username):
            return False, "Username can only contain letters, numbers, and underscores"
        
        return True, "Valid username"
    
    def login_page(self):
        """Enhanced login page with impressive design"""
        st.markdown("""
        <style>
        .main-header {
            text-align: center;
            padding: 2rem 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .auth-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.5rem 1rem;
            font-weight: bold;
            width: 100%;
        }
        .success-box {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            margin: 1rem 0;
        }
        .error-box {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Main header
        st.markdown("""
        <div class="main-header">
            <h1>🌱 Plant Disease Detection</h1>
            <h3>AI-Powered Plant Health Analysis</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Login/Register tabs
        tab1, tab2, tab3 = st.tabs(["🔑 Login", "📝 Register", "🔒 Reset Password"])
        
        with tab1:
            self.login_form()
        
        with tab2:
            self.register_form()
        
        with tab3:
            self.reset_password_form()
    
    def login_form(self):
        """Login form"""
        st.subheader("🔑 Login to Your Account")
        
        with st.form("login_form"):
            username_or_email = st.text_input("👤 Username or Email")
            password = st.text_input("🔒 Password", type="password")
            submit_button = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submit_button:
                if username_or_email and password:
                    success, user, message = self.db.authenticate_user(username_or_email, password)
                    
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_id = user.id
                        st.session_state.username = user.username
                        st.session_state.email = user.email
                        st.success("✅ Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Please fill in all fields")
    
    def register_form(self):
        """Registration form"""
        st.subheader("📝 Create New Account")
        
        with st.form("register_form"):
            username = st.text_input("👤 Username")
            email = st.text_input("📧 Email")
            password = st.text_input("🔒 Password", type="password")
            confirm_password = st.text_input("🔒 Confirm Password", type="password")
            submit_button = st.form_submit_button("🎉 Create Account", use_container_width=True)
            
            if submit_button:
                if username and email and password and confirm_password:
                    # Validate username
                    valid_username, username_msg = self.validate_username(username)
                    if not valid_username:
                        st.error(f"❌ {username_msg}")
                        return
                    
                    # Validate email
                    valid_email, email_msg = self.validate_email_format(email)
                    if not valid_email:
                        st.error(f"❌ {email_msg}")
                        return
                    
                    # Validate password
                    valid_password, password_msg = self.validate_password_strength(password)
                    if not valid_password:
                        st.error(f"❌ {password_msg}")
                        return
                    
                    # Check password confirmation
                    if password != confirm_password:
                        st.error("❌ Passwords do not match")
                        return
                    
                    # Create user
                    success, message = self.db.create_user(username, email, password)
                    
                    if success:
                        st.success("✅ Account created successfully! Please login.")
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Please fill in all fields")
    
    def reset_password_form(self):
        """Password reset form"""
        st.subheader("🔒 Reset Your Password")
        
        if 'reset_step' not in st.session_state:
            st.session_state.reset_step = 1
        
        if st.session_state.reset_step == 1:
            # Step 1: Enter email
            with st.form("reset_email_form"):
                email = st.text_input("📧 Enter your email address")
                submit_button = st.form_submit_button("📨 Send Reset Code", use_container_width=True)
                
                if submit_button:
                    if email:
                        success, message = self.db.generate_reset_token(email)
                        if success:
                            st.session_state.reset_email = email
                            st.session_state.reset_step = 2
                            st.success("✅ Reset code sent to your email!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("❌ Please enter your email")
        
        elif st.session_state.reset_step == 2:
            # Step 2: Enter reset code and new password
            with st.form("reset_password_form"):
                st.info(f"📧 Reset code sent to: {st.session_state.reset_email}")
                reset_code = st.text_input("🔑 Enter 6-digit reset code")
                new_password = st.text_input("🔒 New Password", type="password")
                confirm_password = st.text_input("🔒 Confirm New Password", type="password")
                submit_button = st.form_submit_button("🔄 Reset Password", use_container_width=True)
                
                if submit_button:
                    if reset_code and new_password and confirm_password:
                        # Validate password
                        valid_password, password_msg = self.validate_password_strength(new_password)
                        if not valid_password:
                            st.error(f"❌ {password_msg}")
                            return
                        
                        # Check password confirmation
                        if new_password != confirm_password:
                            st.error("❌ Passwords do not match")
                            return
                        
                        # Reset password
                        success, message = self.db.reset_password(
                            st.session_state.reset_email, 
                            reset_code, 
                            new_password
                        )
                        
                        if success:
                            st.success("✅ Password reset successfully! Please login.")
                            st.session_state.reset_step = 1
                            if 'reset_email' in st.session_state:
                                del st.session_state.reset_email
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("❌ Please fill in all fields")
            
            if st.button("⬅️ Back to email entry"):
                st.session_state.reset_step = 1
                st.rerun()
    
    def logout(self):
        """Logout user"""
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        st.success("👋 Logged out successfully!")
        time.sleep(1)
        st.rerun()
