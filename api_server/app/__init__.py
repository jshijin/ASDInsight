from flask import Flask,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_pymongo import PyMongo
from pymongo import MongoClient
from app.config import Config
from flask_swagger_ui import get_swaggerui_blueprint
from service.data_service.data_service import DataService
from service.data_processing.data_processing import DataProcessing
from service.model_training.model_training import ModelTraining
from service.eye_tracking.eye_tracking import EyeTracking
from service.qchat_screening.qchat10_screening import QchatScreening
from service.prediction.QCHATPredictor import QCHATPredictor
from app.api import api_bp
import logging
import time
import datetime
import os
# Import the custom logging handler
from app.custom_logging import CustomTimedRotatingFileHandler

# Flask Initialization
app = Flask(__name__)

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set up logging configuration
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

app.config.from_object(Config)

# Initialize MongoDB
mongo = PyMongo(app)
client = MongoClient(app.config["MONGO_URI"])


# Automatically redirect to Swagger UI
@app.route('/')
def index():
    return redirect('/swagger', code=302)


def intialize_app(configName='config'):
    
    swaggerui_blueprint = get_swaggerui_blueprint(
        '/swagger',
        '/static/swagger.json',
        config={
            'app_name': "ASDInsight"
        })
    app.register_blueprint(swaggerui_blueprint)



    # Register the API Blueprint
    app.register_blueprint(api_bp)

    
    # Set up logging
    logger = logging.getLogger('my_logger')
    logger.setLevel(logging.INFO)

    # Create a CustomTimedRotatingFileHandler
    timestr = time.strftime("%Y%m%d-%H%M%S")
    log_file_path = os.path.join(log_dir, f'asdinsight_{timestr}.log')
    handler = CustomTimedRotatingFileHandler(
        filename=log_file_path,
        when='midnight',  # Rotate at midnight
        interval=1,       # Interval in days
        backupCount=7,    # Number of backup files to keep
        encoding='utf-8',
        log_dir=log_dir    # Pass log_dir to the custom handler
    )
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    app.logger.addHandler(handler)

    # Initialize services with configuration
    data_service = DataService(app.config, mongo, app.logger)
    data_processing_service = DataProcessing(app.config, app.logger)
    eye_tracking_service = EyeTracking(app.config,data_service,data_processing_service, app.logger)
    qchat_screening_service = QchatScreening(app.config,data_service,data_processing_service, app.logger)
    model_training_service = ModelTraining(app.config,qchat_screening_service, app.logger)

    # Add services to the app context
    app.data_service = data_service
    app.data_processing_service = data_processing_service
    app.model_training_service = model_training_service
    app.eye_tracking_service = eye_tracking_service
    app.qchat_screening_service = qchat_screening_service

    app.logger.info("Intializing ASDInsight Application")
    return app

