import base64
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from flask import request, Blueprint, Response
from threading import Thread
import json
from flask_socketio import emit

from .llm_interface import get_relations_from_text, get_response
from .arxiv import search_arxiv, get_arxiv_by_ids
from .auth import token_required
from .models import Project, User, Chat, Message, File, UnauthorisedMessage, UnauthorizedChatAccess, ChatNotFound, FileNotFound, UnauthorizedFileAccess, UnauthorizedProjectAccess, ProjectNotFound

api_bp = Blueprint('api', __name__)


@api_bp.route('/projects', methods=['GET'])
@token_required
def get_projects(user: Any) -> Response:
    owner_projects = Project.get_by_owner(user)
    member_projects = Project.get_by_membership(user)
    all_projects = [{"name": project.name, "id": project.id, "owner_id": project.owner_id} for project in owner_projects + member_projects]
    print(f"User {user} has projects: {json.dumps(all_projects)}")
    return Response(json.dumps(all_projects), mimetype='application/json')

@api_bp.route('/projects/<int:project_id>', methods=['GET'])
@token_required
def get_project(user: Any, project_id: int) -> Response:
    try:
        project = Project.get_by_id(project_id)
        if not project:
            raise ProjectNotFound(project_id)
        if project.owner_id != user and (not project.is_public) and (user not in (project.members or [])):
            raise UnauthorizedProjectAccess(user, project_id)
        return Response(json.dumps(project.dict()), mimetype='application/json')
    except ProjectNotFound as e:
        return Response(json.dumps({"error": str(e)}), mimetype='application/json', status=404)
    except UnauthorizedProjectAccess as e:
        return Response(json.dumps({"error": str(e)}), mimetype='application/json', status=403)

@api_bp.route('/projects', methods=['POST'])
@token_required
def create_project(user: Any) -> Response:
    try:
        data = request.get_json()
        name = data.get('name')
        if not name:
            raise ValueError("Project name is required")
        new_project = Project(name=name, owner_id=user)
        new_project.save()
        return Response(json.dumps(new_project.dict()), mimetype='application/json', status=201)
    except ValueError as e:
        return Response(json.dumps({"error": str(e)}), mimetype='application/json', status=400)

@api_bp.route('/paper-search', methods=['POST'])
@token_required
def paper_search(user: Any) -> Response:
    try: 
        query: str = request.form.get('query', '')
        category: str = request.form.get('category', 'all')
        if not query:
            raise ValueError("Query parameter is required")
        return Response(json.dumps(search_arxiv(query, category)), mimetype='application/json')
    except ValueError as e:
        return Response(json.dumps({"error": str(e)}), mimetype='application/json', status=400)

@api_bp.route('/send-message', methods=['POST'])
@token_required
def send_message(user: Any) -> Response:
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        message = data.get('message', '')
        attachments = request.json.get('attachments', [])    
        
        if not project_id or not message:
            raise ValueError("Project ID and message content are required")

        project = Project.get(project_id)
        if not project:
            raise ValueError("Project not found")
        
        try:
            chat = Chat.by_project(str(project_id))[0]
        except IndexError:
            if project.owner_id == user or user in (project.members or []):
                chat = Chat(project_id=str(project_id), members=[str(user)] + (project.members or []))
                chat.save()
        
        for attachment in attachments:
            file = File.get(attachment)
            if not file:
                raise FileNotFound(attachment)
            if file.owner_id != user:
                raise UnauthorizedFileAccess(attachment, user)

            file.members = list(set(file.members + chat.members))
            file.save()
        message = chat.add_message(user_id=str(user), content=message, attachments=attachments)
        message.save()
        
        emit('new_message', {
            'id': message.id,
            'chat_id': chat.id,
            'user_id': str(user),
            'content': [{'type': 'text', 'text': message.content}],
            'timestamp': message.timestamp.isoformat(),
            'role': 'user'
        }, room=str(project_id), namespace='/')

        Thread(target=trigger_ai_response, args=(chat[0].id,)).start()
        
        return Response(json.dumps({"message": "Message sent successfully", "chat_id": chat[0].id, "message_id": message.id}), mimetype='application/json', status=201)
    except (UnauthorisedMessage) as e:
        return Response(json.dumps({"error": str(e)}), mimetype='application/json', status=403)
    except (UnauthorizedFileAccess) as e:
        return Response(json.dumps({"error": str(e)}), mimetype='application/json', status=403)
    except (ChatNotFound) as e:
        return Response(json.dumps({"error": str(e)}), mimetype='application/json', status=404)
    except (FileNotFound) as e:
        return Response(json.dumps({"error": str(e)}), mimetype='application/json', status=404)
    except ValueError as e:
        return Response(json.dumps({"error": str(e)}), mimetype='application/json', status=400)

