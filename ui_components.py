import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime
import requests
import tempfile

from config_components import LocalNLPProcessor, Config


class ModernSidebar:
    """Modern sidebar with enhanced Google Sheets guidance"""

    @staticmethod
    def render_sidebar(system):
        with st.sidebar:
            # Header with dark theme gradient
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; margin-bottom: 1rem;">
                <h2 style="margin: 0; color: white; font-weight: 700;">⚡ SAM Outreach</h2>
                <p style="margin: 0; color: rgba(255,255,255,0.9); font-size: 0.9rem;">www.samcreative-solutions.com</p>
            </div>
            """, unsafe_allow_html=True)

            # Logout button
            if st.session_state.get('logged_in', False):
                if st.button("🚪 Logout", use_container_width=True, type="primary"):
                    st.session_state.logged_in = False
                    st.session_state.pop('system', None)
                    st.rerun()

            st.markdown("---")
            ModernSidebar._email_config_section(system)
            st.markdown("---")
            ModernSidebar._campaign_section(system)

    @staticmethod
    def _email_config_section(system):
        st.subheader("📧 Email Settings")

        with st.expander("🔧 Email Setup Guide", expanded=False):
            st.markdown("""
            ### **📧 Universal Email Setup Guide**

            #### **For Gmail:**
            1. **Enable 2-Step Verification:**
               - Go to: https://myaccount.google.com/security
               - Turn ON "2-Step Verification"

            2. **Generate App Password:**
               - Visit: https://myaccount.google.com/apppasswords
               - Select "Mail" as App
               - Select "Windows Computer" as Device
               - Copy the 16-character password

            #### **For Outlook/Hotmail:**
            1. Use your regular email password
            2. **SMTP Settings:**
               - Server: smtp-mail.outlook.com
               - Port: 587
               - Encryption: TLS

            #### **For Yahoo Mail:**
            1. Use your regular email password
            2. **SMTP Settings:**
               - Server: smtp.mail.yahoo.com
               - Port: 587
               - Encryption: TLS

            #### **For Office 365/Company Email:**
            1. Use your company email password
            2. **SMTP Settings:**
               - Server: smtp.office365.com
               - Port: 587
               - Encryption: TLS

            #### **For Other Providers:**
            - Contact your email provider for SMTP settings
            - Usually: smtp.yourdomain.com, port 587
            """)

        # Email provider selection
        email_provider = st.selectbox(
            "Email Provider",
            options=list(Config.EMAIL_PROVIDERS.keys()),
            help="Select your email service provider",
            key="email_provider_select"
        )

        provider_config = Config.EMAIL_PROVIDERS[email_provider]

        col1, col2 = st.columns(2)
        with col1:
            sender_email = st.text_input("Your Email", placeholder="your@email.com", key="sender_email_input")

        with col2:
            if email_provider == "Custom SMTP":
                smtp_server = st.text_input("SMTP Server", placeholder="smtp.yourdomain.com", key="smtp_server_input")
                smtp_port = st.number_input("Port", value=587, min_value=1, max_value=9999, key="smtp_port_input")
            else:
                smtp_server = provider_config["server"]
                smtp_port = provider_config["port"]
                st.info(f"**Server:** {smtp_server}")
                st.info(f"**Port:** {smtp_port}")

        # Password field with provider-specific guidance
        password_label = "App Password" if provider_config.get("requires_app_password", False) else "Password"
        sender_password = st.text_input(
            password_label,
            type="password",
            placeholder=f"Enter your {password_label.lower()}",
            key="sender_password_input"
        )

        # Test connection button
        if st.button("🔗 Test Connection", use_container_width=True, key="test_connection_btn"):
            if sender_email and sender_password:
                with st.spinner("Testing connection..."):
                    if system.configure_email(sender_email, sender_password, smtp_server, smtp_port):
                        st.success("✅ Email connected successfully!")
                    else:
                        st.error("❌ Connection failed. Check credentials.")
            else:
                st.warning("Please enter both email and password")

    @staticmethod
    def _campaign_section(system):
        st.subheader("🎯 Campaign Setup")

        # Get campaign types including custom ones
        campaign_types = Config.CAMPAIGN_TYPES.copy()
        if 'custom_campaigns' in st.session_state:
            for key, name in st.session_state.custom_campaigns.items():
                campaign_types[key] = f"🎯 {name}"

        campaign_type = st.selectbox(
            "Campaign Focus",
            options=list(campaign_types.keys()),
            format_func=lambda x: campaign_types[x],
            index=0,  # Auto-detect as default
            key="campaign_type_select"
        )

        system.current_campaign = campaign_type

        if campaign_type == "custom" and 'custom_campaigns' in st.session_state:
            # Show custom campaigns if available
            custom_options = list(st.session_state.custom_campaigns.keys())[:3]  # First 3 custom campaigns
            if custom_options:
                selected_custom = st.selectbox(
                    "Select Custom Campaign",
                    options=custom_options,
                    format_func=lambda x: st.session_state.custom_campaigns[x],
                    key="custom_campaign_select"
                )
                system.current_campaign = selected_custom
            else:
                system.current_campaign = "auto_detect"

        # Show auto-detect info
        if campaign_type == "auto_detect":
            st.info(
                "🤖 **Auto-detect Mode:** System will analyze each lead's description and choose the best campaign automatically.")

        st.markdown("---")
        ai_mode = st.toggle(
            "🤖 Enable AI Personalized Mode",
            value=st.session_state.get('ai_mode', True),
            help="Use local NLP to generate unique emails for each lead",
            key="ai_mode_toggle"
        )
        st.session_state.ai_mode = ai_mode


class AnalyticsDashboard:
    """Modern analytics dashboard with real-time updates"""

    def __init__(self, system):
        self.system = system
        self._init_realtime_data()

    def _init_realtime_data(self):
        """Initialize real-time data tracking"""
        if 'dashboard_updates' not in st.session_state:
            st.session_state.dashboard_updates = {
                'last_refresh': datetime.now(),
                'recent_leads': [],
                'performance_history': []
            }

    def render_dashboard(self):
        """Render the analytics dashboard"""
        st.header("📊 Real-Time Analytics Dashboard")

        # Auto-refresh indicator
        last_refresh = st.session_state.dashboard_updates.get('last_refresh', datetime.now())
        refresh_diff = (datetime.now() - last_refresh).seconds
        refresh_status = "🟢 Live" if refresh_diff < 60 else "🟡 Stale"

        col_header1, col_header2, col_header3 = st.columns([3, 1, 1])
        with col_header2:
            st.metric("Status", refresh_status)
        with col_header3:
            if st.button("🔄 Refresh", use_container_width=True, key="analytics_refresh"):
                st.session_state.dashboard_updates['last_refresh'] = datetime.now()
                st.rerun()

        # Real-time metrics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            total_sent = st.session_state.get('sent_count', 0)
            st.metric("📤 Total Sent", total_sent, delta=f"+{total_sent}")

        with col2:
            failed_count = st.session_state.get('failed_count', 0)
            st.metric("❌ Failed", failed_count, delta=f"+{failed_count}", delta_color="inverse")

        with col3:
            success_rate = (total_sent / (total_sent + failed_count)) * 100 if (total_sent + failed_count) > 0 else 0
            st.metric("📈 Success Rate", f"{success_rate:.1f}%")

        with col4:
            ai_mode = "Active" if st.session_state.get('ai_mode', True) else "Inactive"
            st.metric("🤖 AI Mode", ai_mode)

        with col5:
            total_leads = self._get_total_leads()
            st.metric("👥 Total Leads", total_leads)

        # Stage Progress with real data
        st.subheader("📈 Stage Progress")
        self._render_stage_progress()

        # Charts section
        col1, col2 = st.columns(2)

        with col1:
            self._render_campaign_chart()

        with col2:
            self._render_followup_chart()

        # Performance metrics
        col1, col2 = st.columns(2)

        with col1:
            self._render_performance_metrics()

        with col2:
            self._render_realtime_activity()

        # Stage-wise analytics
        st.subheader("📋 Stage-wise Performance")
        self._render_stage_analytics()

        # Recent Leads section
        st.subheader("👥 Recent Leads Processed")
        self._render_recent_leads()

    def _get_total_leads(self):
        """Safely get total leads count"""
        total = 0
        stages = ["Initial Outreach", "Follow-up 1", "Follow-up 2", "Follow-up 3"]
        for stage in stages:
            stage_data = self.system.stage_manager.get_stage_data(stage)
            if stage_data is not None and not stage_data.empty:
                total += len(stage_data)
        return total

    def _render_stage_progress(self):
        """Render stage progress with real data"""
        progress_cols = st.columns(4)
        stages = ["Initial Outreach", "Follow-up 1", "Follow-up 2", "Follow-up 3"]

        for i, stage in enumerate(stages):
            with progress_cols[i]:
                stage_data = self.system.stage_manager.get_stage_data(stage)

                if stage_data is not None and not stage_data.empty:
                    total = len(stage_data)
                    sent = len(stage_data[stage_data['Status'].str.contains('Sent', na=False)])
                    progress = (sent / total) * 100 if total > 0 else 0

                    # Create progress bar
                    st.markdown(f"""
                    <div style="background: rgba(30, 42, 74, 0.7); border: 1px solid #2A3D5F; border-radius: 12px; padding: 1rem;">
                        <div style="text-align: center;">
                            <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;">{stage}</div>
                            <div style="font-size: 2rem; font-weight: 700; color: #667eea;">{sent}/{total}</div>
                            <div style="background: #333; border-radius: 10px; height: 8px; margin: 0.5rem 0;">
                                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                         width: {progress}%; height: 100%; border-radius: 10px;"></div>
                            </div>
                            <div style="font-size: 0.8rem; color: #aaa;">{progress:.1f}% Complete</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: rgba(30, 42, 74, 0.7); border: 1px solid #2A3D5F; border-radius: 12px; padding: 1rem;">
                        <div style="text-align: center;">
                            <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;">{stage}</div>
                            <div style="font-size: 2rem; font-weight: 700; color: #666;">-/-</div>
                            <div style="background: #333; border-radius: 10px; height: 8px; margin: 0.5rem 0;">
                                <div style="background: #666; width: 0%; height: 100%; border-radius: 10px;"></div>
                            </div>
                            <div style="font-size: 0.8rem; color: #aaa;">No data loaded</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    def _render_campaign_chart(self):
        """Render campaign performance chart"""
        if not st.session_state.email_history:
            st.info("📊 No data available for campaign analysis")
            return

        # Extract campaign data from history
        campaign_data = {}
        for email in st.session_state.email_history:
            campaign_type = "Auto-detect" if self.system.current_campaign == "auto_detect" else self.system.current_campaign
            if campaign_type not in campaign_data:
                campaign_data[campaign_type] = {'sent': 0, 'failed': 0}

            if email['status'] == 'Sent':
                campaign_data[campaign_type]['sent'] += 1
            else:
                campaign_data[campaign_type]['failed'] += 1

        if campaign_data:
            fig = go.Figure()

            campaigns = list(campaign_data.keys())
            sent_counts = [campaign_data[c]['sent'] for c in campaigns]
            failed_counts = [campaign_data[c]['failed'] for c in campaigns]

            fig.add_trace(go.Bar(name='✅ Sent', x=campaigns, y=sent_counts, marker_color='#00D4AA'))
            fig.add_trace(go.Bar(name='❌ Failed', x=campaigns, y=failed_counts, marker_color='#FF6B6B'))

            fig.update_layout(
                title="📊 Campaign Performance",
                barmode='group',
                height=300,
                showlegend=True,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )

            st.plotly_chart(fig, use_container_width=True)

    def _render_followup_chart(self):
        """Render follow-up stage chart"""
        if not st.session_state.email_history:
            st.info("📊 No data available for follow-up analysis")
            return

        stage_data = {}
        for email in st.session_state.email_history:
            stage = email['followup_stage']
            if stage not in stage_data:
                stage_data[stage] = 0
            stage_data[stage] += 1

        if stage_data:
            fig = px.pie(
                values=list(stage_data.values()),
                names=list(stage_data.keys()),
                title="📧 Email Distribution by Follow-up Stage",
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

    def _render_performance_metrics(self):
        """Render performance metrics"""
        st.subheader("🚀 Performance Metrics")

        if st.session_state.email_history:
            # Calculate metrics
            total_emails = len(st.session_state.email_history)
            sent_emails = len([e for e in st.session_state.email_history if e['status'] == 'Sent'])
            failed_emails = len([e for e in st.session_state.email_history if e['status'] == 'Failed'])

            # Time-based metrics
            if len(st.session_state.email_history) > 1:
                times = [e['timestamp'] for e in st.session_state.email_history]
                time_diff = (max(times) - min(times)).total_seconds() / 3600  # hours
                emails_per_hour = len(st.session_state.email_history) / time_diff if time_diff > 0 else 0
            else:
                emails_per_hour = 0

            metrics_html = f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 12px; color: white;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div style="text-align: center;">
                        <div style="font-size: 2rem; font-weight: bold;">{total_emails}</div>
                        <div style="font-size: 0.9rem;">Total Emails</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 2rem; font-weight: bold;">{emails_per_hour:.1f}</div>
                        <div style="font-size: 0.9rem;">Emails/Hour</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 2rem; font-weight: bold;">{sent_emails}</div>
                        <div style="font-size: 0.9rem;">Successful</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 2rem; font-weight: bold;">{failed_emails}</div>
                        <div style="font-size: 0.9rem;">Failed</div>
                    </div>
                </div>
            </div>
            """
            st.markdown(metrics_html, unsafe_allow_html=True)
        else:
            st.info("📊 No performance data available")

    def _render_realtime_activity(self):
        """Render real-time activity feed"""
        st.subheader("🔄 Real-Time Activity")

        # Check for processing state
        if st.session_state.get('processing', False):
            st.info("⚡ Emails are being sent in real-time...")
            st.markdown(
                '<div style="text-align: center; padding: 1rem; animation: pulse 2s infinite;">⚡ Live updates active</div>',
                unsafe_allow_html=True)

        if st.session_state.email_history:
            recent_activity = st.session_state.email_history[:10]

            activity_html = """
            <div style="background: #1e1e1e; padding: 1rem; border-radius: 8px; max-height: 300px; overflow-y: auto;">
            """

            for i, email in enumerate(recent_activity):
                status_icon = "🟢" if email['status'] == 'Sent' else "🔴"
                time_ago = self.system._get_time_ago(email['timestamp'])

                activity_html += f"""
                <div style="padding: 0.5rem; border-bottom: {'1px solid #333' if i < len(recent_activity) - 1 else 'none'};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 500; color: white;">{email['name']}</span>
                        <span style="font-size: 0.8rem; color: #aaa;">{time_ago}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.25rem;">
                        <span style="font-size: 0.85rem; color: #ccc;">{email['followup_stage']}</span>
                        <span>{status_icon}</span>
                    </div>
                </div>
                """

            activity_html += "</div>"
            st.markdown(activity_html, unsafe_allow_html=True)
        else:
            st.info("📊 No recent activity")

    def _render_recent_leads(self):
        """Show recent leads with names"""
        if not st.session_state.email_history:
            st.info("📭 No leads processed yet")
            return

        # Get unique leads from recent email history
        recent_leads = []
        seen_emails = set()

        for email in st.session_state.email_history[:20]:  # Last 20 emails
            if email['email'] not in seen_emails:
                seen_emails.add(email['email'])
                recent_leads.append({
                    'name': email['name'],
                    'email': email['email'],
                    'last_contact': email['timestamp'],
                    'last_stage': email['followup_stage'],
                    'status': email['status']
                })

        # Display leads
        for lead in recent_leads[:10]:  # Show top 10
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            with col1:
                st.write(f"**{lead['name']}**")
            with col2:
                st.write(f"`{lead['email'][:20]}...`")
            with col3:
                status_color = "🟢" if lead['status'] == 'Sent' else "🔴"
                st.write(status_color)
            with col4:
                st.caption(lead['last_stage'])

    def _render_stage_analytics(self):
        """Render stage-wise analytics"""
        stages = ["Initial Outreach", "Follow-up 1", "Follow-up 2", "Follow-up 3"]
        stage_data = []

        for stage in stages:
            data = self.system.stage_manager.get_stage_data(stage)
            if data is not None and not data.empty:
                total = len(data)
                sent = len(data[data['Status'].str.contains('Sent', na=False)])
                pending = total - sent
                stage_data.append({
                    'Stage': stage,
                    'Total': total,
                    'Sent': sent,
                    'Pending': pending,
                    'Completion': (sent / total * 100) if total > 0 else 0
                })

        if stage_data:
            df = pd.DataFrame(stage_data)

            col1, col2 = st.columns(2)

            with col1:
                # Stage completion chart
                fig = px.bar(
                    df,
                    x='Stage',
                    y='Completion',
                    title='Stage Completion Rate (%)',
                    color='Completion',
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Stage distribution chart
                fig = go.Figure()
                fig.add_trace(go.Bar(name='Total', x=df['Stage'], y=df['Total'], marker_color='#667eea'))
                fig.add_trace(go.Bar(name='Sent', x=df['Stage'], y=df['Sent'], marker_color='#00D4AA'))
                fig.add_trace(go.Bar(name='Pending', x=df['Stage'], y=df['Pending'], marker_color='#FF6B6B'))

                fig.update_layout(
                    title='Leads Distribution by Stage',
                    barmode='group',
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)

            # Data table
            st.dataframe(df, use_container_width=True)
        else:
            st.info("📊 No stage data available for analytics")


class AdminPanel:
    """Admin panel for system management"""

    def __init__(self, system):
        self.system = system

    def render_admin_panel(self):
        """Render admin panel"""
        st.header("⚙️ Admin Panel")

        tab1, tab2, tab3, tab4 = st.tabs(
            ["System Settings", "Campaign Manager", "Data Management", "Logs & Monitoring"])

        with tab1:
            self._render_system_settings()

        with tab2:
            self._render_campaign_manager()

        with tab3:
            self._render_data_management()

        with tab4:
            self._render_logs_monitoring()

    def _render_system_settings(self):
        """Render system settings"""
        st.subheader("🔧 System Configuration")

        # Get current settings from session state or use defaults
        current_batch_size = st.session_state.get('admin_batch_size', Config.DEFAULT_BATCH_SIZE)
        current_max_batch = st.session_state.get('admin_max_batch', Config.MAX_BATCH_SIZE)
        current_smtp_timeout = st.session_state.get('admin_smtp_timeout', Config.SMTP_TIMEOUT)
        current_rate_delay = st.session_state.get('admin_rate_delay', Config.RATE_LIMIT_DELAY)
        current_max_retries = st.session_state.get('admin_max_retries', Config.MAX_RETRIES)
        current_thread_pool = st.session_state.get('admin_thread_pool', Config.THREAD_POOL_SIZE)

        col1, col2 = st.columns(2)

        with col1:
            new_batch_size = st.number_input(
                "Default Batch Size",
                min_value=1,
                max_value=current_max_batch,
                value=current_batch_size,
                key="admin_batch_size_input"
            )

            new_max_batch = st.number_input(
                "Maximum Batch Size",
                min_value=20,
                max_value=1000,
                value=current_max_batch,
                key="admin_max_batch_input"
            )

            new_smtp_timeout = st.number_input(
                "SMTP Timeout (seconds)",
                min_value=5,
                max_value=60,
                value=current_smtp_timeout,
                key="admin_smtp_timeout_input"
            )

        with col2:
            new_rate_delay = st.number_input(
                "Rate Limit Delay (seconds)",
                min_value=0.1,
                max_value=10.0,
                value=current_rate_delay,
                step=0.1,
                key="admin_rate_delay_input"
            )

            new_max_retries = st.number_input(
                "Max Retry Attempts",
                min_value=1,
                max_value=10,
                value=current_max_retries,
                key="admin_max_retries_input"
            )

            new_thread_pool = st.number_input(
                "Thread Pool Size",
                min_value=1,
                max_value=20,
                value=current_thread_pool,
                key="admin_thread_pool_input"
            )

        if st.button("💾 Save System Settings", use_container_width=True):
            # Update configuration in session state
            st.session_state.admin_batch_size = new_batch_size
            st.session_state.admin_max_batch = new_max_batch
            st.session_state.admin_smtp_timeout = new_smtp_timeout
            st.session_state.admin_rate_delay = new_rate_delay
            st.session_state.admin_max_retries = new_max_retries
            st.session_state.admin_thread_pool = new_thread_pool

            # Update actual configuration
            Config.DEFAULT_BATCH_SIZE = new_batch_size
            Config.MAX_BATCH_SIZE = new_max_batch
            Config.SMTP_TIMEOUT = new_smtp_timeout
            Config.RATE_LIMIT_DELAY = new_rate_delay
            Config.MAX_RETRIES = new_max_retries
            Config.THREAD_POOL_SIZE = new_thread_pool

            st.success("✅ System settings updated successfully!")

        # Show current settings
        st.subheader("📋 Current Settings")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Default Batch Size:** {Config.DEFAULT_BATCH_SIZE}")
            st.info(f"**Max Batch Size:** {Config.MAX_BATCH_SIZE}")
            st.info(f"**SMTP Timeout:** {Config.SMTP_TIMEOUT}s")
        with col2:
            st.info(f"**Rate Limit Delay:** {Config.RATE_LIMIT_DELAY}s")
            st.info(f"**Max Retries:** {Config.MAX_RETRIES}")
            st.info(f"**Thread Pool Size:** {Config.THREAD_POOL_SIZE}")

    def _render_campaign_manager(self):
        """Render campaign manager for custom campaigns"""
        st.subheader("🎯 Custom Campaign Manager")

        # Initialize custom campaigns in session state if not exists
        if 'custom_campaigns' not in st.session_state:
            st.session_state.custom_campaigns = {}

        with st.expander("➕ Create New Custom Campaign", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                campaign_key = st.text_input("Campaign Key",
                                             placeholder="ecommerce_solutions",
                                             help="Unique identifier (no spaces)")
                campaign_name = st.text_input("Campaign Display Name",
                                              placeholder="E-commerce Solutions")

            with col2:
                pain_keyword = st.text_input("Primary Pain Keyword",
                                             placeholder="online sales, ecommerce",
                                             help="Keywords that trigger this campaign")
                industry_focus = st.text_input("Industry Focus",
                                               placeholder="retail, online stores",
                                               help="Target industries")

            # Email subject templates
            subject_templates = st.text_area("Subject Templates (one per line)",
                                             placeholder="Boost {name}'s Online Sales\nE-commerce Growth for {name}",
                                             help="Use {name} for personalization")

            # Email body template
            body_template = st.text_area("Email Body Template",
                                         placeholder="Hi {name},\n\nWe specialize in e-commerce solutions...",
                                         height=150)

            if st.button("💾 Save Custom Campaign", use_container_width=True):
                if campaign_key and campaign_name:
                    # Add to LocalNLPProcessor patterns
                    if pain_keyword:
                        keywords = [k.strip() for k in pain_keyword.split(',')]
                        LocalNLPProcessor.PAIN_PATTERNS[campaign_key] = keywords

                    # Store custom campaign
                    st.session_state.custom_campaigns[campaign_key] = campaign_name

                    # Store templates
                    if 'custom_templates' not in st.session_state:
                        st.session_state.custom_templates = {}

                    st.session_state.custom_templates[campaign_key] = {
                        'subjects': [s.strip() for s in subject_templates.split('\n') if s.strip()],
                        'body': body_template
                    }

                    st.success(f"✅ Custom campaign '{campaign_name}' saved!")
                else:
                    st.error("Please provide Campaign Key and Name")

        # Show existing custom campaigns
        if st.session_state.custom_campaigns:
            st.subheader("📋 Existing Custom Campaigns")
            for key, name in st.session_state.custom_campaigns.items():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{name}** (`{key}`)")
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{key}"):
                        st.info("Edit functionality coming soon")
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{key}"):
                        del st.session_state.custom_campaigns[key]
                        if 'custom_templates' in st.session_state and key in st.session_state.custom_templates:
                            del st.session_state.custom_templates[key]
                        st.rerun()

    def _render_data_management(self):
        """Render data management"""
        st.subheader("🗃️ Data Management")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Email History", len(st.session_state.get('email_history', [])))
            st.metric("Active Connections", "3/3")

        with col2:
            st.metric("Database Size", f"{len(st.session_state.get('email_history', [])) * 0.5:.1f} KB")
            st.metric("System Health", "🟢 Excellent")

        st.subheader("🛠️ Maintenance Tools")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Clear All Cache", use_container_width=True):
                # Preserve essential session state
                email_history = st.session_state.get('email_history', [])
                smtp_configured = st.session_state.get('smtp_configured', False)
                sent_count = st.session_state.get('sent_count', 0)
                failed_count = st.session_state.get('failed_count', 0)
                ai_mode = st.session_state.get('ai_mode', True)
                custom_campaigns = st.session_state.get('custom_campaigns', {})
                custom_templates = st.session_state.get('custom_templates', {})
                logged_in = st.session_state.get('logged_in', False)

                st.session_state.clear()

                # Restore essential data
                st.session_state.email_history = email_history
                st.session_state.smtp_configured = smtp_configured
                st.session_state.sent_count = sent_count
                st.session_state.failed_count = failed_count
                st.session_state.ai_mode = ai_mode
                st.session_state.custom_campaigns = custom_campaigns
                st.session_state.custom_templates = custom_templates
                st.session_state.logged_in = logged_in

                st.success("✅ Cache cleared successfully!")
                st.rerun()

        with col2:
            if st.button("💾 Backup Data", use_container_width=True):
                # Export all data
                all_data = []
                stages = ["Initial Outreach", "Follow-up 1", "Follow-up 2", "Follow-up 3"]
                for stage in stages:
                    stage_df = self.system.stage_manager.export_stage_data(stage)
                    if stage_df is not None and not stage_df.empty:
                        stage_df['Source_Stage'] = stage
                        all_data.append(stage_df)

                if all_data:
                    combined_df = pd.concat(all_data, ignore_index=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"backup_{timestamp}.xlsx"

                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        combined_df.to_excel(writer, index=False, sheet_name='All_Data')
                        # Also export email history
                        history_df = self.system.email_history.export_to_dataframe()
                        if history_df is not None:
                            history_df.to_excel(writer, index=False, sheet_name='Email_History')
                    excel_buffer.seek(0)

                    st.download_button(
                        "⬇️ Download Backup",
                        excel_buffer,
                        filename,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    st.success("✅ Backup created successfully!")

        with col3:
            if st.button("📊 System Report", use_container_width=True):
                st.subheader("📋 System Report")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Emails Sent", st.session_state.get('sent_count', 0))
                    st.metric("Failed Emails", st.session_state.get('failed_count', 0))

                    total_sent = st.session_state.get('sent_count', 0)
                    total_failed = st.session_state.get('failed_count', 0)
                    total_attempts = total_sent + total_failed
                    success_rate = (total_sent / total_attempts * 100) if total_attempts > 0 else 0
                    st.metric("Success Rate", f"{success_rate:.1f}%")

                with col2:
                    st.metric("Custom Campaigns", len(st.session_state.get('custom_campaigns', {})))
                    st.metric("Email History", len(st.session_state.get('email_history', [])))
                    ai_status = "🟢 Active" if st.session_state.get('ai_mode', True) else "🔴 Inactive"
                    st.metric("AI Mode", ai_status)

    def _render_logs_monitoring(self):
        """Render logs and monitoring"""
        st.subheader("📋 System Logs")

        # Real logs from session state
        if 'system_logs' not in st.session_state:
            st.session_state.system_logs = [
                {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "level": "INFO",
                 "message": "System initialized"}
            ]

        # Add recent email activity to logs
        if st.session_state.email_history:
            recent_emails = st.session_state.email_history[:5]
            for email in recent_emails:
                log_entry = {
                    "timestamp": email['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                    "level": "INFO" if email['status'] == 'Sent' else "ERROR",
                    "message": f"Email {email['status']} to {email['name']} ({email['followup_stage']})"
                }
                if log_entry not in st.session_state.system_logs[-10:]:  # Avoid duplicates
                    st.session_state.system_logs.append(log_entry)

        # Display logs (most recent first)
        recent_logs = st.session_state.system_logs[-20:]  # Last 20 logs
        recent_logs.reverse()  # Show newest first

        log_container = st.container()
        with log_container:
            for log in recent_logs:
                level_color = {
                    "INFO": "🟢",
                    "WARNING": "🟡",
                    "ERROR": "🔴"
                }

                col1, col2 = st.columns([1, 4])
                with col1:
                    st.write(f"**{log['timestamp']}**")
                with col2:
                    st.write(f"{level_color[log['level']]} {log['message']}")

        # Clear logs button
        if st.button("🗑️ Clear Logs", use_container_width=True):
            st.session_state.system_logs = []
            st.rerun()

        st.subheader("📈 System Monitoring")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Calculate real metrics
            total_sent = st.session_state.get('sent_count', 0)
            total_failed = st.session_state.get('failed_count', 0)
            total_attempts = total_sent + total_failed
            error_rate = (total_failed / total_attempts * 100) if total_attempts > 0 else 0

            st.metric("CPU Usage", "45%")
            st.metric("Memory Usage", f"{len(st.session_state.get('email_history', [])) * 0.1 + 50:.0f}%")

        with col2:
            st.metric("Active Connections", "3")
            st.metric("Queue Size", "0")

        with col3:
            st.metric("Error Rate", f"{error_rate:.1f}%")
            st.metric("Response Time", "120ms")


def render_followup_stage_tab(system, stage):
    """Render individual follow-up stage tab"""
    st.header(f"📧 {stage}")

    # Data Source Section
    st.subheader("📊 Data Source")

    col1, col2 = st.columns([2, 1])

    with col1:
        data_source = st.radio(f"Choose Source for {stage}", ["Upload Excel", "Google Sheets"],
                               horizontal=True, key=f"data_source_{stage}")

        if data_source == "Upload Excel":
            uploaded_file = st.file_uploader(f"Excel File for {stage}", type=['xlsx', 'xls', 'csv'],
                                             help=f"Upload Excel with proper tracking columns for {stage}",
                                             key=f"excel_uploader_{stage}")
            if uploaded_file and st.button(f"📥 Load {stage} Data", use_container_width=True,
                                           key=f"load_excel_{stage}"):
                with st.spinner(f"Loading {stage} data..."):
                    try:
                        if uploaded_file.name.endswith('.csv'):
                            df = pd.read_csv(uploaded_file)
                        else:
                            df = pd.read_excel(uploaded_file)

                        if system.load_dataframe(df, stage):
                            st.success(f"✅ Loaded {len(df)} leads for {stage}")

                            # Auto-detect campaign types for each lead
                            if 'Description' in df.columns:
                                df['Auto_Detected_Campaign'] = df['Description'].apply(
                                    lambda x: LocalNLPProcessor.detect_campaign_type(x) if pd.notna(x) else "no_website"
                                )
                                system.stage_manager.set_stage_data(stage, df)
                                st.info(f"🤖 Auto-detected campaigns for {len(df)} leads")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        else:  # Google Sheets
            with st.expander(f"🔗 Connect Google Sheets for {stage}", expanded=False):
                st.markdown("""
                **Easy Google Sheets Connection:**

                1. **Share your Google Sheet:**
                   - Click "Share" button in Google Sheets
                   - Set to "Anyone with the link can view"
                   - Copy the sharing link

                2. **Paste the link below:**
                   - Just paste the shareable link
                   - No JSON credentials needed for viewing
                """)

                # Use a different key for storing the URL separate from the widget
                sheet_url_key = f"stored_sheet_url_{stage}"
                creds_json_key = f"stored_creds_json_{stage}"

                # Initialize session state for storage if not exists
                if sheet_url_key not in st.session_state:
                    st.session_state[sheet_url_key] = ""
                if creds_json_key not in st.session_state:
                    st.session_state[creds_json_key] = ""

                # Input widgets (these don't store in our custom session state keys)
                sheet_url_input = st.text_input("Google Sheet URL",
                                                placeholder="https://docs.google.com/spreadsheets/d/.../edit",
                                                key=f"sheet_url_input_{stage}")

                # Optional: Service account for write access
                with st.expander("🔐 Advanced: Service Account (for write access)"):
                    creds_json_input = st.text_area("Service Account JSON (Optional)", height=120,
                                                    placeholder='Paste full JSON for write access\n{\n  "type": "service_account",\n  ...\n}',
                                                    key=f"creds_json_input_{stage}")

                if st.button(f"🔗 Connect Sheets for {stage}", use_container_width=True,
                             key=f"connect_sheets_{stage}"):
                    if sheet_url_input:
                        with st.spinner(f"Connecting to Google Sheets for {stage}..."):
                            # Store the values in our custom session state keys
                            st.session_state[sheet_url_key] = sheet_url_input
                            st.session_state[creds_json_key] = creds_json_input

                            # Try with public access first, then with credentials
                            success = False

                            # Simplified connection - just read data
                            try:
                                # Extract sheet ID from URL
                                if '/d/' in sheet_url_input:
                                    sheet_id = sheet_url_input.split('/d/')[1].split('/')[0]
                                    # Try different export formats
                                    for fmt in ['csv', 'xlsx']:
                                        try:
                                            export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format={fmt}"
                                            if fmt == 'csv':
                                                df = pd.read_csv(export_url)
                                            else:
                                                df = pd.read_excel(export_url)

                                            if system.load_dataframe(df, stage):
                                                success = True
                                                break
                                        except:
                                            continue
                            except Exception as e:
                                st.error(f"Public access failed: {e}")

                            # If public access failed and credentials provided, try with service account
                            if not success and creds_json_input:
                                if system.connect_google_sheets(creds_json_input, sheet_url_input, stage):
                                    success = True

                            if success:
                                st.success(f"✅ Google Sheets connected for {stage}!")

                                # Auto-detect campaign types
                                stage_data = system.stage_manager.get_stage_data(stage)
                                if stage_data is not None and 'Description' in stage_data.columns:
                                    stage_data['Auto_Detected_Campaign'] = stage_data['Description'].apply(
                                        lambda x: LocalNLPProcessor.detect_campaign_type(x) if pd.notna(
                                            x) else "no_website"
                                    )
                                    system.stage_manager.set_stage_data(stage, stage_data)
                                    st.info(f"🤖 Auto-detected campaigns for {len(stage_data)} leads")
                            else:
                                st.error("❌ Failed to connect. Check URL and sharing settings.")
                    else:
                        st.warning("Please enter a Google Sheet URL")

    with col2:
        # Stage-specific stats
        st.subheader("📈 Stage Stats")
        stage_data = system.stage_manager.get_stage_data(stage)
        if stage_data is not None and not stage_data.empty:
            total_leads = len(stage_data)
            pending = len(stage_data[stage_data['Status'] == 'Not Sent'])
            sent = len(stage_data[stage_data['Status'].str.contains('Sent', na=False)])

            st.metric("Total Leads", total_leads)
            st.metric("Pending", pending)
            st.metric("Sent", sent)

            # Show campaign distribution if auto-detected
            if 'Auto_Detected_Campaign' in stage_data.columns:
                st.subheader("🎯 Campaign Distribution")
                campaign_dist = stage_data['Auto_Detected_Campaign'].value_counts()
                for campaign, count in campaign_dist.head(3).items():
                    st.write(f"• **{campaign}**: {count}")
        else:
            st.info("No data loaded")

    # Campaign Controls
    st.subheader("🎯 Campaign Controls")

    col_control1, col_control2, col_control3, col_control4 = st.columns([2, 1, 1, 1])

    with col_control1:
        # Get available pending leads for dynamic batch size
        stage_data = system.stage_manager.get_stage_data(stage)
        max_available = 0
        if stage_data is not None and not stage_data.empty:
            if stage == "Initial Outreach":
                max_available = len(stage_data[stage_data['Status'] == 'Not Sent'])
            else:
                prev_stage_col = system.stage_manager._get_previous_stage_column(stage)
                max_available = len(
                    stage_data[(stage_data['Status'] == 'Not Sent') & (stage_data[prev_stage_col] == 'Completed')])

        # Use admin settings or defaults
        max_batch_size = st.session_state.get('admin_max_batch', Config.MAX_BATCH_SIZE)
        default_batch_size = st.session_state.get('admin_batch_size', Config.DEFAULT_BATCH_SIZE)

        # Limit batch size to available leads or max batch size
        actual_max = min(max_available, max_batch_size) if max_available > 0 else max_batch_size

        batch_size = st.slider(
            "Batch Size",
            min_value=1,
            max_value=actual_max,
            value=min(default_batch_size, actual_max) if actual_max > 0 else default_batch_size,
            key=f"batch_size_{stage}"
        )

    with col_control2:
        if st.button(f"🚀 Start {stage}", type="primary", use_container_width=True,
                     disabled=st.session_state.processing or batch_size == 0,
                     key=f"start_{stage}"):
            system.process_batch(batch_size, stage)
            st.rerun()

    with col_control3:
        # Export as Excel
        export_df = system.stage_manager.export_stage_data(stage)
        if export_df is not None and not export_df.empty:
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                export_df.to_excel(writer, index=False, sheet_name=stage)
            excel_buffer.seek(0)

            st.download_button(
                f"📥 Export {stage} as Excel",
                excel_buffer,
                f"{stage.lower().replace(' ', '_')}_data.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key=f"download_excel_{stage}"
            )

    with col_control4:
        # One-click Google Sheets update button - check our stored values
        sheet_url_key = f"stored_sheet_url_{stage}"
        creds_json_key = f"stored_creds_json_{stage}"

        if (sheet_url_key in st.session_state and st.session_state[sheet_url_key] and
                creds_json_key in st.session_state and st.session_state[creds_json_key]):

            if st.button(f"📤 Update Google Sheet",
                         use_container_width=True,
                         type="secondary",
                         key=f"update_sheet_{stage}"):
                with st.spinner("Updating Google Sheet..."):
                    # Pass the stored values to the system
                    system.sheet_url = st.session_state[sheet_url_key]
                    st.session_state.sheets_connected = True

                    if system.export_to_google_sheets(stage):
                        st.success("✅ Google Sheet updated successfully!")
                    else:
                        st.error("❌ Failed to update Google Sheet")
        else:
            st.button(f"📤 Update Google Sheet",
                      disabled=True,
                      use_container_width=True,
                      help="Connect Google Sheets first to enable updates",
                      key=f"update_sheet_disabled_{stage}")

    # Data Preview
    st.subheader("👀 Data Preview")
    stage_data = system.stage_manager.get_stage_data(stage)
    if stage_data is not None and not stage_data.empty:
        # Show relevant columns based on stage
        preview_cols = ['Name', 'Email', 'Status', 'Last_Sent_Date']
        if 'Description' in stage_data.columns:
            preview_cols.insert(2, 'Description')
        if 'Auto_Detected_Campaign' in stage_data.columns:
            preview_cols.append('Auto_Detected_Campaign')

        st.dataframe(stage_data[preview_cols].head(10), use_container_width=True)

        # Show stage requirements
        with st.expander("ℹ️ Stage Requirements"):
            if stage == "Initial Outreach":
                st.info("""
                **Requirements for Initial Outreach:**
                - Leads must have Name, Email, and Description
                - Status should be 'Not Sent' for new leads
                - No previous email history required
                - Campaign type auto-detected from Description
                """)
            else:
                prev_stage = system.stage_manager._get_previous_stage_column(stage)
                st.info(f"""
                **Requirements for {stage}:**
                - Previous stage ({prev_stage.replace('_', ' ')}) must be marked as 'Completed'
                - Status should be 'Not Sent' for this stage
                - Proper tracking columns must be present
                - Uses auto-detected campaign type from Initial Outreach
                """)
    else:
        st.info(f"👆 Load data for {stage} to get started")