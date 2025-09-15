from openai import OpenAI
import os, dotenv, json
import base64

dotenv.load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

def get_response(messages, tools=None, attachments=None, model="google/gemini-2.5-pro"):
    attachments = attachments or []
    
    for attachment in attachments:
        print("Attachment")
        if attachment.split(".")[1] in ["pdf"]:
            with open(attachment, "rb") as f:
                encoded = f"data:application/pdf;base64,{base64.b64encode(f.read()).decode('utf-8')}"
                messages[-1]["content"].append({
                    "type": "file",
                    "file": {
                        "filename": attachment.split("/")[-1],
                        "file_data": encoded
                    }
                })
        elif attachment.split(".")[1] in ["png", "jpg", "jpeg", "gif"]:
            with open(attachment, "rb") as f:
                encoded = f"data:image/{attachment.split('.')[-1]};base64,{base64.b64encode(f.read()).decode('utf-8')}"
                messages[-1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": encoded              
                    }
                })

    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "RESKIT", # Optional. Your site name for rankings on openrouter.ai.
            "X-Title": "ResKit", # Optional. Site title for rankings on openrouter.ai.
        },
        extra_body={},
        model=model,
        messages=messages,
        tools=tools,
        max_tokens=5000
    )
    return completion.choices[0]

def get_relations_from_text(text, model="google/gemma-3-27b-it"):
    messages = [
        {"role": "system", "content": "You are ResKit relationship extractor. Extract relationships from the provided text. Carefully evaluate whether a relationship is bidirectional or not. Evaluate pronouns, noun clauses, gerunds and other linguistic constructs to identify entities. Classify entities into types: Person, Organization, Location, Event, Date, Concept, Object, Other."},
        {"role": "user", "content": f"Extract all relationships from the following text:\n\n{text}"}
    ]
    
    response = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "RESKIT", # Optional. Your site name for rankings on openrouter.ai.
            "X-Title": "ResKit", # Optional. Site title for rankings on openrouter.ai.
        },
        extra_body={},
        model=model,
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                    "name": "relationship_extraction",
                    "strict": True,
                    "description": "Extract relationships from the provided text. Carefully evaluate whether a relationship is bidirectional or not.",
                    "schema": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "subject": {"type": "string"},
                                "subject_type": {"type": "string", "enum": ["Person", "Organization", "Location", "Event", "Date", "Concept", "Object", "Other"]},
                                "relation": {"type": "string"},
                                "bidirectional": {"type": "boolean"},
                                "object": {"type": "string"},
                                "object_type": {"type": "string", "enum": ["Person", "Organization", "Location", "Event", "Date", "Concept", "Object", "Other"]},
                            },
                            "required": ["subject", "relation", "object", "bidirectional", "subject_type", "object_type"]
                        }
                    },
            }
        },
        max_completion_tokens=5000)
    
    return response.choices[0].message.content