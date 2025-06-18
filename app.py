import os
import zipfile
import yaml
import json  # Add missing import
import shutil  # Add missing import
import streamlit as st
from typing import Dict, Any, List
from datetime import datetime
from demo_data import create_demo_pva_classic, create_demo_rasa_project

def cleanup():
    """Clean up temporary directories"""
    try:
        for directory in ["temp_rasa_project", "temp_pva_project", "uploads"]:
            if os.path.exists(directory):
                shutil.rmtree(directory)
                st.info(f"✅ Cleaned up {directory}")
    except Exception as e:
        st.error(f"Error during cleanup: {str(e)}")

def parse_rasa_zip(zip_file_path: str) -> Dict[str, Any]:
    """Parse RASA ZIP file"""
    intents_data = {}
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall("temp_rasa_project")
            st.info("✅ ZIP file extracted successfully")

        nlu_path = "temp_rasa_project/nlu.yml"
        if os.path.exists(nlu_path):
            with open(nlu_path, 'r') as file:
                nlu_yaml = yaml.safe_load(file)
                st.info("✅ NLU file loaded successfully")
                for item in nlu_yaml.get('nlu', []):
                    if 'intent' in item:
                        intent_name = item['intent']
                        examples = item.get('examples', '')
                        if isinstance(examples, str):
                            # Split examples into list and clean them
                            examples = [ex.strip('- ') for ex in examples.split('\n') if ex.strip('- ')]
                            intents_data[intent_name] = examples
        else:
            st.error("❌ NLU file not found in the ZIP")
    except Exception as e:
        st.error(f"Error parsing RASA ZIP: {str(e)}")
    return intents_data

def parse_pva_classic(zip_file_path: str) -> Dict[str, Any]:
    """Parse PVA Classic ZIP file"""
    pva_data = {}
    try:
        # Create temp directory if it doesn't exist
        os.makedirs("temp_pva_project", exist_ok=True)
        
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall("temp_pva_project")
            st.info("✅ ZIP file extracted successfully")

        topics_path = "temp_pva_project/topics.json"
        if os.path.exists(topics_path):
            try:
                with open(topics_path, 'r', encoding='utf-8') as file:
                    topics = json.load(file)
                    st.info("✅ Topics file loaded successfully")
                    if 'topics' in topics:
                        for topic in topics['topics']:
                            if isinstance(topic, dict) and 'name' in topic and 'triggers' in topic:
                                triggers = []
                                for trigger in topic['triggers']:
                                    if trigger.get('type') == 'phrase':
                                        triggers.extend(trigger.get('phrases', []))
                                if triggers:
                                    pva_data[topic['name']] = triggers
                    else:
                        st.error("❌ No topics found in the JSON file")
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON format in topics file")
        else:
            st.error("❌ Topics file not found in the ZIP")
    except Exception as e:
        st.error(f"❌ Error parsing PVA Classic ZIP: {str(e)}")
    finally:
        cleanup()
    return pva_data

def generate_copilot_yaml(intents: Dict[str, Any], bot_type: str) -> str:
    """Generate Copilot Studio compatible YAML with LLM capabilities"""
    copilot_yaml = {
        "apiVersion": "v1",
        "kind": "CopilotAgent",
        "metadata": {
            "name": f"{bot_type.lower()}_migration_{datetime.now().strftime('%Y%m%d')}",
            "description": f"AI-powered agent migrated from {bot_type}",
            "type": "copilot"
        },
        "spec": {
            "language": "en-us",
            "llm": {
                "provider": "azure-openai",
                "model": "gpt-4",
                "temperature": 0.7,
                "maxTokens": 800,
                "topP": 0.95
            },
            "conversations": [],  # Changed from nested structure to array
            "capabilities": {  # Moved capabilities to top level
                "genai": {
                    "semantic_understanding": {
                        "enabled": True,
                        "features": [
                            "contextual_intent_recognition",
                            "entity_extraction",
                            "sentiment_analysis"
                        ]
                    },
                    "memory": {
                        "enabled": True,
                        "retention": "30d",
                        "context_window": 10
                    }
                },
                "m365": {
                    "teams": {
                        "enabled": True,
                        "features": ["chat", "meetings", "channels"]
                    },
                    "outlook": {
                        "enabled": True,
                        "features": ["email", "calendar", "contacts"]
                    },
                    "sharepoint": {
                        "enabled": True,
                        "features": ["files", "sites", "lists"]
                    }
                }
            }
        }
    }

    # Add conversations with enhanced capabilities
    for intent_name, examples in intents.items():
        conversation = {
            "id": intent_name.lower().replace(" ", "_"),
            "name": intent_name,
            "triggers": {
                "utterances": examples,
                "patterns": [f"(?i).*{intent_name}.*"]
            },
            "actions": {
                "llmResponse": {
                    "enabled": True,
                    "prompt": f"""Based on the user's {intent_name} request:
                    1. Analyze the specific needs
                    2. Access relevant M365 data if needed
                    3. Provide a clear and helpful response""",
                    "settings": {
                        "temperature": 0.7,
                        "maxResponseTokens": 400
                    }
                },
                "m365": {
                    "enabled": True,
                    "services": ["teams", "outlook", "sharepoint"]
                }
            },
            "settings": {
                "authentication": {
                    "required": True,
                    "methods": ["aad"]
                },
                "context": {
                    "preserve": True,
                    "timeWindow": "30m"
                }
            }
        }
        copilot_yaml["spec"]["conversations"].append(conversation)

    return yaml.dump(copilot_yaml, allow_unicode=True, sort_keys=False)

