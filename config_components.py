import streamlit as st
import pandas as pd
import numpy as np
import smtplib
import time
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
import os
import warnings
import gspread
from google.oauth2.service_account import Credentials
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')


# Configuration with admin settings
class Config:
    # Campaign types mapping (kept for compatibility)
    CAMPAIGN_TYPES = {
        "auto_detect": "🤖 Auto-detect Campaign (Recommended)",
        "no_website": "🌐 Leads with No Website",
        "no_social_presence": "📱 No Social Media Presence",
        "poor_social_visuals": "🎨 No Engaging Social Media Visuals",
        "social_seo_combo": "🚀 Social Media + SEO Combo",
        "no_social_links": "🔗 No Social Media Links on Website",
        "website_redesign_needed": "🔄 Website Redesign + Social Integration",
        "website_inaccessible": "❌ Website Inaccessible",
        "no_ads_seo": "📊 No Social Media Ads & SEO",
        "seo_visuals_combo": "🎯 SEO + Engaging Social Media Visuals",
        "website_needs_redesign": "✨ Website Needs Redesign"
    }

    # Keep old templates for backward compatibility
    EMAIL_TEMPLATES = {
        "no_social_presence": {
            "subject": "Quick question",
            "body": """Hey {name}, do you ever feel like your brand should be showing up more online?

Many businesses with great products stay invisible simply because they're not active on social. 

I made a short breakdown showing the visibility you could gain — want it?

If yes, I'll send it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
        },
        "poor_social_visuals": {
            "subject": "Curious...",
            "body": """Hey {name}, be honest — do your social posts actually stop the scroll?

Most brands lose attention simply because visuals aren't designed to spark emotion + action. 

I put together a quick guide showing what engaging visuals could do — want it?

If yes, I'll share it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
        },
        "social_seo_combo": {
            "subject": "Quick thought",
            "body": """Hey {name}, ever wonder how much traffic + engagement you're leaving on the table?

Most brands see huge jumps in visibility when social content + SEO work together, not separately. 

I made a simple breakdown showing the potential — want it?

If yes, I'll send it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
        },
        "no_social_links": {
            "subject": "Quick heads up",
            "body": """Hey {name}, small thing — do you know your website isn't linked to your socials?

A lot of businesses lose trust + traffic simply because customers can't follow or engage easily. 

I made a quick breakdown showing the impact — want it?

If yes, I'll share it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
        },
        "website_redesign_needed": {
            "subject": "Honest thought",
            "body": """Hey {name}, does your website feel like it reflects how strong your brand really is?

Sites without social links + modern design lose trust and conversions fast. 

I mocked up a quick vision showing how yours could look + perform — want it?

If yes, I'll send it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
        },
        "website_inaccessible": {
            "subject": "Quick question",
            "body": """Hey {name}, did you know your site isn't loading? Thought you'd want to know.

Lots of businesses lose trust + sales when customers can't reach them. 

I drafted a simple breakdown on how to fix it fast + boost performance — want it?

If yes, I'll send it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
        },
        "no_ads_seo": {
            "subject": "Quick question",
            "body": """Hey {name}, curious — are you intentionally avoiding social ads + SEO, or has it just never been the right time?

Most brands we meet are losing easy traffic + sales simply by not being visible. 

I put together a quick breakdown showing what you could be earning. Want it?

If yes, happy to share + book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
        },
        "seo_visuals_combo": {
            "subject": "Curious...",
            "body": """Hey {name}, quick question — do you ever feel like your online presence should be getting way more attention than it is?

Many brands with great products miss out simply because their SEO isn't ranking and their visuals don't stop the scroll. 

I made a quick guide on fixing both — want it?

If yes, I'll send it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
        },
        "no_website": {
            "subject": "Quick question",
            "body": """Hey {name}, do you ever feel like your business should be easier to find online?

So many great brands lose trust + customers simply because they don't have a website. 

I made a quick breakdown on how much visibility and credibility you could gain — want it?

If yes, I'll send it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
        },
        "website_needs_redesign": {
            "subject": "Quick question",
            "body": """Hey {name}, be honest — does your website actually feel like it represents how good your business really is?

Most sites lose trust + sales simply because design + flow aren't built for impact. 

I made a quick visual breakdown of what yours could look like — want it?

If yes, I'll share it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
        }
    }

    # Default settings - can be modified by admin
    DEFAULT_BATCH_SIZE = 20
    MAX_BATCH_SIZE = 500
    SMTP_TIMEOUT = 15
    RATE_LIMIT_DELAY = 1.5
    MAX_RETRIES = 3
    THREAD_POOL_SIZE = 5

    # Login credentials (can be changed in admin panel)
    DEFAULT_USERNAME = "admin"
    DEFAULT_PASSWORD = "admin123"

    # Email provider configurations
    EMAIL_PROVIDERS = {
        "Gmail": {
            "server": "smtp.gmail.com",
            "port": 587,
            "requires_app_password": True
        },
        "Outlook/Hotmail": {
            "server": "smtp-mail.outlook.com",
            "port": 587,
            "requires_app_password": False
        },
        "Yahoo": {
            "server": "smtp.mail.yahoo.com",
            "port": 587,
            "requires_app_password": False
        },
        "Office 365": {
            "server": "smtp.office365.com",
            "port": 587,
            "requires_app_password": False
        },
        "Custom SMTP": {
            "server": "",
            "port": 587,
            "requires_app_password": False
        }
    }


