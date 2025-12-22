import streamlit as st
import pandas as pd
import io
from datetime import datetime
import time
import hashlib
import random

# Import new template management system
from templates_manager import DynamicTemplateManager
from config_components import *
from ui_components import *


class FollowupStageManager:
    """Manage different follow-up stages with separate data handling"""

    def __init__(self, system):
        self.system = system
        self.stages = ["Initial Outreach", "Follow-up 1", "Follow-up 2", "Follow-up 3"]

    def get_stage_data(self, stage):
        """Get data for specific stage"""
        stage_key = f"{stage.lower().replace('-', '').replace(' ', '')}_data"
        if stage_key not in st.session_state:
            st.session_state[stage_key] = None
        return st.session_state[stage_key]

    def set_stage_data(self, stage, df):
        """Set data for specific stage"""
        stage_key = f"{stage.lower().replace('-', '').replace(' ', '')}_data"
        st.session_state[stage_key] = df

    def validate_stage_data(self, df, stage):
        """Validate data for specific stage with appropriate status checks"""
        if df is None or df.empty:
            return False

        # Check for required columns
        required_columns = ['Name', 'Email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Missing required columns: {', '.join(missing_columns)}")
            return False

        # Add Description column if missing
        if 'Description' not in df.columns:
            df['Description'] = 'Business needs digital marketing services'

        # Add stage-specific tracking columns if missing
        tracking_columns = self._get_stage_tracking_columns(stage)
        for col, default_value in tracking_columns.items():
            if col not in df.columns:
                df[col] = default_value

        return True

    def _get_stage_tracking_columns(self, stage):
        """Get tracking columns specific to each stage"""
        base_columns = {
            'Status': 'Not Sent',
            'Last_Sent_Date': '',
            'Last_Email_Body': ''
        }

        stage_specific = {
            "Initial Outreach": {
                'Followup_Stage': 0,
                'Initial_Outreach_Sent': '',
                'Followup_1_Sent': '',
                'Followup_2_Sent': '',
                'Followup_3_Sent': ''
            },
            "Follow-up 1": {
                'Followup_Stage': 1,
                'Initial_Outreach_Sent': 'Completed',  # Must be completed for follow-up
                'Followup_1_Sent': '',
                'Followup_2_Sent': '',
                'Followup_3_Sent': ''
            },
            "Follow-up 2": {
                'Followup_Stage': 2,
                'Initial_Outreach_Sent': 'Completed',
                'Followup_1_Sent': 'Completed',
                'Followup_2_Sent': '',
                'Followup_3_Sent': ''
            },
            "Follow-up 3": {
                'Followup_Stage': 3,
                'Initial_Outreach_Sent': 'Completed',
                'Followup_1_Sent': 'Completed',
                'Followup_2_Sent': 'Completed',
                'Followup_3_Sent': ''
            }
        }

        return {**base_columns, **stage_specific.get(stage, {})}

    def get_pending_leads(self, stage, batch_size):
        """Get pending leads for specific stage"""
        df = self.get_stage_data(stage)
        if df is None or df.empty:
            return pd.DataFrame()

        if stage == "Initial Outreach":
            mask = df['Status'] == 'Not Sent'
        else:
            # For follow-ups, check that previous stage is completed
            prev_stage_col = self._get_previous_stage_column(stage)
            mask = (df['Status'] == 'Not Sent') & (df[prev_stage_col] == 'Completed')

        pending = df[mask].head(batch_size)
        return pending

    def _get_previous_stage_column(self, stage):
        """Get the column name for the previous stage"""
        stage_mapping = {
            "Follow-up 1": "Initial_Outreach_Sent",
            "Follow-up 2": "Followup_1_Sent",
            "Follow-up 3": "Followup_2_Sent"
        }
        return stage_mapping.get(stage, "")

    def update_lead_status(self, idx, stage, email_body, template_id=None):
        """Update lead status after sending email"""
        df = self.get_stage_data(stage)
        if df is None or df.empty:
            return

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        status_mapping = {
            "Initial Outreach": {
                'Status': 'Initial Sent',
                'Followup_Stage': 1,
                'Initial_Outreach_Sent': now,
                'Last_Email_Body': email_body,
                'Last_Template_Used': template_id
            },
            "Follow-up 1": {
                'Status': 'Follow-up 1 Sent',
                'Followup_Stage': 2,
                'Followup_1_Sent': now,
                'Last_Email_Body': email_body,
                'Last_Template_Used': template_id
            },
            "Follow-up 2": {
                'Status': 'Follow-up 2 Sent',
                'Followup_Stage': 3,
                'Followup_2_Sent': now,
                'Last_Email_Body': email_body,
                'Last_Template_Used': template_id
            },
            "Follow-up 3": {
                'Status': 'Follow-up 3 Sent',
                'Followup_Stage': 4,
                'Followup_3_Sent': now,
                'Last_Email_Body': email_body,
                'Last_Template_Used': template_id
            }
        }

        updates = status_mapping[stage]
        for col, value in updates.items():
            if col in df.columns:
                df.at[idx, col] = value

        df.at[idx, 'Last_Sent_Date'] = now
        self.set_stage_data(stage, df)

    def export_stage_data(self, stage):
        """Export data for specific stage as Excel"""
        df = self.get_stage_data(stage)
        if df is not None and not df.empty:
            # Ensure proper format for next stage
            export_df = df.copy()

            # Update status for next stage compatibility
            if stage == "Initial Outreach":
                export_df['Status'] = 'Not Sent'
                export_df['Initial_Outreach_Sent'] = 'Completed'
            elif stage == "Follow-up 1":
                export_df['Status'] = 'Not Sent'
                export_df['Followup_1_Sent'] = 'Completed'
            elif stage == "Follow-up 2":
                export_df['Status'] = 'Not Sent'
                export_df['Followup_2_Sent'] = 'Completed'

            return export_df
        return None


class EnhancedOutreachSystem:
    """Enhanced outreach system with dynamic template management"""

    def __init__(self):
        self.email_sender = HighPerformanceEmailSender()
        self.template_manager = DynamicTemplateManager()
        self.email_history = EmailHistory()
        self.sheets_manager = GoogleSheetsManager()
        self.analytics_dashboard = AnalyticsDashboard(self)
        self.admin_panel = AdminPanel(self)
        self.stage_manager = FollowupStageManager(self)

        # Template selection modes
        self.template_selection_mode = "auto_detect"  # Options: "auto_detect", "manual_select", "specific_template"
        self.selected_template_id = None

        self.current_campaign = "auto_detect"
        self.current_followup_stage = "Initial Outreach"
        self.sheet_url = None

        # Initialize session state
        self._init_session_state()

    def _init_session_state(self):
        """Initialize all required session states"""
        required_states = {
            'enhanced_init': True,
            'sent_count': 0,
            'failed_count': 0,
            'smtp_configured': False,
            'processing': False,
            'sheets_connected': False,
            'ai_mode': True,
            'logged_in': False,
            'login_attempts': 0,
            'last_login_time': None,
            'login_timestamp': 0,
            'email_history': [],
            'dashboard_updates': {'last_refresh': datetime.now()},
            'recent_activity': [],
            'template_selection_mode': 'auto_detect',
            'selected_template_id': None,
            'manual_template_override': False,
            'template_preview_shown': False
        }

        for key, value in required_states.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def set_template_selection_mode(self, mode: str, template_id: str = None):
        """Set template selection mode"""
        self.template_selection_mode = mode
        self.selected_template_id = template_id
        st.session_state.template_selection_mode = mode
        if template_id:
            st.session_state.selected_template_id = template_id

    def _get_time_ago(self, timestamp):
        """Calculate time ago from timestamp"""
        now = datetime.now()
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            except:
                return "Recently"

        diff = now - timestamp

        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "Just now"

    def configure_email(self, email, password, server="smtp.gmail.com", port=587):
        """Configure email with any provider"""
        try:
            self.email_sender.configure(email, password, server, port)
            if self.email_sender.test_connection():
                st.session_state.smtp_configured = True
                # Store email config in session state
                st.session_state.email_config = {
                    'email': email,
                    'server': server,
                    'port': port
                }
                return True
            return False
        except Exception as e:
            st.error(f"Configuration error: {str(e)}")
            return False

    def connect_google_sheets(self, credentials_json, sheet_url, stage):
        """Connect to Google Sheets for specific stage"""
        if self.sheets_manager.connect(credentials_json):
            self.sheet_url = sheet_url
            df = self.sheets_manager.get_sheet_data(sheet_url)
            if df is not None and not df.empty:
                if self.stage_manager.validate_stage_data(df, stage):
                    self.stage_manager.set_stage_data(stage, df)
                    st.session_state.sheets_connected = True
                    return True
        return False

    def load_dataframe(self, df, stage):
        """Load and validate dataframe for specific stage"""
        if df is not None and not df.empty:
            if self.stage_manager.validate_stage_data(df, stage):
                self.stage_manager.set_stage_data(stage, df)
                return True
        return False

    def process_batch(self, batch_size=8, stage="Initial Outreach"):
        """Process batch with dynamic template selection"""
        if not st.session_state.smtp_configured:
            st.error("❌ Configure email settings first")
            return

        pending_leads = self.stage_manager.get_pending_leads(stage, batch_size)

        if pending_leads.empty:
            st.info(f"🎉 No pending leads for {stage}!")
            return

        st.session_state.processing = True

        # Create real-time updates container
        realtime_container = st.container()

        with realtime_container:
            st.subheader("🚀 Real-time Sending Progress")

            # Create columns for status display
            status_col1, status_col2, status_col3 = st.columns(3)

            with status_col1:
                progress_bar = st.progress(0)
            with status_col2:
                current_status = st.empty()
            with status_col3:
                current_lead = st.empty()

        template_mode = st.session_state.get('template_selection_mode', 'auto_detect')

        # Determine mode text
        if template_mode == "auto_detect":
            mode_text = "🤖 Auto-detect Templates"
        elif template_mode == "specific_template":
            if st.session_state.selected_template_id:
                template_name = self.template_manager.templates.get(
                    st.session_state.selected_template_id, {}
                ).get('name', 'Unknown')
                mode_text = f"🎯 Specific: {template_name}"
            else:
                mode_text = "🎯 Specific Template"
        elif template_mode == "manual_select":
            mode_text = "🔄 Manual Template Selection"
        else:
            mode_text = "📧 Template Mode"

        current_status.text(f"Starting {mode_text} {stage}...")
        current_lead.text("Preparing emails...")

        # Prepare email tasks with template detection
        email_tasks = []
        successful_prepares = 0
        failed_prepares = 0

        for idx, lead in pending_leads.iterrows():
            try:
                # Determine which template to use
                template_id = None
                lead_name = lead['Name'] if 'Name' in lead else "Lead"
                description = lead['Description'] if 'Description' in lead and pd.notna(lead['Description']) else ""

                # Template selection logic
                if st.session_state.template_selection_mode == "auto_detect":
                    # Auto-detect based on description
                    template_id = self.template_manager.detect_best_template(description)
                    if st.session_state.get('debug_mode', False):
                        st.write(f"Auto-detected: {template_id} for {lead_name}")

                elif st.session_state.template_selection_mode == "specific_template":
                    # Use specifically selected template
                    template_id = st.session_state.selected_template_id

                elif st.session_state.template_selection_mode == "manual_select":
                    # Manual override per lead (if specified in data)
                    if 'Selected_Template' in lead and pd.notna(lead['Selected_Template']):
                        template_id = str(lead['Selected_Template']).strip()
                    else:
                        # Fallback to auto-detect
                        template_id = self.template_manager.detect_best_template(description)

                # Get template for the stage
                template = self.template_manager.get_template(template_id, stage)

                if not template or not template.get('body'):
                    st.warning(f"No template body found for {template_id} at {stage}")
                    template = self.template_manager.get_template("no_website", stage)

                # Personalize email
                subject = template["subject"].format(name=lead_name)
                email_body = template["body"].format(name=lead_name)

                email_tasks.append((idx, lead['Email'], subject, email_body, lead_name, template_id))
                successful_prepares += 1

            except Exception as e:
                st.error(f"Failed to prepare email for {lead_name}: {str(e)}")
                failed_prepares += 1

        # Send emails with real-time updates
        successful_sends = 0
        failed_sends = 0

        if email_tasks:
            for i, (idx, recipient_email, subject, body, lead_name, template_id) in enumerate(email_tasks):
                # Update real-time display
                progress = ((i + 1) / len(email_tasks)) * 100
                progress_bar.progress(int(progress))
                current_status.text(f"📤 Sending email {i + 1}/{len(email_tasks)}")
                current_lead.text(f"👤 Current: {lead_name}")

                # Add to recent activity
                activity_entry = {
                    'timestamp': datetime.now(),
                    'lead_name': lead_name,
                    'email': recipient_email,
                    'stage': stage,
                    'template': template_id,
                    'status': 'Processing'
                }
                st.session_state.recent_activity.append(activity_entry)

                # Send the email
                success = self.email_sender.send_single_email(recipient_email, subject, body)

                # Add delay between emails
                time.sleep(Config.RATE_LIMIT_DELAY)

                # Update results
                if success:
                    self.stage_manager.update_lead_status(idx, stage, body, template_id)
                    successful_sends += 1
                    self.email_history.add_email(
                        lead_name, recipient_email, subject, body, "Sent", stage, template_id
                    )
                    st.session_state.recent_activity[-1]['status'] = '✅ Sent'
                else:
                    failed_sends += 1
                    self.email_history.add_email(
                        lead_name, recipient_email, subject, body, "Failed", stage, template_id
                    )
                    st.session_state.recent_activity[-1]['status'] = '❌ Failed'

                # Force UI update
                time.sleep(0.1)

        # Complete progress
        progress_bar.progress(100)
        current_status.text(f"✅ Batch complete!")
        current_lead.text(f"Total: {len(email_tasks)} emails")

        st.session_state.sent_count += successful_sends
        st.session_state.failed_count += failed_sends
        st.session_state.processing = False

        if successful_sends > 0:
            # Show template usage summary
            template_summary = {}
            for task in email_tasks:
                template_id = task[5]
                if template_id:
                    template_summary[template_id] = template_summary.get(template_id, 0) + 1

            summary_text = f"✅ {mode_text} - Sent {successful_sends} {stage} emails!"
            if template_summary:
                summary_text += f"\n📊 Templates used: "
                summary_text += ", ".join([f"{self.template_manager.templates.get(tid, {}).get('name', tid)} ({count})"
                                           for tid, count in template_summary.items()][:3])

            st.success(summary_text)
            # Auto-refresh dashboard
            time.sleep(2)
            st.rerun()

        if failed_sends > 0:
            st.error(f"❌ Failed to send {failed_sends} emails")

        if failed_prepares > 0:
            st.warning(f"⚠️ Failed to prepare {failed_prepares} emails")

    def export_to_google_sheets(self, stage):
        """Export current data with status to Google Sheets - ONE CLICK UPDATE"""
        try:
            # Get the sheet URL from session state
            sheet_url = st.session_state.get(f'sheet_url_{stage}')
            creds_json = st.session_state.get(f'creds_json_{stage}')

            if not sheet_url or not creds_json:
                st.error("❌ Google Sheets not properly configured for this stage")
                return False

            # Connect to Google Sheets
            if not self.sheets_manager.connected:
                if not self.sheets_manager.connect(creds_json):
                    st.error("❌ Failed to connect to Google Sheets")
                    return False

            # Get current data
            df = self.stage_manager.export_stage_data(stage)
            if df is None or df.empty:
                st.error("❌ No data to export")
                return False

            # Update Google Sheet
            if self.sheets_manager.update_sheet_with_status(sheet_url, 0, df):
                # Add log entry
                if 'system_logs' not in st.session_state:
                    st.session_state.system_logs = []

                st.session_state.system_logs.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "level": "INFO",
                    "message": f"Google Sheet updated for {stage} with {len(df)} records"
                })
                return True
            else:
                return False

        except Exception as e:
            st.error(f"Export error: {str(e)}")
            return False

    def get_system_status(self):
        status = {
            "email_service": st.session_state.smtp_configured,
            "sheets_connected": st.session_state.sheets_connected,
            "ai_mode": st.session_state.get('ai_mode', True),
            "processing": not st.session_state.processing,
            "sent_emails": st.session_state.sent_count,
            "failed_emails": st.session_state.failed_count,
            "template_mode": st.session_state.get('template_selection_mode', 'auto_detect'),
            "templates_loaded": len(self.template_manager.templates)
        }
        return status