@api_bp.route('/read-messages/<project_id>', methods=['GET'])
@token_required
def read_messages(user: Any, project_id: str) -> Response:
    try:
        after: Optional[str] = request.args.get('after')

        project = Project.get(project_id)
        if not project:
            raise ProjectNotFound(project_id)
    
        chat = Chat.by_project(str(project_id))
        chat = chat[0] if len(chat) > 0 else None
        if not chat:
            return Response(json.dumps([]), mimetype='application/json')
        
        if user not in chat.members + [project.owner_id]:
            raise UnauthorizedChatAccess(user, chat.id)
        
        messages = Message.get_all_by_chat(chat.id)
        if after:
            messages = [msg for msg in messages if msg.timestamp > datetime.strptime(after[:-1], "%Y-%m-%dT%H:%M:%S.%f")]

        enriched_messages = []
        for message in messages:
            user_info = User.get(message.user_id)
            username = user_info.username if user_info else "Unknown"
            if message.user_id == 'card':
                message.content = json.loads(message.content)
            if message.content == "" or message.user_id == 'tool':
                continue
                
            enriched_content = [{
                "type": "text",
                "text": message.content if message.content else ""
            }] + [{
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{file.name.split('.')[-1]};base64,{base64.b64encode(file.data).decode('utf-8')}"      
                }
            } if file.name.endswith(('.png', '.jpg', '.jpeg', '.gif')) else {
                "type": "file",
                "file": {
                    "filename": file.name,
                    "file_data": f"data:application/pdf;base64,{base64.b64encode(file.data).decode('utf-8')}"
                }
            } if file.name.endswith('.pdf') else None for file in filter(None, [File.get(file_id) for file_id in message.attachments])]
            
            role = 'ai' if message.user_id in ['system', 'card'] else 'user'
            
            enriched_messages.append({
                "id": message.id,
                "chat_id": message.chat_id,
                "user_id": message.user_id,
                "username": username,
                "content": list(filter(None, enriched_content)),
                "timestamp": message.timestamp.isoformat(),
                "tool_calls": message.tool_calls,
                "role": role
            })
        
        return Response(json.dumps(enriched_messages), mimetype='application/json')
    except ProjectNotFound as e:
        return Response(json.dumps({"error": str(e)}), mimetype='application/json', status=404)
    except UnauthorizedChatAccess as e:
        return Response(json.dumps({"error": str(e)}), mimetype='application/json', status=403)

