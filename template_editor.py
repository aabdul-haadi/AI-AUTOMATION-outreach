import streamlit as st
import json
import pandas as pd
import tempfile
from datetime import datetime
from templates_manager import DynamicTemplateManager


class TemplateEditor:
    """Streamlit UI for managing dynamic templates with real-time editing"""

    def __init__(self, template_manager):
        self.tm = template_manager
        self.selected_template = None

    def render_editor(self):
        """Render template editor interface"""
        st.title("📝 Dynamic Template Manager")

        # Quick stats
        stats = self.tm.get_template_statistics()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Templates", stats["total_templates"])
        with col2:
            st.metric("Total Keywords", stats["total_keywords"])
        with col3:
            st.metric("With Follow-ups", stats["templates_with_followups"])
        with col4:
            st.metric("Most Keywords", stats["most_keywords"])

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Browse & Edit",
            "➕ Add New",
            "🔍 Test Detection",
            "📊 Template Analytics",
            "📁 Import/Export"
        ])

        with tab1:
            self._render_browse_templates()

        with tab2:
            self._render_add_template()

        with tab3:
            self._render_test_detection()

        with tab4:
            self._render_template_analytics()

        with tab5:
            self._render_import_export()

    def _render_browse_templates(self):
        """Browse and edit existing templates"""
        st.subheader("📋 Existing Templates")

        # Search and filter
        col_search, col_filter = st.columns(2)
        with col_search:
            search_term = st.text_input("🔍 Search templates", placeholder="Search by name or keyword...")

        with col_filter:
            filter_option = st.selectbox("Filter by", ["All", "Has Follow-ups", "High Priority (>7)"])

        # Create template list for editing
        templates_list = []
        for template_id, data in self.tm.templates.items():
            if search_term and search_term.lower() not in data.get("name", "").lower():
                continue

            if filter_option == "Has Follow-ups" and len(data.get("followup_stages", {})) <= 1:
                continue
            elif filter_option == "High Priority (>7)" and data.get("priority", 5) <= 7:
                continue

            templates_list.append({
                "id": template_id,
                "name": data.get("name", "Unnamed"),
                "keywords": len(data.get("keywords", [])),
                "priority": data.get("priority", 5),
                "followup_stages": len(data.get("followup_stages", {})),
                "has_initial": "Initial Outreach" in data.get("followup_stages", {})
            })

        if templates_list:
            # Convert to DataFrame for display
            templates_df = pd.DataFrame(templates_list)

            # Select template for editing
            template_options = [f"{row['id']} - {row['name']}" for _, row in templates_df.iterrows()]
            selected_option = st.selectbox(
                "Select template to edit:",
                options=template_options,
                key="template_select_edit"
            )

            if selected_option:
                selected_id = selected_option.split(" - ")[0]
                self._render_template_editor(selected_id)
        else:
            st.info("No templates found. Add your first template in the 'Add New' tab.")

    def _render_template_editor(self, template_id: str):
        """Edit a specific template"""
        if template_id not in self.tm.templates:
            st.error(f"Template '{template_id}' not found!")
            return

        template_data = self.tm.templates[template_id]

        with st.form(f"edit_form_{template_id}"):
            st.markdown(f"### ✏️ Editing: **{template_data.get('name', 'Unnamed')}**")

            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input(
                    "Template Name",
                    value=template_data.get("name", ""),
                    help="Display name for the template"
                )
                new_priority = st.number_input(
                    "Priority (1-10)",
                    value=template_data.get("priority", 5),
                    min_value=1,
                    max_value=10,
                    help="Higher priority templates are chosen first"
                )

            with col2:
                current_keywords = template_data.get("keywords", [])
                keywords_text = st.text_area(
                    "Keywords (comma separated)",
                    value=", ".join(current_keywords),
                    height=100,
                    help="Keywords that trigger this template. Add as many as possible for better detection."
                )

            # Parse keywords
            keyword_list = []
            for line in keywords_text.split('\n'):
                for kw in line.split(','):
                    kw = kw.strip()
                    if kw:
                        keyword_list.append(kw)

            # Follow-up stages editor
            st.markdown("### 📧 Email Templates by Follow-up Stage")

            stages = ["Initial Outreach", "Follow-up 1", "Follow-up 2", "Follow-up 3"]
            stage_data = template_data.get("followup_stages", {})

            for stage in stages:
                with st.expander(f"**{stage}**", expanded=(stage == "Initial Outreach")):
                    stage_info = stage_data.get(stage, {})

                    # Subjects
                    current_subjects = stage_info.get("subjects", [""])
                    subjects_text = st.text_area(
                        f"Email Subjects for {stage}",
                        value="\n".join(current_subjects),
                        height=80,
                        help="One subject per line. Use {name} for personalization."
                    )

                    # Body
                    body_text = st.text_area(
                        f"Email Body for {stage}",
                        value=stage_info.get("body", ""),
                        height=250,
                        help="Email body template. Use {name} for personalization."
                    )

                    # Update stage data
                    stage_data[stage] = {
                        "subjects": [s.strip() for s in subjects_text.split('\n') if s.strip()],
                        "body": body_text
                    }

            # Action buttons
            col_save, col_delete, col_duplicate = st.columns(3)

            with col_save:
                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                    update_data = {
                        "name": new_name,
                        "keywords": keyword_list,
                        "priority": new_priority,
                        "followup_stages": stage_data
                    }

                    if self.tm.update_template(template_id, update_data):
                        st.success("✅ Template updated successfully!")
                        st.rerun()

            with col_delete:
                if st.form_submit_button("🗑️ Delete Template", type="secondary", use_container_width=True):
                    if st.session_state.get(f"confirm_delete_{template_id}", False):
                        if self.tm.delete_template(template_id):
                            st.success("✅ Template deleted!")
                            st.rerun()
                    else:
                        st.session_state[f"confirm_delete_{template_id}"] = True
                        st.warning("⚠️ Click again to confirm deletion")

            with col_duplicate:
                if st.form_submit_button("📋 Duplicate Template", type="secondary", use_container_width=True):
                    new_id = f"{template_id}_copy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    if self.tm.add_template(new_id, template_data):
                        st.success(f"✅ Template duplicated as '{new_id}'!")
                        st.rerun()

    def _render_add_template(self):
        """Add new template form"""
        st.subheader("➕ Create New Template")

        with st.form("add_template_form"):
            st.markdown("### Basic Information")

            col1, col2 = st.columns(2)
            with col1:
                template_id = st.text_input(
                    "Template ID",
                    placeholder="ecommerce_solutions",
                    help="Unique identifier (no spaces, use underscores)"
                )
                template_name = st.text_input(
                    "Template Name",
                    placeholder="E-commerce Solutions",
                    help="Display name for the template"
                )

            with col2:
                priority = st.number_input(
                    "Priority",
                    value=5,
                    min_value=1,
                    max_value=10,
                    help="Higher priority templates get chosen first when keywords match"
                )

            # Keywords
            st.markdown("### 🔑 Keywords for Detection")
            st.info("Add relevant keywords that should trigger this template. The more specific, the better!")

            keywords = st.text_area(
                "Keywords (comma separated or one per line)",
                placeholder="ecommerce, online store, shopify, woocommerce, online sales, digital store",
                height=120
            )

            # Initial outreach template
            st.markdown("### 📧 Initial Outreach Email")

            initial_subjects = st.text_area(
                "Email Subjects (one per line)",
                placeholder="Boost {name}'s Online Sales\nE-commerce Growth for {name}\nOnline Store Optimization for {name}",
                height=80,
                help="Use {name} for personalization"
            )

            initial_body = st.text_area(
                "Email Body Template",
                placeholder="""Hey {name},

I noticed you're in e-commerce and wanted to reach out...

Our solutions have helped similar stores increase their online revenue by 30-50% within months.

Would you like to see a quick case study?

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com""",
                height=250
            )

            # Quick add follow-up stages
            st.markdown("### 🔄 Quick Add Follow-up Emails")
            add_followups = st.checkbox("Add follow-up email templates now", value=False)

            if add_followups:
                followup_stages = ["Follow-up 1", "Follow-up 2", "Follow-up 3"]
                for stage in followup_stages:
                    with st.expander(f"Add {stage}", expanded=False):
                        st.text_area(
                            f"{stage} Subjects",
                            placeholder=f"Following up - Opportunity for {{name}}\n{stage} - Business growth",
                            height=60,
                            key=f"{stage}_subjects_new"
                        )
                        st.text_area(
                            f"{stage} Body",
                            placeholder=f"Hi {{name}},\n\nFollowing up on my previous email...",
                            height=150,
                            key=f"{stage}_body_new"
                        )

            if st.form_submit_button("💾 Create Template", use_container_width=True):
                if template_id and template_name:
                    # Parse keywords
                    keyword_list = []
                    for line in keywords.split('\n'):
                        for kw in line.split(','):
                            kw = kw.strip()
                            if kw:
                                keyword_list.append(kw)

                    # Build template structure
                    new_template = {
                        "name": template_name,
                        "keywords": keyword_list,
                        "priority": priority,
                        "followup_stages": {
                            "Initial Outreach": {
                                "subjects": [s.strip() for s in initial_subjects.split('\n') if s.strip()],
                                "body": initial_body
                            }
                        }
                    }

                    # Add follow-up stages if created
                    if add_followups:
                        for stage in followup_stages:
                            subjects_key = f"{stage}_subjects_new"
                            body_key = f"{stage}_body_new"

                            if subjects_key in st.session_state and body_key in st.session_state:
                                subjects_text = st.session_state[subjects_key]
                                body_text = st.session_state[body_key]

                                if subjects_text.strip() and body_text.strip():
                                    new_template["followup_stages"][stage] = {
                                        "subjects": [s.strip() for s in subjects_text.split('\n') if s.strip()],
                                        "body": body_text
                                    }

                    if self.tm.add_template(template_id, new_template):
                        st.success(f"✅ Template '{template_name}' created successfully!")
                        st.balloons()
                else:
                    st.error("❌ Please provide both Template ID and Name")

    def _render_test_detection(self):
        """Test template detection with real-time feedback"""
        st.subheader("🔍 Test Template Detection")

        col1, col2 = st.columns([2, 1])

        with col1:
            test_description = st.text_area(
                "Lead Description",
                placeholder="Paste a lead description here to test which template would be selected...\n\nExample: 'Business needs website development and social media marketing. Currently no online presence.'",
                height=200,
                key="test_description"
            )

        with col2:
            st.markdown("### Detection Settings")
            min_score_threshold = st.slider(
                "Minimum Score Threshold",
                min_value=0,
                max_value=50,
                value=10,
                help="Higher values require stronger matches"
            )

            show_all_scores = st.checkbox("Show all scores", value=True)
            auto_detect = st.checkbox("Auto-detect on type", value=True)

        if test_description or st.button("🔬 Test Detection", key="test_detection_btn"):
            if test_description:
                # Get detection results
                best_template_id = self.tm.detect_best_template(test_description)

                # Calculate all scores for display
                text = test_description.lower()
                all_scores = {}

                for template_id, template_data in self.tm.templates.items():
                    score = 0
                    for keyword in template_data.get("keywords", []):
                        keyword_lower = keyword.lower()
                        keyword_words = keyword_lower.split()

                        if keyword_lower in text:
                            score += 15 * len(keyword_words)
                        elif all(word in text for word in keyword_words):
                            score += 10 * len(keyword_words)
                        else:
                            matches = sum(1 for word in keyword_words if word in text)
                            if matches > 0:
                                score += 5 * matches

                    if score > 0:
                        priority = template_data.get("priority", 5)
                        all_scores[template_id] = score * (priority / 5)

                # Display results
                st.markdown("### 📊 Detection Results")

                col_result1, col_result2 = st.columns(2)

                with col_result1:
                    if best_template_id in self.tm.templates:
                        template_info = self.tm.templates[best_template_id]
                        st.success(f"**Selected Template:** {template_info.get('name', best_template_id)}")
                        st.metric("Detection Score", f"{all_scores.get(best_template_id, 0):.1f}")

                        # Show matched keywords
                        matched_keywords = []
                        for keyword in template_info.get("keywords", []):
                            if keyword.lower() in text:
                                matched_keywords.append(keyword)

                        if matched_keywords:
                            st.info(f"**Matched Keywords:** {', '.join(matched_keywords[:5])}")

                with col_result2:
                    # Show sample email
                    template = self.tm.get_template(best_template_id)
                    with st.expander("📧 Preview Email", expanded=True):
                        st.write("**Subject:**")
                        st.code(template["subject"].format(name="John Doe"))
                        st.write("**Body Preview:**")
                        preview = template["body"].format(name="John Doe")
                        st.text(preview[:200] + "..." if len(preview) > 200 else preview)

                # Show all scores
                if show_all_scores and all_scores:
                    st.markdown("### 📈 All Template Scores")

                    # Create sorted DataFrame
                    scores_df = pd.DataFrame([
                        {
                            "Template": self.tm.templates[tid].get("name", tid),
                            "Score": score,
                            "Priority": self.tm.templates[tid].get("priority", 5),
                            "Keywords": len(self.tm.templates[tid].get("keywords", [])),
                            "Selected": "✅" if tid == best_template_id else ""
                        }
                        for tid, score in sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
                        if score >= min_score_threshold
                    ])

                    if not scores_df.empty:
                        st.dataframe(scores_df, use_container_width=True)
                    else:
                        st.warning(f"No templates scored above {min_score_threshold}")

        # Manual template selection for testing
        st.markdown("---")
        st.subheader("🔄 Manual Template Selection Test")

        template_options = self.tm.get_all_template_names()
        selected_template_name = st.selectbox(
            "Select template manually:",
            options=[t["name"] for t in template_options],
            key="manual_template_select"
        )

        if selected_template_name:
            template_id = self.tm.get_template_by_name(selected_template_name)
            if template_id:
                template = self.tm.get_template(template_id)

                col_manual1, col_manual2 = st.columns(2)
                with col_manual1:
                    custom_name = st.text_input("Test Name", value="John Doe")
                    custom_subject = st.text_input(
                        "Custom Subject",
                        value=template["subject"].format(name=custom_name)
                    )

                with col_manual2:
                    followup_stage = st.selectbox(
                        "Follow-up Stage",
                        ["Initial Outreach", "Follow-up 1", "Follow-up 2", "Follow-up 3"],
                        key="manual_followup_stage"
                    )

                    # Get template for selected stage
                    stage_template = self.tm.get_template(template_id, followup_stage)

                # Preview
                st.markdown("### 📧 Final Email Preview")
                st.write("**Subject:**")
                st.code(stage_template["subject"].format(name=custom_name))

                st.write("**Body:**")
                email_body = stage_template["body"].format(name=custom_name)
                st.text_area(
                    "Email Content",
                    value=email_body,
                    height=300,
                    disabled=True,
                    key="manual_preview"
                )

    def _render_template_analytics(self):
        """Show template usage analytics"""
        st.subheader("📊 Template Analytics")

        # Template statistics
        stats = self.tm.get_template_statistics()

        col1, col2 = st.columns(2)

        with col1:
            # Priority distribution
            priority_counts = {}
            for template_id, data in self.tm.templates.items():
                priority = data.get("priority", 5)
                priority_counts[priority] = priority_counts.get(priority, 0) + 1

            if priority_counts:
                priority_df = pd.DataFrame(
                    list(priority_counts.items()),
                    columns=["Priority", "Count"]
                ).sort_values("Priority")

                st.bar_chart(priority_df.set_index("Priority"))
                st.caption("Template Distribution by Priority")

        with col2:
            # Keywords per template
            keyword_counts = [
                len(data.get("keywords", []))
                for data in self.tm.templates.values()
            ]

            if keyword_counts:
                keywords_df = pd.DataFrame({"Keywords": keyword_counts})
                st.metric("Avg Keywords/Template", f"{sum(keyword_counts) / len(keyword_counts):.1f}")
                st.metric("Max Keywords", max(keyword_counts))
                st.metric("Min Keywords", min(keyword_counts))

        # Template completeness analysis
        st.subheader("📋 Template Completeness")

        completeness_data = []
        for template_id, data in self.tm.templates.items():
            followup_stages = data.get("followup_stages", {})
            completeness_data.append({
                "Template": data.get("name", template_id),
                "Initial Outreach": "✅" if "Initial Outreach" in followup_stages else "❌",
                "Follow-up 1": "✅" if "Follow-up 1" in followup_stages else "❌",
                "Follow-up 2": "✅" if "Follow-up 2" in followup_stages else "❌",
                "Follow-up 3": "✅" if "Follow-up 3" in followup_stages else "❌",
                "Total Stages": len(followup_stages),
                "Keywords": len(data.get("keywords", []))
            })

        if completeness_data:
            completeness_df = pd.DataFrame(completeness_data)
            st.dataframe(completeness_df, use_container_width=True)

        # Export analytics
        st.download_button(
            "📥 Export Analytics Data",
            data=pd.DataFrame(completeness_data).to_csv(index=False),
            file_name=f"template_analytics_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    def _render_import_export(self):
        """Import/Export templates"""
        st.subheader("📁 Import/Export Templates")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Export Templates")

            export_format = st.selectbox(
                "Export Format",
                ["json", "yaml"],
                key="export_format_select"
            )

            include_all = st.checkbox("Include all templates", value=True)

            if st.button("📥 Export Templates", use_container_width=True):
                filename = self.tm.export_templates(export_format)

                with open(filename, 'rb') as f:
                    st.download_button(
                        "⬇️ Download Template File",
                        f,
                        filename,
                        f"text/{export_format}",
                        use_container_width=True
                    )

                st.success(f"✅ Templates exported to {filename}")

        with col2:
            st.markdown("### Import Templates")

            uploaded_file = st.file_uploader(
                "Upload template file",
                type=['json', 'yaml', 'yml'],
                key="template_uploader"
            )

            import_option = st.radio(
                "Import option:",
                ["Merge with existing", "Replace all templates"],
                key="import_option"
            )

            if uploaded_file and st.button("📤 Import Templates", use_container_width=True):
                with st.spinner("Importing templates..."):
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False,
                                                     suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name

                    try:
                        if import_option == "Replace all templates":
                            # Backup current templates
                            backup_file = f"templates_backup_before_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                            self.tm.export_templates()

                            # Load new templates
                            if tmp_path.endswith('.json'):
                                with open(tmp_path, 'r', encoding='utf-8') as f:
                                    new_templates = json.load(f)
                            else:
                                import yaml
                                with open(tmp_path, 'r', encoding='utf-8') as f:
                                    new_templates = yaml.safe_load(f)

                            # Replace all templates
                            self.tm.templates = new_templates
                            self.tm._save_templates()

                        else:  # Merge with existing
                            self.tm.import_templates(tmp_path)

                        st.success("✅ Templates imported successfully!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Import failed: {e}")

        # Quick template backup
        st.markdown("---")
        st.subheader("⚡ Quick Backup")

        if st.button("💾 Create Quick Backup", use_container_width=True):
            backup_file = f"templates_quick_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.tm.templates, f, indent=2)

            with open(backup_file, 'rb') as f:
                st.download_button(
                    "⬇️ Download Backup",
                    f,
                    backup_file,
                    "application/json",
                    use_container_width=True
                )