def render_login():
    """Render login form with improved security and session handling"""
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Login header
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="color: #667eea; margin-bottom: 0.5rem;">🔐 SAM Outreach Pro</h1>
            <p style="color: #888; margin-bottom: 2rem;">Dynamic Template Email Outreach System</p>
        </div>
        """, unsafe_allow_html=True)

        # Login card
        with st.container():
            st.markdown(
                '<div style="background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">',
                unsafe_allow_html=True)

            st.markdown("### 🔑 Administrator Login")

            username = st.text_input("Username", placeholder="Enter username", key="login_username")
            password = st.text_input("Password", type="password", placeholder="Enter password", key="login_password")

            # Login button
            if st.button("🚀 Login to Dashboard", use_container_width=True, type="primary"):
                if username == Config.DEFAULT_USERNAME and password == Config.DEFAULT_PASSWORD:
                    # Successful login - set all required session states
                    st.session_state.logged_in = True
                    st.session_state.login_attempts = 0
                    st.session_state.last_login_time = datetime.now()
                    st.session_state.login_timestamp = time.time()  # For session expiry

                    # Initialize other required session states
                    if 'email_history' not in st.session_state:
                        st.session_state.email_history = []
                    if 'smtp_configured' not in st.session_state:
                        st.session_state.smtp_configured = False
                    if 'ai_mode' not in st.session_state:
                        st.session_state.ai_mode = True
                    if 'sent_count' not in st.session_state:
                        st.session_state.sent_count = 0
                    if 'failed_count' not in st.session_state:
                        st.session_state.failed_count = 0
                    if 'recent_activity' not in st.session_state:
                        st.session_state.recent_activity = []

                    st.success("✅ Login successful! Redirecting...")
                    time.sleep(0.5)  # Brief pause for user to see success message
                    st.rerun()
                else:
                    # Failed login
                    st.session_state.login_attempts = st.session_state.get('login_attempts', 0) + 1
                    st.error(f"❌ Invalid credentials. Attempt {st.session_state.login_attempts}/5")

                    # Show hint after 2 failed attempts
                    if st.session_state.login_attempts >= 2:
                        st.info(f"💡 Hint: Default credentials are {Config.DEFAULT_USERNAME}/{Config.DEFAULT_PASSWORD}")

                    # Lock after 5 failed attempts
                    if st.session_state.login_attempts >= 5:
                        st.error("🔒 Too many failed attempts. Please try again later.")
                        time.sleep(2)  # Give time to read message
                        st.session_state.login_attempts = 0  # Reset after lockout

            # Forgot password section
            with st.expander("🔐 Forgot Password?"):
                st.info(f"""
                **Default Administrator Credentials:**
                - **Username:** `{Config.DEFAULT_USERNAME}`
                - **Password:** `{Config.DEFAULT_PASSWORD}`

                **Security Note:**
                - Change these credentials in the Admin Panel after login
                - For security, use strong passwords
                - Contact system administrator for password reset
                """)

            st.markdown("</div>", unsafe_allow_html=True)


def load_css():
    """Load the external CSS theme file"""
    # Fallback CSS if file not found
    st.markdown("""
    <style>
    /* Main theme */
    .main {
        background-color: #0F1A2F;
        color: #FFFFFF;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1E2A4A 0%, #2A3D5F 100%);
        border: 1px solid #2A3D5F;
        color: #FFFFFF;
        border-radius: 12px;
        padding: 1.5rem;
        transition: transform 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-5px);
    }

    /* Stage indicators */
    .stage-indicator {
        background: rgba(30, 42, 74, 0.7);
        border: 1px solid #2A3D5F;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    /* Main header */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
        padding: 1rem;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }

    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #667eea;
    }

    /* Dataframe styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Success/Error messages */
    .stAlert {
        border-radius: 8px;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E2A4A 0%, #0F1A2F 100%);
    }

    /* Login page specific */
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding-top: 100px;
    }

    /* Tooltips */
    [data-testid="stTooltip"] {
        border-radius: 8px;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }

        .metric-card {
            padding: 1rem;
        }
    }

    /* Real-time activity styling */
    .activity-item {
        padding: 0.5rem;
        border-bottom: 1px solid #2A3D5F;
        transition: background-color 0.3s ease;
    }

    .activity-item:hover {
        background-color: rgba(102, 126, 234, 0.1);
    }

    /* Progress animation */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }

    .pulse-animation {
        animation: pulse 2s infinite;
    }

    /* Template selector styling */
    .template-selector {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    /* Template preview */
    .template-preview {
        background: rgba(30, 42, 74, 0.9);
        border: 1px solid #2A3D5F;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="SAM Creative Solutions - Dynamic Template Outreach Pro",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Force session persistence
    if not hasattr(st, 'already_started'):
        st.already_started = True

    # Load CSS Theme
    load_css()

    # Initialize critical session states if they don't exist
    required_states = ['logged_in', 'email_history', 'smtp_configured', 'ai_mode',
                       'sent_count', 'failed_count', 'login_attempts', 'recent_activity',
                       'template_selection_mode', 'selected_template_id']

    for state in required_states:
        if state not in st.session_state:
            if state == 'logged_in':
                st.session_state[state] = False
            elif state == 'email_history':
                st.session_state[state] = []
            elif state in ['sent_count', 'failed_count', 'login_attempts']:
                st.session_state[state] = 0
            elif state == 'ai_mode':
                st.session_state[state] = True
            elif state == 'smtp_configured':
                st.session_state[state] = False
            elif state == 'recent_activity':
                st.session_state[state] = []
            elif state == 'template_selection_mode':
                st.session_state[state] = 'auto_detect'
            elif state == 'selected_template_id':
                st.session_state[state] = None

    # Check session timeout (8 hours)
    if 'login_timestamp' in st.session_state and st.session_state.login_timestamp > 0:
        session_timeout = 8 * 60 * 60  # 8 hours in seconds
        if time.time() - st.session_state.login_timestamp > session_timeout:
            st.session_state.logged_in = False
            st.warning("Session expired. Please login again.")
            time.sleep(2)
            st.rerun()

    # Check if user is logged in
    if not st.session_state.logged_in:
        render_login()
        return

    # Initialize system after successful login
    if 'system' not in st.session_state:
        st.session_state.system = EnhancedOutreachSystem()

    system = st.session_state.system

    # Modern Header
    st.markdown('<div class="main-header">🚀 SAM Creative Solutions - Dynamic Template Outreach Pro</div>',
                unsafe_allow_html=True)

    # Sidebar
    ModernSidebar.render_sidebar(system)

    # Main Content with Enhanced Tab Structure
    main_tab1, main_tab2, main_tab3, main_tab4 = st.tabs(["📊 Dashboard", "📧 Outreach", "📈 Analytics", "⚙️ Admin"])

    with main_tab1:
        st.header("📊 Campaign Dashboard")

        # Add real-time refresh button
        col_header1, col_header2, col_header3 = st.columns([4, 1, 1])
        with col_header2:
            refresh_status = "🟢 Live" if st.session_state.get('processing', False) else "🟡 Idle"
            st.metric("Status", refresh_status)
        with col_header3:
            if st.button("🔄 Refresh", use_container_width=True, key="refresh_dashboard_main"):
                st.session_state.dashboard_updates = {'last_refresh': datetime.now()}
                st.rerun()

        # Overview Metrics
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            total_sent = st.session_state.get('sent_count', 0)
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin: 0; color: #aaa; font-size: 0.9rem;">Total Sent</h3>
                <p style="margin: 0; color: #00D4AA; font-size: 2rem; font-weight: 700;">{total_sent}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            failed_count = st.session_state.get('failed_count', 0)
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin: 0; color: #aaa; font-size: 0.9rem;">Failed</h3>
                <p style="margin: 0; color: #FF6B6B; font-size: 2rem; font-weight: 700;">{failed_count}</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            success_rate = (total_sent / (total_sent + failed_count)) * 100 if (total_sent + failed_count) > 0 else 0
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin: 0; color: #aaa; font-size: 0.9rem;">Success Rate</h3>
                <p style="margin: 0; color: #F59E0B; font-size: 2rem; font-weight: 700;">{success_rate:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            template_mode = st.session_state.get('template_selection_mode', 'auto_detect')
            mode_text = "🤖 Auto" if template_mode == "auto_detect" else "🎯 Specific" if template_mode == "specific_template" else "🔄 Manual"
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin: 0; color: #aaa; font-size: 0.9rem;">Template Mode</h3>
                <p style="margin: 0; color: #667eea; font-size: 2rem; font-weight: 700;">{mode_text}</p>
            </div>
            """, unsafe_allow_html=True)

        with col5:
            total_templates = len(system.template_manager.templates)
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin: 0; color: #aaa; font-size: 0.9rem;">Templates</h3>
                <p style="margin: 0; color: #764ba2; font-size: 2rem; font-weight: 700;">{total_templates}</p>
            </div>
            """, unsafe_allow_html=True)

        with col6:
            email_status = "🟢 Connected" if st.session_state.get('smtp_configured', False) else "🔴 Disconnected"
            status_color = "#00D4AA" if st.session_state.get('smtp_configured', False) else "#FF6B6B"
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin: 0; color: #aaa; font-size: 0.9rem;">Email Service</h3>
                <p style="margin: 0; color: {status_color}; font-size: 2rem; font-weight: 700;">{email_status}</p>
            </div>
            """, unsafe_allow_html=True)

        # Stage Progress with real data
        st.subheader("📈 Stage Progress")
        progress_cols = st.columns(4)
        stages = ["Initial Outreach", "Follow-up 1", "Follow-up 2", "Follow-up 3"]

        for i, stage in enumerate(stages):
            with progress_cols[i]:
                stage_data = system.stage_manager.get_stage_data(stage)

                if stage_data is not None and not stage_data.empty:
                    total = len(stage_data)
                    sent = len(stage_data[stage_data['Status'].str.contains('Sent', na=False)])
                    pending = total - sent
                    progress = (sent / total) * 100 if total > 0 else 0

                    # Determine progress color
                    if progress >= 80:
                        progress_color = "#00D4AA"
                    elif progress >= 50:
                        progress_color = "#F59E0B"
                    else:
                        progress_color = "#667eea"

                    st.markdown(f"""
                    <div class="stage-indicator">
                        <div style="text-align: center;">
                            <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem; color: #fff;">{stage}</div>
                            <div style="font-size: 1.8rem; font-weight: 700; color: {progress_color}; margin-bottom: 0.5rem;">
                                {sent}<span style="font-size: 1rem; color: #aaa;">/{total}</span>
                            </div>
                            <div style="background: #2A3D5F; border-radius: 10px; height: 10px; margin: 0.5rem 0; overflow: hidden;">
                                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                         width: {progress}%; height: 100%; border-radius: 10px;"></div>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #aaa; margin-top: 0.5rem;">
                                <span>✅ {sent}</span>
                                <span>⏳ {pending}</span>
                            </div>
                            <div style="font-size: 0.8rem; color: #aaa; margin-top: 0.25rem;">{progress:.1f}% Complete</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="stage-indicator">
                        <div style="text-align: center;">
                            <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem; color: #fff;">{stage}</div>
                            <div style="font-size: 1.8rem; font-weight: 700; color: #666; margin-bottom: 0.5rem;">
                                0/0
                            </div>
                            <div style="background: #2A3D5F; border-radius: 10px; height: 10px; margin: 0.5rem 0; overflow: hidden;">
                                <div style="background: #666; width: 0%; height: 100%; border-radius: 10px;"></div>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #aaa; margin-top: 0.5rem;">
                                <span>✅ 0</span>
                                <span>⏳ 0</span>
                            </div>
                            <div style="font-size: 0.8rem; color: #aaa; margin-top: 0.25rem;">0% Complete</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # Template Usage Overview
        st.subheader("🎯 Template Usage Overview")

        if st.session_state.email_history:
            # Count template usage from email history
            template_counts = {}
            for email in st.session_state.email_history:
                template_id = email.get('template_id')
                if template_id:
                    template_counts[template_id] = template_counts.get(template_id, 0) + 1

            if template_counts:
                # Show top 5 templates
                top_templates = sorted(template_counts.items(), key=lambda x: x[1], reverse=True)[:5]

                cols = st.columns(5)
                for i, (template_id, count) in enumerate(top_templates):
                    with cols[i]:
                        template_name = system.template_manager.templates.get(template_id, {}).get('name', template_id)
                        st.metric(template_name[:15] + "..." if len(template_name) > 15 else template_name, count)
            else:
                st.info("📊 No template usage data yet")
        else:
            st.info("📭 No emails sent yet")

        # Add Recent Activity Section with Lead Names and Templates
        st.subheader("🔄 Recent Email Activity")

        activity_container = st.container()

        with activity_container:
            # Check for real-time updates during processing
            if st.session_state.get('processing', False):
                st.info("⏳ Processing emails in real-time...")
                # Show pulsing animation
                st.markdown(
                    '<div class="pulse-animation" style="text-align: center; padding: 1rem;">⚡ Live Updates Active</div>',
                    unsafe_allow_html=True)

            # Show recent activity from session state
            if st.session_state.recent_activity:
                recent_activity = st.session_state.recent_activity[-15:]  # Show last 15
                recent_activity.reverse()  # Show newest first

                for activity in recent_activity:
                    timestamp = activity.get('timestamp', datetime.now())
                    if isinstance(timestamp, str):
                        try:
                            timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                        except:
                            pass

                    time_ago = system._get_time_ago(timestamp)
                    template_id = activity.get('template', 'Unknown')
                    template_name = system.template_manager.templates.get(template_id, {}).get('name', template_id)

                    col_act1, col_act2, col_act3, col_act4 = st.columns([1, 2, 1, 1])
                    with col_act1:
                        status_icon = activity.get('status', '⏳')
                        st.write(f"**{status_icon}**")
                    with col_act2:
                        lead_name = activity.get('lead_name', 'Unknown')
                        stage = activity.get('stage', 'Unknown Stage')
                        st.write(f"**{lead_name}**")
                        st.caption(f"{stage} | {template_name[:20]}{'...' if len(template_name) > 20 else ''}")
                    with col_act3:
                        st.write(f"`{time_ago}`")
                    with col_act4:
                        # Quick preview button
                        if st.button("👁️", key=f"preview_{hash(str(activity))}"):
                            st.session_state[f"show_preview_{hash(str(activity))}"] = True

                    # Show preview if clicked
                    if st.session_state.get(f"show_preview_{hash(str(activity))}", False):
                        with st.expander("📧 Email Preview", expanded=True):
                            # Find the email in history
                            for email in st.session_state.email_history:
                                if (email.get('name') == activity.get('lead_name') and
                                        email.get('timestamp') == activity.get('timestamp')):
                                    st.write("**Subject:**")
                                    st.code(email.get('subject', 'No subject'))
                                    st.write("**Body Preview:**")
                                    preview = email.get('body', 'No body')[:300] + "..." if len(
                                        email.get('body', '')) > 300 else email.get('body', '')
                                    st.text(preview)
                                    break

                    st.divider()
            else:
                st.info("📭 No recent email activity")

        # Quick Actions
        st.subheader("⚡ Quick Actions")
        action_cols = st.columns(5)

        with action_cols[0]:
            if st.button("🔄 Update All Sheets", use_container_width=True, help="Update all connected Google Sheets"):
                success_count = 0
                for stage in stages:
                    if system.export_to_google_sheets(stage):
                        success_count += 1
                if success_count > 0:
                    st.success(f"✅ Updated {success_count} Google Sheets!")
                else:
                    st.info("ℹ️ No Google Sheets connected or configured for update")

        with action_cols[1]:
            # Export all data as Excel
            all_data = []
            for stage in stages:
                stage_df = system.stage_manager.export_stage_data(stage)
                if stage_df is not None and not stage_df.empty:
                    stage_df['Source_Stage'] = stage
                    all_data.append(stage_df)

            if all_data:
                combined_df = pd.concat(all_data, ignore_index=True)
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    combined_df.to_excel(writer, index=False, sheet_name='All_Stages_Data')
                excel_buffer.seek(0)

                st.download_button(
                    "📥 Export All Data",
                    excel_buffer,
                    "all_outreach_data.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    help="Download all campaign data as Excel file"
                )

        with action_cols[2]:
            # Export email history as Excel
            history_df = system.email_history.export_to_dataframe()
            if history_df is not None and not history_df.empty:
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    history_df.to_excel(writer, index=False, sheet_name='Email_History')
                excel_buffer.seek(0)

                st.download_button(
                    "📨 Export Email History",
                    excel_buffer,
                    "email_history.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    help="Download complete email history with template info"
                )

        with action_cols[3]:
            # Export templates
            if st.button("📋 Export Templates", use_container_width=True, help="Export all templates"):
                filename = system.template_manager.export_templates("json")
                with open(filename, 'rb') as f:
                    st.download_button(
                        "⬇️ Download Templates",
                        f,
                        filename,
                        "application/json",
                        use_container_width=True,
                        key="export_templates_btn"
                    )

        with action_cols[4]:
            if st.button("📊 Force Refresh", use_container_width=True, help="Force refresh all dashboard metrics"):
                st.session_state.dashboard_updates = {'last_refresh': datetime.now()}
                st.rerun()

        # Current Template Mode Overview
        st.subheader("🎯 Current Template Configuration")

        col_mode1, col_mode2 = st.columns([2, 1])

        with col_mode1:
            template_mode = st.session_state.get('template_selection_mode', 'auto_detect')

            if template_mode == "auto_detect":
                st.success("**🤖 Auto-detect Mode Active**")
                st.info("System will automatically select the best template based on lead description keywords.")

                # Show template detection stats
                template_stats = system.template_manager.get_template_statistics()
                st.caption(
                    f"📊 {template_stats['total_templates']} templates with {template_stats['total_keywords']} keywords available for detection")

            elif template_mode == "specific_template":
                selected_id = st.session_state.get('selected_template_id')
                if selected_id:
                    template_name = system.template_manager.templates.get(selected_id, {}).get('name', 'Unknown')
                    st.success(f"**🎯 Specific Template Mode Active**")
                    st.info(f"Using template: **{template_name}**")

                    # Show template info
                    template = system.template_manager.get_template(selected_id)
                    if template:
                        with st.expander("📧 Template Preview", expanded=False):
                            st.write("**Sample Subject:**")
                            st.code(template["subject"].format(name="John Doe"))
                            st.write("**Body Preview:**")
                            preview = template["body"].format(name="John Doe")
                            st.text(preview[:200] + "..." if len(preview) > 200 else preview)
                else:
                    st.warning("**⚠️ No template selected**")
                    st.info("Please select a specific template in the Outreach tab.")

            elif template_mode == "manual_select":
                st.success("**🔄 Manual Selection Mode Active**")
                st.info("Template selection will be based on 'Selected_Template' column in your data.")

        with col_mode2:
            # Quick template switch
            st.markdown("**Quick Settings**")

            if st.button("Switch to Auto-detect", use_container_width=True):
                system.set_template_selection_mode("auto_detect")
                st.success("Switched to Auto-detect mode!")
                st.rerun()

            # Show most used template
            if st.session_state.email_history:
                template_counts = {}
                for email in st.session_state.email_history:
                    template_id = email.get('template_id')
                    if template_id:
                        template_counts[template_id] = template_counts.get(template_id, 0) + 1

                if template_counts:
                    most_used = max(template_counts.items(), key=lambda x: x[1])
                    template_name = system.template_manager.templates.get(most_used[0], {}).get('name', most_used[0])
                    st.metric("Most Used Template",
                              f"{template_name[:15]}..." if len(template_name) > 15 else template_name)

    with main_tab2:
        # Outreach sub-tabs
        outreach_tab1, outreach_tab2, outreach_tab3, outreach_tab4 = st.tabs([
            "📧 Initial Outreach", "🔄 Follow-up 1", "📞 Follow-up 2", "⏰ Follow-up 3"
        ])

        with outreach_tab1:
            render_followup_stage_tab(system, "Initial Outreach")

        with outreach_tab2:
            render_followup_stage_tab(system, "Follow-up 1")

        with outreach_tab3:
            render_followup_stage_tab(system, "Follow-up 2")

        with outreach_tab4:
            render_followup_stage_tab(system, "Follow-up 3")

    with main_tab3:
        # Analytics Dashboard
        system.analytics_dashboard.render_dashboard()

    with main_tab4:
        # Admin Panel - Now includes Template Editor
        system.admin_panel.render_admin_panel()


if __name__ == "__main__":
    main()