def main():
    st.title("🔄 Classic Bot to Copilot Studio Migration Tool")
    
    # Create two columns for main layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        bot_type = st.radio(
            "Select your source bot type:",
            ["Power Virtual Agents Classic", "RASA"],
            horizontal=True
        )

        st.markdown("---")

        if bot_type == "Power Virtual Agents Classic":
            st.info("📌 Optimized for PVA Classic to Copilot Studio migration")
            st.markdown("""
            ### Instructions:
            1. Export your PVA Classic bot from Power Platform
            2. Upload the exported ZIP file
            3. The tool will convert topics to Copilot Studio format
            """)
        else:
            st.info("📌 Supporting migration from RASA to Copilot Studio")
            st.markdown("""
            ### Instructions:
            1. Upload your RASA bot's ZIP file
            2. The tool will extract intents and generate Copilot agent YAML
            3. Download the generated YAML file
            """)

        uploaded_file = st.file_uploader("📁 Upload your bot ZIP file", type=["zip"])
        
        if uploaded_file:
            try:
                os.makedirs("uploads", exist_ok=True)
                zip_path = os.path.join("uploads", uploaded_file.name)
                
                with open(zip_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                    st.info("✅ File uploaded successfully")

                if bot_type == "Power Virtual Agents Classic":
                    intents = parse_pva_classic(zip_path)
                else:
                    intents = parse_rasa_zip(zip_path)

                if intents:
                    st.success("✅ Parsed intents successfully!")
                    
                    # Show extracted intents
                    with st.expander("View Extracted Intents"):
                        st.json(intents)
                    
                    # Generate and show Copilot YAML with GenAI features
                    copilot_yaml = generate_copilot_yaml(intents, bot_type)
                    
                    # Show YAML preview with GenAI capabilities
                    with st.expander("Preview Copilot Studio YAML with GenAI & M365"):
                        st.code(copilot_yaml, language="yaml")
                        
                        # Add feature highlights
                        st.markdown("""
                        #### ✨ Enhanced Features:
                        - 🧠 **GenAI Capabilities**
                          - Semantic Understanding
                          - Conversation Memory
                          - Contextual Processing
                        - 🔄 **M365 Integrations**
                          - Teams Integration
                          - Outlook Services
                          - SharePoint Connection
                        - 📊 **Advanced Settings**
                          - Adaptive Learning
                          - Performance Monitoring
                          - User Feedback Collection
                        """)
                    
                    # Download button
                    st.download_button(
                        "⬇️ Download Enhanced Copilot Studio YAML",
                        data=copilot_yaml,
                        file_name=f"copilot_studio_enhanced_{datetime.now().strftime('%Y%m%d')}.yaml",
                        mime="text/yaml",
                        help="Download the AI-enhanced Copilot Studio configuration"
                    )
                    
                    # Success message with next steps
                    st.success("""
                    ✅ Conversion completed successfully!
                    
                    Next steps:
                    1. Download the Copilot Studio YAML file
                    2. Import it into your Copilot Studio project
                    3. Review and customize the generated conversations
                    """)
                else:
                    st.error("❌ No intents found in the uploaded file")

            except zipfile.BadZipFile:
                st.error("❌ Invalid ZIP file")
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
            finally:
                cleanup()

    # Sidebar with demo options
    with col2:
        st.markdown("### 🎮 Try Demo")
        if st.button("Download PVA Demo"):
            demo_zip = create_demo_pva_classic()
            st.download_button(
                "⬇️ Download PVA Demo",
                data=demo_zip,
                file_name=f"pva_classic_demo_{datetime.now().strftime('%Y%m%d')}.zip",
                mime="application/zip"
            )
        
        if st.button("Download RASA Demo"):
            demo_zip = create_demo_rasa_project()
            st.download_button(
                "⬇️ Download RASA Demo",
                data=demo_zip,
                file_name=f"rasa_demo_{datetime.now().strftime('%Y%m%d')}.zip",
                mime="application/zip"
            )

if __name__ == "__main__":
    main()