def trigger_ai_response(chat_id: str) -> Optional[Dict[str, Any]]:
    system_prompt = [{"role": "system", "content": "You are ResKit, an AI assistant that helps researchers analyse academic papers and do their own research. Provide concise, accurate, and relevant information based on the user's queries about research topics, papers, and authors. If you don't know the answer, just say you don't know. Do not make up answers."}]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_relations_from_text",
                "description": "Extract relationships from the provided text. Carefully evaluate whether a relationship is bidirectional or not.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to extract relationships from."
                        }
                    },
                    "required": ["text"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_arxiv",
                "description": "Search for academic papers on arXiv based on a query and category.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query."
                        },
                        "category": {
                            "type": "string",
                            "enum": [
                                "all", "astro-ph", "cond-mat", "gr-qc", "hep-ex", "hep-lat", "hep-ph", "hep-th",
                                "math-ph", "nlin", "nucl-ex", "nucl-th", "physics", "quant-ph", "math", "cs",
                                "q-bio", "q-fin", "stat", "eess", "econ"
                            ],
                            "description": "The category to search in (e.g., all, astro-ph, cond-mat, gr-qc, hep-ex, hep-lat, hep-ph, hep-th, math-ph, nlin, nucl-ex, nucl-th, physics, quant-ph, math, cs, q-bio, q-fin, stat, eess, econ)."
                        }
                    },
                    "required": ["query", "category"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "send_paper_card",
                "description": "Send a card to the user with details about specific papers. Use this to send details of papers the user has asked for. Follow the function call with a precurser message to the user indicating that the card has been sent. No need to mention information about the card in the main response.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "arxiv_ids": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "A list of arXiv IDs of the papers to include in the card."
                        }
                    },
                    "required": ["arxiv_ids"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_from_arxiv",
                "description": "Fetch details of specific papers from arXiv based on their arXiv IDs. The file will be provided as an attachment if available. Use this to fetch content of papers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "arxiv_ids": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "A list of arXiv IDs of the papers to fetch."
                        }
                    },
                    "required": ["arxiv_ids"]
                }
            }
        }
    ]
    
    while True:
        chat_log = Message.get_all_by_chat(chat_id)
        if not chat_log or len(chat_log) == 0:
            raise ChatNotFound(chat_id)

        annotate_message = lambda message: f"{User.get(message.user_id).username}: {message.content}" if message.user_id not in ['system', 'tool', 'card'] else message.content

        enrich_content = lambda message: [{
                "type": "text",
                "text": annotate_message(message)
            }] + [{
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{file.name.split('.')[-1]};base64,{base64.b64encode(file.data).decode('utf-8')}"      
                }
            } if file.name.endswith(('.png', '.jpg', '.jpeg', '.gif')) else {
                "type": "file",
                "file": {
                    "filename": file.name,
                    "file_data": f"data:application/pdf;base64,{base64.b64encode(file.data).decode('utf-8')}"
                }
            } for file in filter(None, [File.get(file_id) for file_id in message.attachments])]

        bot_context = system_prompt + [{
            "role": "assistant",
            "content": message.content,
            "tool_calls": json.loads(message.tool_calls) if message.tool_calls not in [None, ""] else []
        } if message.user_id == 'system' else
            json.loads(message.content)
        if message.user_id == 'tool' else {
            "role": "assistant",
            "content": message.content,
        } if message.user_id == 'card' else {
            "role": "user",
            "content": enrich_content(message)
        } for message in chat_log]
    
        response = get_response(bot_context, tools=tools)
        if response.finish_reason == "tool_calls":
            message = Message(chat_id=chat_id, user_id='system', content="", tool_calls=json.dumps([{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in response.message.tool_calls]))
            message.save()
            print(f"Saved system message with tool calls: ", message)
            for tool_call in response.message.tool_calls:
                call_id = tool_call.id
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                if tool_name == "search_arxiv":
                    tool_response = search_arxiv(tool_args.get("query", ""), tool_args.get("category", "all"))
                elif tool_name == "read_from_arxiv":
                    docs = get_arxiv_by_ids(tool_args.get("arxiv_ids", []))
                    urls = [doc.get("pdf_link", "") for doc in docs if doc.get("pdf_link", "")]
                    tool_response = [{"type": "file", "file": {"filename": url.split("/")[-1], "file_data": url}} for url in urls]
                elif tool_name == "send_paper_card":
                    cards = get_arxiv_by_ids(tool_args.get("arxiv_ids", []))
                    for card in cards:
                        card_message = Message(chat_id=chat_id, user_id='card', content=json.dumps(card))
                        card_message.save()
                        emit('new_card', {'cards': card}, room=str(chat_id), namespace='/')
                    tool_response = "Sent paper card for arXiv IDs " + ",".join(tool_args.get("arxiv_ids", []))
                elif tool_name == "get_relations_from_text":
                    tool_response = get_relations_from_text(tool_args.get("text", ""))
                else:
                    tool_response = f"Error: Unknown tool {tool_name}"
                tool_response_content = {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": json.dumps(tool_response)
                }
                bot_context.append(tool_response_content)
                message = Message(chat_id=chat_id, user_id='tool', content=json.dumps(tool_response_content))
                message.save()
        else:
            message = Message(chat_id=chat_id, user_id='system', content=response.message.content)
            message.save()
            emit('new_message', {
                'id': message.id,
                'chat_id': chat_id,
                'user_id': 'system',
                'role': 'assistant',
                'content': [{'type': 'text', 'text': response.message.content}],
                'timestamp': datetime.now().isoformat()
            }, room=str(chat_id), namespace='/')
            break

@api_bp.route('/upload', methods=['POST'])
@token_required
def upload_file(user: Any) -> Tuple[Dict[str, Any], int]:
    try:
        if 'file' not in request.files:
            raise ValueError("No file part in the request")
        file_data = request.files['file']
        if file_data.filename == '':
            raise ValueError("No selected file")

        file = File(name=file_data.filename, owner_id=user)
        file.data = file_data.read()
        file.save()
        return {"message": f"File uploaded successfully", "filename": file.name}, 200
    except ValueError as e:
        return {"error": str(e)}, 400