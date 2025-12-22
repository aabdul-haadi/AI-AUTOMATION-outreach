import json
import os
import streamlit as st
from datetime import datetime
import pandas as pd
import random
from typing import Dict, List, Optional, Any
import yaml

class DynamicTemplateManager:
    """Dynamic template management system with keyword-based matching"""
    
    def __init__(self, templates_file="email_templates.json"):
        self.templates_file = templates_file
        self.templates = self._load_templates()
        self.keyword_mapping = self._build_keyword_mapping()
        
    def _load_templates(self) -> Dict:
        """Load templates from JSON file or create default"""
        try:
            if os.path.exists(self.templates_file):
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
                    # Convert template format if needed
                    return self._convert_old_format(templates)
            else:
                return self._create_default_templates()
        except Exception as e:
            st.error(f"Error loading templates: {e}")
            return self._create_default_templates()
    
    def _convert_old_format(self, templates: Dict) -> Dict:
        """Convert old template format to new format"""
        new_templates = {}
        for template_id, template_data in templates.items():
            if isinstance(template_data, dict) and "name" in template_data:
                # Already new format
                new_templates[template_id] = template_data
            else:
                # Convert old format
                new_templates[template_id] = {
                    "name": template_id.replace("_", " ").title(),
                    "keywords": template_data.get("keywords", []),
                    "priority": template_data.get("priority", 5),
                    "followup_stages": template_data.get("followup_stages", {})
                }
        return new_templates
    
    def _create_default_templates(self) -> Dict:
        """Create comprehensive default templates from your list"""
        default_templates = {
            "no_social_presence": {
                "name": "No Social Media Presence",
                "keywords": [
                    "no social media", "not active on social", "social media inactive",
                    "need social media", "social media presence", "social media marketing",
                    "social media strategy", "social media engagement", "brand visibility online",
                    "online visibility", "digital presence"
                ],
                "priority": 10,
                "followup_stages": {
                    "Initial Outreach": {
                        "subjects": [
                            "Quick question",
                            "Social media opportunity",
                            "Online visibility for {name}"
                        ],
                        "body": """Hey {name}, do you ever feel like your brand should be showing up more online?

Many businesses with great products stay invisible simply because they're not active on social. 

I made a short breakdown showing the visibility you could gain — want it?

If yes, I'll send it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
                    },
                    "Follow-up 1": {
                        "subjects": [
                            "Following up - Social media presence",
                            "More about social visibility"
                        ],
                        "body": """Hi {name},

Following up on my previous email about social media presence.

I've worked with several businesses that were in a similar situation - great products but not enough online visibility. 

Within weeks of implementing a proper social media strategy, they started seeing significant increases in engagement and leads.

Would you like to see their results?

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
                    },
                    "Follow-up 2": {
                        "subjects": ["Circling back - Social media strategy"],
                        "body": """Hi {name},

Circling back as I know you're focused on growing your business.

The challenge of not being visible on social media is real for many businesses. People are searching for businesses like yours on platforms like Instagram, Facebook, and LinkedIn every day.

We could help you create a presence that attracts your ideal customers.

Open to a quick chat this week?

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
                    },
                    "Follow-up 3": {
                        "subjects": ["Final follow-up - Social media opportunity"],
                        "body": """Hi {name},

This will be my final follow-up about social media presence.

The opportunity to connect with your audience online remains available when you're ready. Many businesses see social media as their most valuable marketing channel once properly set up.

The door remains open if you ever want to discuss how we can help your brand show up more online.

Wishing you continued success.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
                    }
                }
            },
            
            "poor_social_visuals": {
                "name": "Poor Social Media Visuals",
                "keywords": [
                    "social media visuals", "engaging visuals", "social media design",
                    "visual content", "graphics design", "social media graphics",
                    "stop the scroll", "visual appeal", "social media posts design",
                    "creative visuals", "visual marketing"
                ],
                "priority": 9,
                "followup_stages": {
                    "Initial Outreach": {
                        "subjects": [
                            "Curious...",
                            "Social media visuals question",
                            "Visual content for {name}"
                        ],
                        "body": """Hey {name}, be honest — do your social posts actually stop the scroll?

Most brands lose attention simply because visuals aren't designed to spark emotion + action. 

I put together a quick guide showing what engaging visuals could do — want it?

If yes, I'll share it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
                    },
                    "Follow-up 1": {
                        "subjects": ["Following up - Social media visuals"],
                        "body": """Hi {name},

Following up on my previous email about social media visuals.

In today's fast-scrolling world, your visuals have less than 2 seconds to make an impression. Professional, eye-catching graphics can increase engagement by up to 300%.

We've helped businesses transform their social media presence with visuals that actually convert.

Interested in seeing some examples?

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
                    }
                }
            },
            
            "social_seo_combo": {
                "name": "Social Media + SEO Combo",
                "keywords": [
                    "social media and seo", "seo with social", "social seo",
                    "website and social media", "seo optimization with social",
                    "digital marketing package", "complete digital solution",
                    "traffic and engagement", "social content and seo"
                ],
                "priority": 8,
                "followup_stages": {
                    "Initial Outreach": {
                        "subjects": [
                            "Quick thought",
                            "Social + SEO opportunity",
                            "Visibility boost for {name}"
                        ],
                        "body": """Hey {name}, ever wonder how much traffic + engagement you're leaving on the table?

Most brands see huge jumps in visibility when social content + SEO work together, not separately. 

I made a simple breakdown showing the potential — want it?

If yes, I'll send it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
                    }
                }
            },
            
            "no_social_links": {
                "name": "No Social Media Links on Website",
                "keywords": [
                    "social media links", "social icons", "connect social media",
                    "social media integration", "website social links",
                    "social media buttons", "follow buttons", "social sharing"
                ],
                "priority": 7,
                "followup_stages": {
                    "Initial Outreach": {
                        "subjects": [
                            "Quick heads up",
                            "Website improvement for {name}",
                            "Social media connection"
                        ],
                        "body": """Hey {name}, small thing — do you know your website isn't linked to your socials?

A lot of businesses lose trust + traffic simply because customers can't follow or engage easily. 

I made a quick breakdown showing the impact — want it?

If yes, I'll share it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
                    }
                }
            },
            
            "website_redesign_needed": {
                "name": "Website Redesign + Social Integration",
                "keywords": [
                    "website redesign", "modern website", "update website",
                    "website makeover", "website revamp", "social media integration",
                    "website and social", "outdated website", "website refresh"
                ],
                "priority": 8,
                "followup_stages": {
                    "Initial Outreach": {
                        "subjects": [
                            "Honest thought",
                            "Website opportunity for {name}",
                            "Modern website design"
                        ],
                        "body": """Hey {name}, does your website feel like it reflects how strong your brand really is?

Sites without social links + modern design lose trust and conversions fast. 

I mocked up a quick vision showing how yours could look + perform — want it?

If yes, I'll send it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
                    }
                }
            },
            
            "website_inaccessible": {
                "name": "Website Inaccessible",
                "keywords": [
                    "website down", "site not loading", "website error",
                    "site broken", "website crash", "404 error",
                    "website not working", "site inaccessible", "page not found"
                ],
                "priority": 10,
                "followup_stages": {
                    "Initial Outreach": {
                        "subjects": [
                            "Quick question",
                            "Important: Website issue",
                            "Website fix for {name}"
                        ],
                        "body": """Hey {name}, did you know your site isn't loading? Thought you'd want to know.

Lots of businesses lose trust + sales when customers can't reach them. 

I drafted a simple breakdown on how to fix it fast + boost performance — want it?

If yes, I'll send it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
                    }
                }
            },
            
            "no_ads_seo": {
                "name": "No Social Media Ads & SEO",
                "keywords": [
                    "social media ads", "google ads", "paid advertising",
                    "ppc campaign", "social ads", "advertising campaign",
                    "digital ads", "online advertising", "seo and ppc",
                    "ads and seo", "paid search"
                ],
                "priority": 7,
                "followup_stages": {
                    "Initial Outreach": {
                        "subjects": [
                            "Quick question",
                            "Advertising opportunity",
                            "Traffic boost for {name}"
                        ],
                        "body": """Hey {name}, curious — are you intentionally avoiding social ads + SEO, or has it just never been the right time?

Most brands we meet are losing easy traffic + sales simply by not being visible. 

I put together a quick breakdown showing what you could be earning. Want it?

If yes, happy to share + book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
                    }
                }
            },
            
            "seo_visuals_combo": {
                "name": "SEO + Engaging Social Media Visuals",
                "keywords": [
                    "seo and social media visuals", "seo with visuals",
                    "search and social", "ranking and visuals",
                    "seo optimization with design", "content and seo",
                    "visual seo", "seo graphics"
                ],
                "priority": 8,
                "followup_stages": {
                    "Initial Outreach": {
                        "subjects": [
                            "Curious...",
                            "SEO + Visuals opportunity",
                            "Online presence boost"
                        ],
                        "body": """Hey {name}, quick question — do you ever feel like your online presence should be getting way more attention than it is?

Many brands with great products miss out simply because their SEO isn't ranking and their visuals don't stop the scroll. 

I made a quick guide on fixing both — want it?

If yes, I'll send it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
                    }
                }
            },
            
            "no_website": {
                "name": "No Website",
                "keywords": [
                    "no website", "need website", "without website",
                    "dont have website", "create website", "website development",
                    "build website", "make website", "online presence"
                ],
                "priority": 10,
                "followup_stages": {
                    "Initial Outreach": {
                        "subjects": [
                            "Quick question",
                            "Website opportunity",
                            "Online presence for {name}"
                        ],
                        "body": """Hey {name}, do you ever feel like your business should be easier to find online?

So many great brands lose trust + customers simply because they don't have a website. 

I made a quick breakdown on how much visibility and credibility you could gain — want it?

If yes, I'll send it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
                    }
                }
            },
            
            "website_needs_redesign": {
                "name": "Website Needs Redesign",
                "keywords": [
                    "website redesign", "modern website", "update website",
                    "website makeover", "website revamp", "outdated website",
                    "website improvement", "redesign site", "website upgrade"
                ],
                "priority": 9,
                "followup_stages": {
                    "Initial Outreach": {
                        "subjects": [
                            "Quick question",
                            "Website redesign opportunity",
                            "Modern website for {name}"
                        ],
                        "body": """Hey {name}, be honest — does your website actually feel like it represents how good your business really is?

Most sites lose trust + sales simply because design + flow aren't built for impact. 

I made a quick visual breakdown of what yours could look like — want it?

If yes, I'll share it + we can book a free call.

Best,
SAM - SAM Creative Solutions
www.samcreative-solutions.com"""
                    }
                }
            }
        }
        
        self._save_templates(default_templates)
        return default_templates
    
    def _build_keyword_mapping(self) -> Dict[str, str]:
        """Build reverse mapping from keywords to template IDs"""
        mapping = {}
        for template_id, template_data in self.templates.items():
            for keyword in template_data.get("keywords", []):
                mapping[keyword.lower()] = template_id
        return mapping
    
    def _save_templates(self, templates: Optional[Dict] = None) -> bool:
        """Save templates to file"""
        if templates is None:
            templates = self.templates
        try:
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(templates, f, indent=2, ensure_ascii=False)
            self.templates = templates
            self.keyword_mapping = self._build_keyword_mapping()
            return True
        except Exception as e:
            st.error(f"Error saving templates: {e}")
            return False
    
    def detect_best_template(self, description: str) -> str:
        """Find the best template based on advanced keyword matching"""
        if not description or pd.isna(description):
            return "no_website"
        
        text = str(description).lower()
        scores = {}
        
        # Advanced scoring algorithm
        for template_id, template_data in self.templates.items():
            score = 0
            priority = template_data.get("priority", 5)
            
            for keyword in template_data.get("keywords", []):
                keyword_lower = keyword.lower()
                keyword_words = keyword_lower.split()
                
                # Exact phrase match (highest score)
                if keyword_lower in text:
                    score += 15 * len(keyword_words)
                
                # All words in phrase appear (in any order)
                elif all(word in text for word in keyword_words):
                    score += 10 * len(keyword_words)
                
                # Partial match
                else:
                    matches = sum(1 for word in keyword_words if word in text)
                    if matches > 0:
                        score += 5 * matches
            
            # Bonus for exact template name match
            template_name = template_data.get("name", "").lower()
            if template_name in text:
                score += 20
            
            if score > 0:
                # Apply priority weighting
                scores[template_id] = score * (priority / 5)
        
        # Debug info
        if st.session_state.get('debug_mode', False) and scores:
            st.write("🔍 Template scores:", scores)
        
        # Return template with highest score
        if scores:
            best_template = max(scores.items(), key=lambda x: x[1])
            if best_template[1] >= 10:  # Minimum threshold
                return best_template[0]
        
        # Default fallback based on common patterns
        if "website" in text and ("down" in text or "not working" in text or "error" in text):
            return "website_inaccessible"
        elif "website" in text:
            return "no_website" if "no" in text or "don't" in text else "website_needs_redesign"
        elif "social" in text and ("visual" in text or "design" in text):
            return "poor_social_visuals"
        elif "social" in text:
            return "no_social_presence"
        elif "seo" in text:
            return "seo_visuals_combo" if "visual" in text else "social_seo_combo"
        
        return "no_website"
    
    def get_template(self, template_id: str, followup_stage: str = "Initial Outreach") -> Dict:
        """Get template for specific followup stage"""
        if template_id not in self.templates:
            # Fallback to no_website
            template_id = "no_website"
        
        template_data = self.templates[template_id]
        
        # Check if we have the specific followup stage
        if followup_stage in template_data.get("followup_stages", {}):
            stage_data = template_data["followup_stages"][followup_stage]
        else:
            # Fallback to Initial Outreach
            stage_data = template_data.get("followup_stages", {}).get("Initial Outreach", {})
            if not stage_data:
                # Ultimate fallback
                return {
                    "subject": "Business Opportunity",
                    "body": f"Hello {{name}},\n\nI wanted to connect about your business.\n\nBest regards,\nSAM Creative Solutions"
                }
        
        # Get random subject if available
        subjects = stage_data.get("subjects", ["Business Opportunity"])
        subject = random.choice(subjects) if subjects else "Business Opportunity"
        
        return {
            "subject": subject,
            "body": stage_data.get("body", ""),
            "template_name": template_data.get("name", "Unknown")
        }
    
    def get_all_template_names(self) -> List[Dict]:
        """Get all template names and IDs for dropdown"""
        return [
            {"id": template_id, "name": data.get("name", template_id)}
            for template_id, data in self.templates.items()
        ]
    
    def get_template_by_name(self, template_name: str) -> Optional[str]:
        """Get template ID by name"""
        for template_id, data in self.templates.items():
            if data.get("name") == template_name:
                return template_id
        return None
    
    def add_template(self, template_id: str, template_data: Dict) -> bool:
        """Add a new template"""
        self.templates[template_id] = template_data
        return self._save_templates()
    
    def update_template(self, template_id: str, updates: Dict) -> bool:
        """Update existing template"""
        if template_id in self.templates:
            if updates:
                self.templates[template_id].update(updates)
            return self._save_templates()
        return False
    
    def delete_template(self, template_id: str) -> bool:
        """Delete template"""
        if template_id in self.templates:
            del self.templates[template_id]
            return self._save_templates()
        return False
    
    def export_templates(self, format: str = "json") -> str:
        """Export templates to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"templates_backup_{timestamp}.{format}"
        
        if format == "json":
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=2, ensure_ascii=False)
        elif format == "yaml":
            import yaml
            with open(filename, 'w', encoding='utf-8') as f:
                yaml.dump(self.templates, f, allow_unicode=True)
        
        return filename
    
    def import_templates(self, file_path: str) -> bool:
        """Import templates from file"""
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    new_templates = json.load(f)
            elif file_path.endswith(('.yaml', '.yml')):
                import yaml
                with open(file_path, 'r', encoding='utf-8') as f:
                    new_templates = yaml.safe_load(f)
            else:
                return False
            
            # Merge with existing templates
            self.templates.update(new_templates)
            return self._save_templates()
        except Exception as e:
            st.error(f"Import error: {e}")
            return False
    
    def get_template_statistics(self) -> Dict:
        """Get statistics about templates"""
        total_templates = len(self.templates)
        total_keywords = sum(len(t.get("keywords", [])) for t in self.templates.values())
        templates_with_followups = sum(1 for t in self.templates.values() if len(t.get("followup_stages", {})) > 1)
        
        return {
            "total_templates": total_templates,
            "total_keywords": total_keywords,
            "templates_with_followups": templates_with_followups,
            "most_keywords": max((len(t.get("keywords", [])), tid) for tid, t in self.templates.items())[1],
            "highest_priority": max((t.get("priority", 5), tid) for tid, t in self.templates.items())[1]
        }