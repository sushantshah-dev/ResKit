from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from .api import api_bp
from .auth import auth_bp

def create_app():
    app = Flask(__name__)
    socketio = SocketIO(app, cors_allowed_origins="*")

    @app.route('/')
    def landing():
        return render_template('landing.html')
    
    @app.route('/app')
    def app_view():
        return render_template('app.html')
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    @socketio.on('join')
    def on_join(data):
        project_id = data['projectId']
        join_room(str(project_id))
        emit('status', {'msg': 'Connected to project room'}, room=str(project_id))

    @socketio.on('leave')
    def on_leave(data):
        project_id = data['projectId']
        leave_room(str(project_id))
        emit('status', {'msg': 'Left project room'}, room=str(project_id))

    return app, socketio
