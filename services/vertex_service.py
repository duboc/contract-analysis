from vertexai.generative_models import GenerativeModel, GenerationConfig, SafetySetting, HarmCategory, HarmBlockThreshold
import json
import logging

class VertexService:
    def __init__(self):
        self.generation_config = {
            'temperature': 0.3,
            'top_p': 0.95,
            'top_k': 40,
            'max_output_tokens': 8000,
            'candidate_count': 1,
            'response_mime_type': 'application/json'
        }
        
        self.safety_settings = [
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=HarmBlockThreshold.BLOCK_NONE
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=HarmBlockThreshold.BLOCK_NONE
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=HarmBlockThreshold.BLOCK_NONE
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=HarmBlockThreshold.BLOCK_NONE
            )
        ]
        
        self.logger = logging.getLogger(__name__)

    def analyze_document(self, text: str, schema: dict) -> tuple[bool, dict, str]:
        try:
            model = GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config=GenerationConfig(**self.generation_config),
                safety_settings=self.safety_settings
            )

            response = model.generate_content(
                text,
                generation_config=GenerationConfig(
                    **self.generation_config,
                    response_schema=schema
                )
            )

            try:
                result = json.loads(response.text)
                return True, result, None
            except json.JSONDecodeError:
                return False, None, response.text
                
        except Exception as e:
            error_msg = f"Error generating content: {str(e)}"
            self.logger.error(error_msg)
            return False, None, error_msg

def transform_analysis_result(result: dict) -> dict:
    """Transform the analysis result into the expected format"""
    transformed = {
        "high": [],
        "medium": []
    }
    
    for item in result.get("list_of_statements", []):
        transformed_item = {
            "text": item["verbatim_text"],
            "suggestion": item["lower_risk_text_suggestion"],
            "analysis": item["risk_reason"],
            "page": item["page_location"],
            "source": "main"
        }
        transformed[item["risk_level"]].append(transformed_item)
    
    return transformed
