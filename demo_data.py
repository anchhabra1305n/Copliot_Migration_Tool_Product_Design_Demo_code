import json
import yaml
import io
import zipfile
from datetime import datetime

def create_demo_pva_classic() -> bytes:
    """Creates a demo PVA Classic project"""
    topics_json = {
        "topics": [
            {
                "id": "it_support",
                "name": "IT Support Request",
                "description": "Handle IT support requests",
                "triggers": [
                    {
                        "type": "phrase",
                        "phrases": [
                            "I need IT help",
                            "computer problem",
                            "technical support needed",
                            "laptop not working",
                            "printer issue"
                        ]
                    }
                ]
            }
        ]
    }

    memory_zip = io.BytesIO()
    with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("topics.json", json.dumps(topics_json, indent=2))
        
    memory_zip.seek(0)
    return memory_zip.getvalue()

def create_demo_rasa_project() -> bytes:
    """Creates a demo RASA project"""
    nlu_yaml = {
        "version": "3.1",
        "nlu": [
            {
                "intent": "it_support",
                "examples": """
                    - I need technical support
                    - My computer is not working
                    - Having issues with my laptop
                    - Need IT help urgently
                    - System error help
                    """
            },
            {
                "intent": "password_reset",
                "examples": """
                    - I need to reset my password
                    - Forgot my login credentials
                    - Can't access my account
                    - Password not working
                    """
            }
        ]
    }

    memory_zip = io.BytesIO()
    with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("nlu.yml", yaml.dump(nlu_yaml, allow_unicode=True))
        
    memory_zip.seek(0)
    return memory_zip.getvalue()