class LocalNLPProcessor:
    """Local NLP processing for intent detection (now using DynamicTemplateManager)"""

    # These are kept for backward compatibility but the main detection is now in templates_manager.py
    PAIN_PATTERNS = {
        "no_website": {
            "keywords": ["no website", "need website", "without website", "dont have website", "create website",
                         "website development", "build website"],
            "weight": 3.0
        },
        "poor_social_visuals": {
            "keywords": ["engaging social media visuals", "social media visuals", "social media design",
                         "social media graphics", "visual content", "graphics design", "social media posts design"],
            "weight": 2.5
        },
        "social_seo_combo": {
            "keywords": ["website and seo", "website and social media", "seo and social media",
                         "digital marketing package", "complete digital solution"],
            "weight": 2.0
        },
        "no_social_presence": {
            "keywords": ["social media presence", "social media management", "social media marketing",
                         "social media strategy", "social media engagement"],
            "weight": 2.0
        },
        "no_social_links": {
            "keywords": ["social media links", "social icons", "connect social media", "social media integration"],
            "weight": 1.5
        },
        "website_inaccessible": {
            "keywords": ["website down", "site not loading", "website error", "site broken", "website crash"],
            "weight": 3.0
        },
        "website_needs_redesign": {
            "keywords": ["website redesign", "modern website", "update website", "website makeover", "website revamp"],
            "weight": 2.0
        },
        "website_redesign_needed": {
            "keywords": ["website and social media integration", "complete website solution", "website overhaul"],
            "weight": 1.5
        },
        "no_ads_seo": {
            "keywords": ["seo and ppc", "social media ads", "google ads", "paid advertising", "advertising campaign",
                         "ppc campaign", "social ads"],
            "weight": 2.5
        },
        "seo_visuals_combo": {
            "keywords": ["seo and engaging social media visuals", "seo with social media visuals",
                         "search and social media"],
            "weight": 2.0
        }
    }

    # Industry detection map
    INDUSTRY_MAP = {
        "travel_agency": ["travel agency", "tour operator", "travel company", "tourist service", "vacation planning",
                          "travel planning", "tourism"],
        "restaurant": ["restaurant", "cafe", "food", "dining", "bistro", "coffee shop", "eatery", "food truck"],
        "real_estate": ["real estate", "property", "realtor", "housing", "apartment", "realty", "property management"],
        "clinic": ["clinic", "doctor", "dental", "health", "medical", "hospital", "healthcare", "pharmacy"],
        "ecommerce": ["shop", "store", "ecommerce", "online store", "retail", "merchant", "boutique"],
        "agency": ["agency", "marketing", "branding", "advertising", "consulting", "consultant", "services"],
        "education": ["school", "education", "training", "course", "learning", "academy", "tutoring"],
        "fitness": ["gym", "fitness", "yoga", "wellness", "training", "exercise", "personal trainer"],
        "beauty": ["salon", "spa", "beauty", "hair", "nails", "cosmetics", "esthetician", "makeup"],
        "auto": ["auto care", "car service", "automotive", "mechanic", "car repair", "auto maintenance"],
        "legal": ["legal", "law firm", "attorney", "lawyer", "legal service", "legal consultation"],
        "retail": ["store", "retail", "shop", "merchant", "boutique", "outlet", "showroom"]
    }

    @classmethod
    def detect_campaign_type(cls, description: str):
        """Enhanced campaign detection with weighted keyword scoring - For backward compatibility"""
        # This method is now a wrapper that uses the DynamicTemplateManager
        try:
            # Try to import the template manager
            from templates_manager import DynamicTemplateManager

            # Create or get template manager instance
            if 'template_manager' in st.session_state:
                tm = st.session_state.template_manager
            else:
                tm = DynamicTemplateManager()
                st.session_state.template_manager = tm

            # Use the template manager's detection
            return tm.detect_best_template(description)

        except ImportError:
            # Fallback to old detection if template_manager not available
            if not description or pd.isna(description):
                return "no_website"

            text = str(description).lower()
            scores = {}

            # Calculate weighted scores for each campaign type
            for campaign_type, pattern_data in cls.PAIN_PATTERNS.items():
                keywords = pattern_data["keywords"]
                weight = pattern_data.get("weight", 1.0)
                score = 0

                for keyword in keywords:
                    # Check for exact phrase match (higher score)
                    if keyword in text:
                        # Longer keyword matches get higher scores
                        keyword_length = len(keyword.split())
                        score += weight * (keyword_length * 2)

                    # Check for individual word matches (lower score)
                    elif all(word in text for word in keyword.split()):
                        score += weight * len(keyword.split())

                # Additional scoring based on word presence
                for keyword in keywords:
                    for word in keyword.split():
                        if word in text:
                            score += 0.1 * weight

                if score > 0:
                    scores[campaign_type] = score

            # Return the campaign with highest score, or default to no_website
            if scores:
                best_campaign = max(scores.items(), key=lambda x: x[1])
                if best_campaign[1] >= 1.0:  # Minimum threshold
                    return best_campaign[0]

            # Default based on common patterns
            if "website" in text and ("seo" in text or "social" in text):
                return "social_seo_combo"
            elif "website" in text:
                return "no_website"
            elif "seo" in text and "social" in text:
                return "seo_visuals_combo"
            elif "seo" in text and "ppc" in text:
                return "no_ads_seo"
            elif "social" in text and "visual" in text:
                return "poor_social_visuals"

            return "no_website"

    @staticmethod
    def extract_profile(description: str):
        """Extract intent profile from description - For backward compatibility"""
        if not description or pd.isna(description):
            return {
                "industry": "Business",
                "pain": "General",
                "service": "digital marketing",
                "goal": "grow your business online",
                "campaign_type": "no_website"
            }

        text = str(description).lower()

        # Detect campaign type
        campaign_type = LocalNLPProcessor.detect_campaign_type(description)

        # Detect industry
        industry = "business"
        industry_score = 0
        for k, words in LocalNLPProcessor.INDUSTRY_MAP.items():
            score = sum(1 for w in words if w in text)
            if score > industry_score:
                industry = k
                industry_score = score

        return {
            "industry": industry.replace("_", " ").title(),
            "pain": campaign_type.replace("_", " ").title(),
            "service": "digital marketing",
            "goal": "grow your business online",
            "campaign_type": campaign_type
        }

    @staticmethod
    def generate_personalized_email(name: str, description: str, campaign_type: str,
                                    followup_stage: str = "Initial Outreach"):
        """Generate personalized email using templates - For backward compatibility"""
        try:
            # Try to use the template manager
            from templates_manager import DynamicTemplateManager

            if 'template_manager' in st.session_state:
                tm = st.session_state.template_manager
            else:
                tm = DynamicTemplateManager()
                st.session_state.template_manager = tm

            # Get template from template manager
            template = tm.get_template(campaign_type, followup_stage)
            if template and template.get('body'):
                return template["body"].format(name=name)

        except (ImportError, KeyError):
            pass

        # Fallback to old template system
        if followup_stage == "Initial Outreach":
            if campaign_type in Config.EMAIL_TEMPLATES:
                return Config.EMAIL_TEMPLATES[campaign_type]["body"].format(name=name)

        # Fallback templates for follow-ups
        profile = LocalNLPProcessor.extract_profile(description)

        templates = {
            "Follow-up 1": f"""Hi {name},

Following up on my previous email about helping your {profile['industry']} business with digital marketing.

Many businesses face the same challenge of {profile['pain'].lower()}, but there are proven solutions.

We've prepared a short case study showing how we helped a {profile['industry']} business overcome this.

Would you be interested in seeing it?

Best regards,
SAM - SAM Creative Solutions
www.samcreative-solutions.com""",

            "Follow-up 2": f"""Hi {name},

Circling back as I know you're focused on growing your business.

Specifically for {profile['industry']}, addressing {profile['pain'].lower()} can lead to significant improvements.

We recently helped a similar client increase their results by 3x in just 90 days.

Open to a quick 10-minute chat this week?

Best regards,
SAM - SAM Creative Solutions
www.samcreative-solutions.com""",

            "Follow-up 3": f"""Hi {name},

This will be my final follow-up. I don't want to take more of your time managing {profile['industry']}.

The challenge of {profile['pain'].lower()} is real for many businesses, and the solution exists when you're ready.

The door remains open if you ever want to discuss how we can help your business grow online.

Wishing you continued success.

Best regards,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
        }

        return templates.get(followup_stage,
                             Config.EMAIL_TEMPLATES.get(campaign_type, {}).get("body", "").format(name=name))

    @classmethod
    def auto_detect_leads(cls, df):
        """Auto-detect campaign types for all leads in dataframe - For backward compatibility"""
        if df is None or df.empty:
            return df

        df = df.copy()

        if 'Description' not in df.columns:
            df['Description'] = 'Business needs digital marketing services'

        # Detect campaign for each lead
        campaign_types = []

        for idx, row in df.iterrows():
            description = row['Description'] if pd.notna(row['Description']) else ''
            campaign_type = cls.detect_campaign_type(description)
            campaign_types.append(campaign_type)

        df['Auto_Detected_Campaign'] = campaign_types

        # Add campaign names for display
        df['Campaign_Name'] = df['Auto_Detected_Campaign'].apply(
            lambda x: Config.CAMPAIGN_TYPES.get(x, x.replace('_', ' ').title())
        )

        return df


class HighPerformanceEmailSender:
    """High-performance email sender with connection management and threading"""

    def __init__(self):
        self.smtp_config = None
        self._connection_pool = []
        self._max_connections = 3
        self._lock = threading.Lock()

    def configure(self, email, password, server="smtp.gmail.com", port=587):
        """Configure SMTP settings"""
        self.smtp_config = {
            'email': email,
            'password': password,
            'server': server,
            'port': port
        }

    def _create_connection(self):
        """Create new SMTP connection"""
        try:
            connection = smtplib.SMTP(
                self.smtp_config['server'],
                self.smtp_config['port'],
                timeout=Config.SMTP_TIMEOUT
            )
            connection.starttls()
            connection.login(self.smtp_config['email'], self.smtp_config['password'])
            return connection
        except Exception as e:
            st.error(f"Failed to create SMTP connection: {e}")
            return None

    def _get_connection(self):
        """Get connection from pool or create new one"""
        with self._lock:
            if self._connection_pool:
                connection = self._connection_pool.pop()
                try:
                    connection.noop()  # Test connection
                    return connection
                except:
                    pass  # Connection is dead, create new one

            return self._create_connection()

    def _return_connection(self, connection):
        """Return connection to pool"""
        with self._lock:
            if connection and len(self._connection_pool) < self._max_connections:
                try:
                    connection.noop()  # Test connection
                    self._connection_pool.append(connection)
                    return
                except:
                    pass  # Connection is dead, don't return to pool

            # Close dead connection
            if connection:
                try:
                    connection.quit()
                except:
                    pass

    def test_connection(self):
        """Test SMTP connection"""
        try:
            conn = self._create_connection()
            if conn:
                conn.quit()
                return True
            return False
        except:
            return False

    def send_single_email(self, recipient_email, subject, body):
        """Send single email with retry logic and better error handling"""
        if not self.smtp_config:
            raise ValueError("SMTP not configured")

        for attempt in range(Config.MAX_RETRIES):
            connection = None
            try:
                connection = self._get_connection()
                if not connection:
                    if attempt == Config.MAX_RETRIES - 1:
                        return False
                    time.sleep(1)
                    continue

                msg = MIMEText(body, 'plain')
                msg['From'] = self.smtp_config['email']
                msg['To'] = recipient_email
                msg['Subject'] = subject
                msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')

                connection.sendmail(self.smtp_config['email'], recipient_email, msg.as_string())
                return True

            except smtplib.SMTPServerDisconnected:
                # Server disconnected, don't return connection to pool
                if connection:
                    try:
                        connection.quit()
                    except:
                        pass
                connection = None

                if attempt == Config.MAX_RETRIES - 1:
                    return False
                time.sleep(1)

            except Exception as e:
                if attempt == Config.MAX_RETRIES - 1:
                    return False
                time.sleep(1)

            finally:
                if connection:
                    self._return_connection(connection)

        return False

    def send_batch_emails(self, email_tasks):
        """Send batch emails using thread pool for maximum performance"""
        if not self.smtp_config:
            raise ValueError("SMTP not configured")

        results = []

        def send_task(task):
            idx, recipient_email, subject, body, lead_name = task
            success = self.send_single_email(recipient_email, subject, body)
            time.sleep(Config.RATE_LIMIT_DELAY)  # Rate limiting between emails
            return idx, success

        # Use thread pool for parallel sending
        with ThreadPoolExecutor(max_workers=Config.THREAD_POOL_SIZE) as executor:
            future_to_task = {executor.submit(send_task, task): task for task in email_tasks}

            for future in as_completed(future_to_task):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    st.error(f"Email task failed: {e}")
                    results.append((future_to_task[future][0], False))

        return results

    def close(self):
        """Close all connections"""
        with self._lock:
            for connection in self._connection_pool:
                try:
                    connection.quit()
                except:
                    pass
            self._connection_pool.clear()


class GoogleSheetsManager:
    """Enhanced Google Sheets integration"""

    def __init__(self):
        self.client = None
        self.connected = False

    def connect(self, credentials_json):
        """Connect to Google Sheets"""
        try:
            if isinstance(credentials_json, str):
                credentials_json = json.loads(credentials_json)

            scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
            creds = Credentials.from_service_account_info(credentials_json, scopes=scopes)
            self.client = gspread.authorize(creds)
            self.connected = True
            return True
        except Exception as e:
            st.error(f"Google Sheets connection failed: {e}")
            return False

    def get_sheet_data(self, sheet_url, worksheet_name=0):
        """Get data from Google Sheet"""
        try:
            spreadsheet = self.client.open_by_url(sheet_url)
            worksheet = spreadsheet.worksheet(worksheet_name)
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error reading sheet: {e}")
            return None

    def update_sheet_with_status(self, sheet_url, worksheet_name, df):
        """Update Google Sheet with color-coded status"""
        try:
            spreadsheet = self.client.open_by_url(sheet_url)
            worksheet = spreadsheet.worksheet(worksheet_name)

            worksheet.clear()
            headers = df.columns.tolist()
            worksheet.update([headers] + df.values.tolist())

            return True
        except Exception as e:
            st.error(f"Error updating sheet: {e}")
            return False


class EmailHistory:
    """Enhanced email history with export and template tracking"""

    def __init__(self):
        if 'email_history' not in st.session_state:
            st.session_state.email_history = []

    def add_email(self, name, email, subject, body, status, followup_stage, template_id=None):
        """Add email to history with template info"""
        # Get template name if available
        template_name = "Unknown"
        if template_id:
            try:
                from templates_manager import DynamicTemplateManager
                if 'template_manager' in st.session_state:
                    tm = st.session_state.template_manager
                    template_name = tm.templates.get(template_id, {}).get('name', template_id)
            except:
                template_name = template_id

        st.session_state.email_history.insert(0, {
            'timestamp': datetime.now(),
            'name': name,
            'email': email,
            'subject': subject,
            'body': body,
            'status': status,
            'followup_stage': followup_stage,
            'template_id': template_id,
            'template_name': template_name
        })

        # Keep only last 200 emails
        if len(st.session_state.email_history) > 200:
            st.session_state.email_history = st.session_state.email_history[:200]

    def show_history(self):
        """Show email history"""
        if not st.session_state.email_history:
            st.info("📭 No emails sent yet")
            return

        st.subheader("📨 Email History")

        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input("🔍 Search emails", placeholder="Search by name, email, or template...")
        with col2:
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.email_history = []
                st.rerun()

        # Filter emails
        filtered_emails = st.session_state.email_history
        if search_term:
            search_lower = search_term.lower()
            filtered_emails = [
                email for email in st.session_state.email_history
                if (search_lower in email['name'].lower() or
                    search_lower in email['email'].lower() or
                    search_lower in email['subject'].lower() or
                    search_lower in str(email.get('template_name', '')).lower())
            ]

        # Show filtered emails
        recent_emails = filtered_emails[:50]  # Limit to 50 for performance

        for i, email in enumerate(recent_emails):
            expander_key = f"history_expander_{i}_{hash(email['email'])}"
            with st.expander(
                    f"📧 {email['timestamp'].strftime('%m/%d %H:%M')} - {email['name']} ({email['followup_stage']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**To:** {email['email']}")
                    st.write(f"**Subject:** {email['subject']}")
                    if email.get('template_name'):
                        st.write(f"**Template:** {email['template_name']}")
                with col2:
                    status_color = "🟢" if email['status'] == "Sent" else "🔴"
                    st.write(f"**Status:** {status_color} {email['status']}")
                    st.write(f"**Stage:** {email['followup_stage']}")
                    st.write(f"**Time:** {email['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")

                text_area_key = f"email_body_{i}_{hash(email['email'])}"
                st.text_area("Email Content", email['body'], height=120, key=text_area_key, disabled=True)

    def export_to_dataframe(self):
        """Export history to DataFrame for Excel export"""
        if not st.session_state.email_history:
            return None

        history_data = []
        for email in st.session_state.email_history:
            history_data.append({
                'Timestamp': email['timestamp'],
                'Name': email['name'],
                'Email': email['email'],
                'Subject': email['subject'],
                'Status': email['status'],
                'Followup_Stage': email['followup_stage'],
                'Template': email.get('template_name', 'Unknown'),
                'Template_ID': email.get('template_id', ''),
                'Email_Body': email['body']
            })

        return pd.DataFrame(history_data)

    def get_template_usage_stats(self):
        """Get statistics on template usage"""
        if not st.session_state.email_history:
            return {}

        template_stats = {}
        for email in st.session_state.email_history:
            template_id = email.get('template_id')
            if template_id:
                if template_id not in template_stats:
                    template_stats[template_id] = {
                        'name': email.get('template_name', template_id),
                        'total': 0,
                        'successful': 0,
                        'failed': 0
                    }

                template_stats[template_id]['total'] += 1
                if email['status'] == 'Sent':
                    template_stats[template_id]['successful'] += 1
                else:
                    template_stats[template_id]['failed'] += 1

        return template_stats


class TemplateUtils:
    """Utility functions for template management"""

    @staticmethod
    def get_template_preview(template_id, followup_stage="Initial Outreach", name="John Doe"):
        """Get a preview of a template"""
        try:
            from templates_manager import DynamicTemplateManager

            if 'template_manager' in st.session_state:
                tm = st.session_state.template_manager
            else:
                tm = DynamicTemplateManager()
                st.session_state.template_manager = tm

            template = tm.get_template(template_id, followup_stage)
            if template:
                return {
                    'subject': template['subject'].format(name=name),
                    'body': template['body'].format(name=name)
                }
        except:
            pass

        return None

    @staticmethod
    def get_all_template_options():
        """Get all templates for dropdown selection"""
        try:
            from templates_manager import DynamicTemplateManager

            if 'template_manager' in st.session_state:
                tm = st.session_state.template_manager
            else:
                tm = DynamicTemplateManager()
                st.session_state.template_manager = tm

            template_options = []
            for template_id, template_data in tm.templates.items():
                template_name = template_data.get('name', template_id)
                template_options.append({
                    'id': template_id,
                    'name': template_name,
                    'keywords': len(template_data.get('keywords', [])),
                    'priority': template_data.get('priority', 5)
                })

            # Sort by priority then name
            template_options.sort(key=lambda x: (-x['priority'], x['name']))
            return template_options
        except:
            return []

    @staticmethod
    def detect_template_for_description(description):
        """Detect which template would be used for a description"""
        try:
            from templates_manager import DynamicTemplateManager

            if 'template_manager' in st.session_state:
                tm = st.session_state.template_manager
            else:
                tm = DynamicTemplateManager()
                st.session_state.template_manager = tm

            return tm.detect_best_template(description)
        except:
            # Fallback to old NLP processor
            return LocalNLPProcessor.detect_campaign_type(description)


# Export all classes
__all__ = [
    'Config',
    'LocalNLPProcessor',
    'HighPerformanceEmailSender',
    'GoogleSheetsManager',
    'EmailHistory',
    'TemplateUtils'
]