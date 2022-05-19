from flask import current_app as app
from flask import jsonify, make_response
from application.models import *
from flask_restful import Resource, reqparse
from flask_expects_json import expects_json
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required

from .response_codes import *
from .schema import *

class Each_Tracker_api(Resource):
    @jwt_required()
    def get(self, id):
        try:
            user_id = get_jwt_identity()
            tracker_data = Tracker.query.filter_by(user_id=user_id, id=id).one_or_none()
            if tracker_data:
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

                return make_response(jsonify(data), 200)
            else:
                return show_404()
        except:
            app.logger.exception("API_ETA1")
            return show_500()
    
    @jwt_required()
    def delete(self, id):
        user_id = get_jwt_identity()
        tracker_data = Tracker.query.filter_by(user_id=user_id, id=id).one_or_none()
        # if it exists, proceed.
        if tracker_data:
            try:            
                db.session.delete(tracker_data)
                db.session.commit()
            except:
                app.logger.exception(f'API_ETA2: Error ocurred while deleting tracker with id {id}')
                # if any internal error occurs, rollback the database
                db.session.rollback()
                return show_500()
            
            return show_200('deletion success')
        else:
            return show_404()

    @expects_json(patch_tracker_schema)
    @jwt_required()
    def patch(self, id):
        tracker_patch_args = reqparse.RequestParser()
        tracker_patch_args.add_argument('name')
        tracker_patch_args.add_argument('description')
        tracker_patch_args.add_argument('settings', type=str, action='append')
        tracker_patch_args.add_argument('type', choices=allowed_choices)
        tracker_patch_args.add_argument('choices', type=dict, action='append')
        tracker_patch_args.add_argument('delete_choices')

        # if the request method is get
        # check if a tracker with the provided id and made by current user exists or not.
        user_id = get_jwt_identity()
        tracker_data = Tracker.query.filter_by(user_id=user_id, id=id).one_or_none()
        # if it exists, proceed.
        if not tracker_data:
            return show_404()

        try:
            args = tracker_patch_args.parse_args()
            name = args.get('name', None)
            description = args.get('description', None)
            settings = args.get('settings', None)
            ttype = args.get('type', None)
            choices = args.get('choices', None)
            delete_choices = args.get('delete_choices', False)

            tracker_data.name = name if name != None else tracker_data.name
            tracker_data.description = description if description != None else tracker_data.description
            
            if settings != None:
                for i in Settings.query.filter_by(tracker_id=id).all():
                    db.session.delete(i)
                
                for i in settings:
                    # make settings object
                    new_setting = Settings(tracker_id = tracker_data.id, value = i.strip())
                    # add the details of new settings to db session
                    db.session.add(new_setting)
            
            if ttype == None:
                datatypes = list(set([i.datatype for i in tracker_data.ttype]))
                ttype = datatypes[0] if len(datatypes) > 0 else '' 
            
            datatypes = list(set([i.datatype for i in tracker_data.ttype]))
            oldtype = datatypes[0] if len(datatypes) > 0 else ''                
            
            if oldtype != ttype:
                for i in tracker_data.ttype:
                    db.session.delete(i)
                old_logs = Tracker_log.query.filter_by(tracker_id = tracker_data.id).all()
                for ol in old_logs:
                    db.session.delete(ol)
                # if tracker type is multiple select
                if ttype == 'ms':
                    if choices != None:
                        for i in choices:
                            new_choice = Tracker_type(tracker_id  = tracker_data.id, datatype = ttype, value = i['new_name'].strip())
                            db.session.add(new_choice)
                    else:
                        return show_400('choices can\'t be empty if changing type to multi-select')
                
                # if tracker type is integer values
                else:
                    new_choice = Tracker_type(tracker_id  = tracker_data.id, datatype = ttype, value = None)
                    db.session.add(new_choice)
            
            else:
                # if tracker type is multiple select
                if ttype == 'ms':
                    if choices != None and not delete_choices:                        
                        for x in choices:                            
                            if 'id' in x and x['id'] != None and x['id'] != "":
                                new_value = x['new_name']
                                choice_db = Tracker_type.query.filter_by(id=x['id']).one_or_none()
                                if choice_db != None:
                                    if new_value != '':                                
                                            choice_db.value = new_value                                
                                    else:
                                        vals = db.delete(Tracker_log_value).where(Tracker_log_value.value.in_([choice_db.id]))                                    
                                        db.session.execute(vals)
                                        db.session.delete(choice_db)
                                else:
                                    return show_400(f'Choice with id {x["id"]} does not exist')
                            else:                            
                                if x['new_name'] != '' and x['new_name'] != None:
                                    new_choice = Tracker_type(tracker_id  = tracker_data.id, datatype = ttype, value = x['new_name'].strip())
                                    db.session.add(new_choice)
                                else:
                                    return show_400(f'new_name cannot be empty if adding new choice')
            
            if ttype == 'ms' and delete_choices:
                all_choices = Tracker_type.query.filter_by(tracker_id=tracker_data.id).all()
                for x in all_choices:
                    vals = db.delete(Tracker_log_value).where(Tracker_log_value.value.in_([x.id]))                                    
                    db.session.execute(vals)
                    db.session.delete(x)
                
                new_choice = Tracker_type(tracker_id = tracker_data.id, datatype=ttype, value="placeholder choice")
                db.session.add(new_choice)
                

                # commit all the above changes to the database
            db.session.commit()
            return show_200()
        except:
            app.logger.exception(f'API_ETA3: Error ocurred while editing tracker with id {id}')
            # if any internal error occurs, rollback the database
            db.session.rollback()
            return show_500()
