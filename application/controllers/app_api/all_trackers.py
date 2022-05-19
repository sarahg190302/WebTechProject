from flask import current_app as app
from flask import jsonify, make_response
from application.models import *
from flask_restful import Resource, reqparse
from flask_expects_json import expects_json
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required

from .response_codes import *
from .schema import *

class Trackers_api(Resource):
    @jwt_required()
    def get(self):
        try:
            user_id = get_jwt_identity()
            all_tracker_data = Tracker.query.filter_by(user_id=user_id).all()
            if all_tracker_data:
                final_data = []
                for tracker_data in all_tracker_data:
                    datatypes = list(set([i.datatype for i in tracker_data.ttype]))
                    data = {
                        'id': tracker_data.id,
                        'name': tracker_data.name,
                        'description': tracker_data.description,
                        'type': datatypes[0] if len(datatypes) > 0 else '',
                        'settings': [i.value for i in tracker_data.settings]
                    }
                    if data['type'] == 'ms':
                        data['choices'] = []
                        for i in tracker_data.ttype:
                            data['choices'].append({"id": i.id, "value": i.value})
                    else:
                        data['choices'] = None
                    
                    final_data.append(data)
                return make_response(jsonify(final_data), 200)
            else:
                return show_404()
        except:
            app.logger.exception("API_TA1")
            return show_500()
    

    @expects_json(add_tracker_schema)
    @jwt_required()
    def post(self):
        tracker_input_args = reqparse.RequestParser()
        tracker_input_args.add_argument('name')
        tracker_input_args.add_argument('description')
        tracker_input_args.add_argument('settings', type=str, action='append')
        tracker_input_args.add_argument('type', choices=allowed_choices)
        tracker_input_args.add_argument('choices', type=str, action='append')

        args = tracker_input_args.parse_args()
        name = args.get('name', None)
        description = args.get('description', None)
        settings = args.get('settings', None)
        ttype = args.get('type', None)
        choices = args.get('choices', None)
        
        try:
            user_id = get_jwt_identity()
            # get the new tracker's object
            new_tracker = Tracker(name = name, description = description, user_id=user_id)
            # add the detais of new tracker to database session
            db.session.add(new_tracker)
            # flushes the session, so we get the new tracker's id from database, without committing to disc yet.
            db.session.flush()
            # get all the settings, remove spaces and split by comma
            for i in settings:
                # make settings object
                new_setting = Settings(tracker_id = new_tracker.id, value = i.strip())
                # add the details of new settings to db session
                db.session.add(new_setting)
            
            # flushes the session, so we get the new tracker's id from database, without committing to disc yet.
            db.session.flush()

            # if tracker type is multiple select
            if ttype == 'ms':
                if choices != None:
                    # add each choice to the database
                    for i in choices:
                        new_choice = Tracker_type(tracker_id  = new_tracker.id, datatype = ttype, value = i.strip())
                        db.session.add(new_choice)
                
                else:
                    return show_400("choices are required with this type of tracker.")
            
            # if tracker type is integer values
            else:
                new_choice = Tracker_type(tracker_id  = new_tracker.id, datatype = ttype, value = None)
                db.session.add(new_choice)

            # commit all the changes commited to settings so far
            db.session.commit()
            return make_response(jsonify({"msg": "added tracker"}), 201)
        except:
            # some internal error occurred
            app.logger.exception('API_TA2: Error occurred while adding Tracker')
            # rollback whatever the last session changes were.
            db.session.rollback()            
            # set error flash message
            return show_500()
