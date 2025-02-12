# main.py
import asyncio
import atexit
import threading
from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_httpauth import HTTPTokenAuth
from flask_jwt_extended import JWTManager, get_jwt_identity
from flask_session import Session
from flask_cors import CORS
from apis import api # init_deposit_monitoring, cleanup_deposit_monitoring
from models import db
from res import CustomError
from datetime import timedelta
import config as app_config
import logging

auth = HTTPTokenAuth(scheme='Bearer')

class MonitoringManager:
    def __init__(self):
        self.monitor_thread = None
        self.loop = None
        self.should_stop = False
        self._monitoring_started = False

    def start_monitoring(self, app):
        """Start monitoring in a separate thread"""
        if self.monitor_thread is not None or self._monitoring_started:
            return

        self._monitoring_started = True

        def run_async_monitoring():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            with app.app_context():
                try:
                    from apis.deposit.deposit_helper import deposit_helper
                    
                    async def monitor():
                        try:
                            async def deposit_callback(deposit_data):
                                app.logger.info(f"Processing deposit: {deposit_data}")
                                
                            await deposit_helper.start_monitoring(deposit_callback)
                        except Exception as e:
                            app.logger.error(f"Error in monitoring: {str(e)}")

                    self.loop.run_until_complete(monitor())
                except Exception as e:
                    app.logger.error(f"Failed to start monitoring: {str(e)}")
                finally:
                    self.loop.close()

        self.monitor_thread = threading.Thread(target=run_async_monitoring)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        app.logger.info("Deposit monitoring started")

    def stop_monitoring(self):
        """Stop the monitoring thread"""
        if self.monitor_thread is None:
            return

        if self.loop is not None:
            async def cleanup():
                from apis.deposit.deposit_helper import deposit_helper
                await deposit_helper.stop_monitoring()

            if not self.loop.is_closed():
                self.loop.run_until_complete(cleanup())
                self.loop.close()

        self.monitor_thread.join(timeout=5)
        self.monitor_thread = None
        self.loop = None
        self._monitoring_started = False

monitor_manager = MonitoringManager()

def create_app():
    app = Flask(__name__)
    print(f"Initializing app with SECRET_KEY: {app_config.config.SECRET_KEY[:10]}...") 
    # Configuration
    
    app.config['JWT_SECRET_KEY'] = app_config.config.SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

    app.config['JWT_DECODE_ALGORITHMS'] = ['HS256']
    app.config['JWT_ENCODE_NBF'] = False  # Disable "not before" claim
    app.config['JWT_ERROR_MESSAGE_KEY'] = 'message'

    app.config['SECRET_KEY'] = app_config.config.SECRET_KEY
    app.config['SESSION_PERMANENT'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = app_config.config.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)
    app.config['UPLOAD_FOLDER'] = 'uploads/'

    # Initialize extensions
    db.init_app(app)
    api.init_app(app)
    Session().init_app(app)
    jwt = JWTManager(app)
    migrate = Migrate(app, db)
    CORS(app)
    
    @app.before_request
    def start_monitoring():
        monitor_manager.start_monitoring(app)

    atexit.register(monitor_manager.stop_monitoring)

    @app.route('/')
    def index():
        return 'received!', 200

    @app.route('/health')
    def health():
        return "I'm healthy", 200

    @app.errorhandler(CustomError)
    def handle_custom_error(error):
        response = {
            "error": {
                "status_code": error.error_code,
                "message": error.message
            }
        }
        return jsonify(response), error.error_code

    # Register additional routes
    from routes import register_additional_routes
    register_additional_routes(app)

    return app

# Create the Flask application instance
app = create_app()

if __name__ == '__main__':
    if app_config.config.ENV != 'development':
        from waitress import serve
        serve(app, host="0.0.0.0", port=8080)
    else:
        app.run(debug=True)