import os, logging
from flask import Flask
from application import config
from application.config import LocalDevelopmentConfig
from application.database import db

from application.models import User, Role
from flask_security import Security, SQLAlchemySessionUserDatastore, SQLAlchemyUserDatastore
from flask_security import RegisterForm
from wtforms import StringField
from wtforms.validators import DataRequired

from flask_restful import Api
from flask_jwt_extended import JWTManager

# set the configurations for the log file
logging.basicConfig(filename='debug.log', level=logging.INFO, format='[%(levelname)s %(asctime)s %(name)s] ' + '%(message)s')
# set app = None to initialize variable
app = None


def create_app():
    '''This function creates a flask app along with all the necessary db, context, security relating things.
    '''
    # create flask app with name = __name__ and template folder where .html are stored
    app = Flask(__name__, template_folder='templates')

    # check if flask environment is is development
    if os.environ.get('FLASK_ENV') == 'development':
        app.logger.info('STARTING DEVELOPMENT ENVIRONMENT')
        # load development configurations
        app.config.from_object(LocalDevelopmentConfig)
    
    # initialize database
    db.init_app(app)
    app.app_context().push()

    # this is used to extend the registration form in Flask-Security. This inherits
    # the Flask-Security's already created RegisterForm class.
    class ExtendedRegisterForm(RegisterForm):
        # the additional field we are adding to the form, name of variable must be exactly same as database attribute.
        username = StringField('Full Name', [DataRequired()])

    # initialize the Flask-Security.
    user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
    # this provides a current_user object in all the possible templates.
    security = Security(app, user_datastore, register_form=ExtendedRegisterForm)

    app.logger.info('App setup complete.')
    return app

app = create_app()

# import default controllers
from application.controllers.default import *
# import controllers related to trackers
from application.controllers.tracker import *
# import controllers related to logging of trackers
from application.controllers.log import *
from application.controllers.autologger import *


from application.controllers.app_api.schema import *
from application.controllers.app_api.response_codes import *
from application.controllers.app_api.auth import *
from application.controllers.app_api.single_tracker import *
from application.controllers.app_api.all_trackers import *
from application.controllers.app_api.all_logs import *
from application.controllers.app_api.single_log import *
from application.controllers.app_api.stats import *

# import error handling controllers
from application.controllers.error_handlers import *

api = Api(app)
jwt = JWTManager(app)
api.add_resource(Each_Tracker_api, "/api/tracker/<int:id>")
api.add_resource(Trackers_api, "/api/tracker")
api.add_resource(Each_Log_api, "/api/tracker/<int:tracker_id>/logs/<int:log_id>")
api.add_resource(Logs_api, "/api/tracker/<int:tracker_id>/logs")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)