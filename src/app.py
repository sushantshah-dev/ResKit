from flask import Flask, render_template
from .auth import auth_bp

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def landing():
        return render_template('landing.html')
    
    @app.route('/app')
    def app_view():
        return render_template('app.html')
    
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app
