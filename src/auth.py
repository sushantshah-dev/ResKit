import hashlib
import json
from flask import Blueprint, Response, render_template, request, jsonify
from functools import wraps
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os, dotenv

from .models import User, UserNotFound

dotenv.load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = data['user_id']
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@auth_bp.route('/', methods=['GET'])
def index():
    return render_template('auth.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Username and password are required!'}), 400
    
    hashed_password = generate_password_hash(password, method='scrypt')
    new_user = User(username=username, email=email, hashed_password=hashed_password)
    new_user.save()
    
    token = jwt.encode({'user_id': new_user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)}, SECRET_KEY, algorithm="HS256")
    return jsonify({'message': 'User registered successfully!', 'token': token}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'message': 'Email and password are required!'}), 400
    
    user = User.get_by_email(email)
    
    if not user or not check_password_hash(user.hashed_password, password):
        return jsonify({'message': 'Invalid credentials!'}), 401
    
    token = jwt.encode({'user_id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)}, SECRET_KEY, algorithm="HS256")
    return jsonify({'token': token}), 200

@auth_bp.route('/profile', methods=['GET'])
@token_required
def profile(current_user):
    try:
        user = User.get(current_user)
        if not user:
            raise UserNotFound(current_user)
        
        return jsonify({
            'id': user.id,
            'username': user.username,
            'profile_picture': f"https://www.gravatar.com/avatar/{hashlib.sha256(user.email.lower().encode()).hexdigest()}",
            'email': user.email,
            'is_active': user.is_active,
            'is_admin': user.is_admin,
            'date_created': user.created_at.isoformat()
        }), 200
    except UserNotFound as e:
        return Response(json.dumps({"error": str(e)}), mimetype='application/json', status=404)