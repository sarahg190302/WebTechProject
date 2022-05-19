from flask import Flask, request, redirect, url_for, flash, abort
from flask import render_template
from flask import current_app as app
from flask_security import login_required
import flask_login, json
from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField, HiddenField)
from wtforms.validators import InputRequired, Length, AnyOf, ValidationError
from application.controllers.app_api.response_codes import show_404
from application.models import *
from datetime import datetime, timedelta
import collections
import numpy as np
from scipy import stats
from .custom_handles import *

# ===============================================TRACKER VALIDATION==========================================================

form_tracker_types = ['ms', 'integer', 'float', 'timerange']
timerange_format = '%m/%d/%Y %I:%M %p'

def check_tid(form, field):
    tracker_data = Tracker.query.filter_by(user_id=flask_login.current_user.id, id=form.tid.data).one_or_none()
    if not tracker_data:
        raise ValidationError("Don't mess around with Tracker ID")

class Add_Tracker_Form(FlaskForm):
    tname = StringField('Tracker Name', validators=[InputRequired(), Length(min=5, max=55)])
    tdescription = TextAreaField('Tracker Description', validators=[Length(max=255)])
    ttype = SelectField('Tracker Type', choices=form_tracker_types, validators=[InputRequired(), AnyOf(form_tracker_types, message='Invalid Type supplied')])
    tchoices = TextAreaField('Multi Select choices')
    tsettings = StringField('Tracker Settings', validators=[InputRequired()])

class Edit_Tracker_Form(Add_Tracker_Form):
    tid = HiddenField('Current Tracker ID', validators = [InputRequired(), check_tid])
    oldtype = HiddenField('Old Tracker Type', validators = [InputRequired(), AnyOf(form_tracker_types, message="Old validator is of invalid type")])

# ========================================================================================================================


# =============================================ADD TRACKER PAGE===========================================================
@app.route('/tracker/add', methods = ['GET', 'POST'])
@login_required
def add_tracker():
    try:
        # if the requested method is GET
        if request.method == 'GET':
            return render_template('tracker/add_edit.html', title='Add Tracker')
        else:
            add_form = Add_Tracker_Form()
            # TODO Add tracker choice - time duration
            if not add_form.validate_on_submit():
                flash('Validation error occurred while adding tracker', 'danger')
                return render_template('tracker/add_edit.html', title='Add Tracker', form=add_form, retry=True)
            try:
                # get the new tracker's object
                new_tracker = Tracker(name = request.form['tname'], description = request.form['tdescription'], user_id=flask_login.current_user.id)
                # add the detais of new tracker to database session
                db.session.add(new_tracker)
                # flushes the session, so we get the new tracker's id from database, without committing to disc yet.
                db.session.flush()
                # get all the settings from json format, remove spaces and split by comma
                for i in json.loads(request.form['tsettings']):
                    # make settings object
                    new_setting = Settings(tracker_id = new_tracker.id, value = i['value'])
                    # add the details of new settings to db session
                    db.session.add(new_setting)
                
                # flushes the session, so we get the new tracker's id from database, without committing to disc yet.
                db.session.flush()

                ttype = request.form['ttype']
                # if tracker type is multiple select
                if ttype == 'ms':
                    # get all the choices splitted across the \n
                    tchoices = json.loads(request.form['tchoices'])
                    # add each choice to the database
                    for i in tchoices:
                        new_choice = Tracker_type(tracker_id  = new_tracker.id, datatype = ttype, value = i['value'].strip())
                        db.session.add(new_choice)
                
                # if tracker type is integer values
                else:
                    new_choice = Tracker_type(tracker_id  = new_tracker.id, datatype = ttype, value = None)
                    db.session.add(new_choice)

                # commit all the changes commited to settings so far
                db.session.commit()
            except:
                # some internal error occurred
                app.logger.exception('Error occurred while adding Tracker')
                # rollback whatever the last session changes were.
                db.session.rollback()            
                # set error flash message
                flash('There was an error adding the tracker', 'danger')
                # redirect to home page
                return redirect(url_for('home_page'))


            # set success flash message to be displayed on home page
            flash('Successfully added Tracker', 'success')
            # redirect to home page
            return redirect(url_for('home_page'))
    except:
        app.logger.exception("Error occurred")
        abort(500)

# =========================================================================================================================





# =============================================EDIT TRACKER PAGE===========================================================
@app.route('/tracker/<int:id>/edit', methods = ['GET', 'POST'])
@login_required
def edit_tracker(id):
    try:
        # if the request method is get
        # check if a tracker with the provided id and made by current user exists or not.
        tracker_data = Tracker.query.filter_by(user_id=flask_login.current_user.id, id=id).one_or_none()
        # if it exists, proceed.
        if tracker_data:
            # get datatype of the tracker
            datatypes = list(set([i.datatype for i in tracker_data.ttype]))
            # collect all the data about the current tracker being edited.
            data = {
                'id': tracker_data.id,
                'name': tracker_data.name,
                'description': tracker_data.description,
                'user_id': tracker_data.user_id,
                'settings': ",".join([i.value for i in tracker_data.settings]),
                # set datatype to empty if no type is defined earlier
                'type': datatypes[0] if len(datatypes) > 0 else '',
                # get all the choices of the tracker, replace NULL values with ''
                'choices': [(i.id, (i.value if i.value else '')) for i in tracker_data.ttype] if len(datatypes) > 0 else ''
            }
            if request.method == 'GET':
                flash('Opened tracker', 'info')
                return render_template('tracker/add_edit.html', title=f'Edit Tracker {id}', edit_mode=True, tracker=data)
                    
            else:
                edit_form = Edit_Tracker_Form()
                # if it exists, proceed. Additionally also check if tracker url id and form hidden field id matches or not.
                if not edit_form.validate_on_submit():
                    flash('Validation error occurred while editing tracker', 'danger')
                    return render_template('tracker/add_edit.html', form=edit_form, retry=True, title=f'Edit Tracker {id}', edit_mode=True, tracker=data)

                if id == int(request.form['tid']):
                    try:
                        # update values of tracker
                        tracker_data.name = request.form['tname']
                        tracker_data.description = request.form['tdescription']

                        # delete all the old settings of a tracker
                        for i in Settings.query.filter_by(tracker_id=id).all():
                            db.session.delete(i)
                        
                        # add new settings for the tracker
                        for i in json.loads(request.form['tsettings']):
                            # make settings object
                            new_setting = Settings(tracker_id = tracker_data.id, value = i['value'])
                            # add the details of new settings to db session
                            db.session.add(new_setting)
                        
                        # delete old data_types for the tracker                
                        #for i in tracker_data.ttype:
                        #    db.session.delete(i)
                        


                        # add new data types for the tracker
                        ttype = request.form['ttype']
                        oldtype = request.form['oldtype']

                        if oldtype != ttype:
                            for i in tracker_data.ttype:
                                db.session.delete(i)
                            old_logs = Tracker_log.query.filter_by(tracker_id = tracker_data.id).all()
                            for ol in old_logs:
                                db.session.delete(ol)
                            # if tracker type is multiple select
                            if ttype == 'ms':
                                # get all the choices splitted across the \n
                                tchoices = json.loads(request.form['tchoices'])
                                # add each choice to the database
                                for i in tchoices:
                                    new_choice = Tracker_type(tracker_id  = tracker_data.id, datatype = ttype, value = i['value'])
                                    db.session.add(new_choice)
                            
                            # if tracker type is integer values
                            else:
                                new_choice = Tracker_type(tracker_id  = tracker_data.id, datatype = ttype, value = None)
                                db.session.add(new_choice)
                        
                        else:
                            # if tracker type is multiple select
                            if ttype == 'ms':
                                tchoices = json.loads(request.form['tchoices'])
                                old_ids = [x.id for x in tracker_data.ttype]
                                
                                
                                for x in tchoices:
                                    if 'id' in x:
                                        choice_from_db = Tracker_type.query.filter_by(id=x['id']).one_or_none()                                    
                                        if choice_from_db != None:
                                            choice_from_db.value = x['value']                                    
                                        old_ids.remove(x['id'])
                                    
                                    else:
                                        new_choice = Tracker_type(tracker_id  = tracker_data.id, datatype = ttype, value = x['value'].strip())
                                        db.session.add(new_choice)
                                
                                if len(old_ids) > 0:
                                    for o in old_ids:
                                        tlogs = Tracker_log.query.filter_by(tracker_id=tracker_data.id).all()
                                        logIDs = [i.id for i in tlogs]

                                        old_vals = Tracker_log_value.query.filter_by(value=o).all()
                                        for ol in old_vals:
                                            if ol.log_id in logIDs:
                                                tlogs_single = Tracker_log.query.filter_by(id=ol.log_id).one_or_none()
                                                db.session.delete(tlogs_single)

                                        choice_from_db = Tracker_type.query.filter_by(id=o).one_or_none()
                                        db.session.delete(choice_from_db)
                        
                        # commit all the above changes to the database
                        db.session.commit()
                    
                    except:
                        app.logger.exception(f'Error ocurred while editing tracker with id {id}')
                        # if any internal error occurs, rollback the database
                        db.session.rollback()
                        flash('Internal error occurred, wasn\'t able to update tracker', 'danger')
                        return redirect(url_for('edit_tracker', id=id))
                    
                    flash('Succesfully updated tracker info', 'success')
                    return redirect(url_for('show_tracker_log', id=tracker_data.id))
                else:
                    return show_normal_404()
        else:
            return show_normal_404()
    except:
        app.logger.exception("Error occurred")
        abort(500)

# =========================================================================================================================




# ============================================DELETE TRACKER PAGE==========================================================
@app.route('/tracker/<int:id>/delete', methods = ['GET'])
@login_required
def delete_tracker(id):
    try:
        # check if a tracker with the provided id and made by current user exists or not.
        tracker_data = Tracker.query.filter_by(user_id=flask_login.current_user.id, id=id).one_or_none()
        # if it exists, proceed.
        if tracker_data:
            try:            
                db.session.delete(tracker_data)
                db.session.commit()
            except:
                app.logger.exception(f'Error ocurred while deleting tracker with id {id}')
                # if any internal error occurs, rollback the database
                db.session.rollback()
                flash('Internal error occurred, wasn\'t able to delete tracker', 'danger')
                return redirect(url_for('home_page'))
            
            flash('Succesfully deleted tracker', 'success')
            return redirect(url_for('home_page'))
        else:
            return show_normal_404()
    except:
        app.logger.exception("error occurred")
        abort(500)

# =========================================================================================================================

# =================================================SHOW TRACKER INFO=======================================================
@app.route('/tracker/<int:id>/show', methods = ['GET', 'POST'], defaults= {'period': 'm'})
@app.route('/tracker/<int:id>/show/<string:period>', methods = ['GET', 'POST'])
@login_required
def show_tracker_log(id, period):
    try:
        # check if a tracker with the provided id and made by current user exists or not.
        tracker_data = Tracker.query.filter_by(user_id=flask_login.current_user.id, id=id).one_or_none()
        # if it exists, proceed.
        if tracker_data:
            datatypes = list(set([i.datatype for i in tracker_data.ttype]))
            tdata = {
                'id': tracker_data.id,
                'name': tracker_data.name,
                'description': tracker_data.description,
                'user_id': tracker_data.user_id,
                'settings': ",".join([i.value for i in tracker_data.settings]),
                'type': datatypes[0] if len(datatypes) > 0 else '',
                'choices': {i.id: (i.value.strip() if i.value else '') for i in tracker_data.ttype}
            }
            log_data = []
            if tdata['type'] != 'timerange':
                chart_data = {}
            else:
                chart_data = []
            
            all_values = []
            for i in tracker_data.values:
                this_data = {
                    'id': i.id,
                    'timestamp': i.timestamp,
                    'note': i.note,
                    'value': [tdata['choices'][int(x.value)] for x in i.values] if tdata['type'] == 'ms' else [x.value for x in i.values]
                }
                log_data.append(this_data)

                if tdata['type'] == 'ms':                
                    options = list(set(this_data['value']))
                    for x in options:
                        if x in chart_data:
                            chart_data[x] += this_data['value'].count(x)
                        else:
                            chart_data[x] = this_data['value'].count(x)
                
                elif tdata['type'] in ['integer', 'float']:
                    all_values.append(int("".join(this_data['value'])) if tdata['type'] == 'integer' else float("".join(this_data['value'])))
                    include = False
                    difference_in_time = datetime.today() - this_data['timestamp']
                    if period == 'w' and difference_in_time.days <= 7:
                        ts = datetime.strftime(i.timestamp, "%Y-%m-%d")
                        include = True
                    elif period == 'm' and difference_in_time.days <= 30:
                        ts = datetime.strftime(i.timestamp, "%Y-%m-%d")                
                        include = True
                    elif period == 'd' and difference_in_time.days <= 0:
                        ts = datetime.strftime(i.timestamp, "%H:%M")                    
                        include = True
                    elif period == 'a':
                        ts = datetime.strftime(i.timestamp, "%Y-%m-%d")
                        include = True
                    
                    if include:
                        if ts in chart_data:
                            chart_data[ts] += int("".join(this_data['value'])) if tdata['type'] == 'integer' else float("".join(this_data['value']))
                        else:
                            chart_data[ts] = int("".join(this_data['value'])) if tdata['type'] == 'integer' else float("".join(this_data['value']))
                
                else:
                    theTime = ("".join(this_data['value'])).split('-')
                    start = theTime[0].strip()
                    end = theTime[1].strip()

                    difference_in_time = datetime.today() - datetime.strptime(start, timerange_format)
                    if period == 'w' and difference_in_time.days > 7:
                        start = datetime.strftime(datetime.today() - timedelta(7), timerange_format)
                    elif period == 'm' and difference_in_time.days > 30:
                        start = datetime.strftime(datetime.today() - timedelta(30), timerange_format)
                    elif period == 'd' and difference_in_time.days > 0:
                        start = datetime.strftime(datetime.today(), timerange_format)
                    elif period == 'a':
                        start = start
                    
                    endTimeDiff = datetime.today() - datetime.strptime(end, timerange_format)
                    if period == 'w' and endTimeDiff.days > 7:
                        end = start
                    elif period == 'm' and endTimeDiff.days > 30:
                        end = start
                    elif period == 'd' and endTimeDiff.days > 0:
                        end = start
                    elif period == 'a':
                        end = end

                    timeData = {
                        "id": this_data['id'],
                        "note": this_data['note'],
                        "start": start,
                        "end" :  end
                    }
                    if start != end:
                        chart_data.append(timeData)

            if tdata['type'] in ['integer', 'float']:
                if period == 'w':
                    delta = 7
                    for i in range(delta):
                        key = datetime.strftime(datetime.today()-timedelta(i), "%Y-%m-%d")
                        if key not in chart_data:
                            chart_data[key] = 0
                elif period == 'm':
                    delta = 30
                    for i in range(delta):
                        key = datetime.strftime(datetime.today()-timedelta(i), "%Y-%m-%d")
                        if key not in chart_data:
                            chart_data[key] = 0
                elif period == 'd':
                    delta = 24
                    for i in range(delta):
                        key = datetime.strftime(datetime.today()-timedelta(hours=i), "%H:00")
                        if key not in chart_data:
                            chart_data[key] = 0
            log_data = sorted(log_data, key=lambda d: d['timestamp'],reverse=True)
            extra = {
                'mean': None,
                'median': None,
                'mode': None,
                '25th': None,
                '75th': None
            }
            if tdata['type'] in ['integer', 'float']:
                if len(all_values) > 0:
                    extra['mean'] = np.mean(all_values)
                    extra['median'] = np.median(all_values)
                    extra['mode'] = stats.mode(all_values)
                    extra['25th'] = np.percentile(all_values, 25)
                    extra['75th'] = np.percentile(all_values, 75)
            
            return render_template('tracker/show.html', extra=extra, title=f"Logs {tdata['name']}", tracker = tdata, logs = log_data, period = period, total=len(tracker_data.values), chart=collections.OrderedDict(sorted(chart_data.items())) if tdata['type'] != 'timerange' else chart_data )
        else:
            return show_normal_404()
    except:
        app.logger.exception("Error occurred")
        abort(500)


# =========================================================================================================================


@app.route('/tracker/<int:tracker_id>/logs/delete_all', methods = ['GET'])
@login_required
def delete_all_tracker_logs(tracker_id):
    try:
        # check if a tracker with the provided id and made by current user exists or not.
        tracker_data = Tracker.query.filter_by(user_id=flask_login.current_user.id, id=tracker_id).one_or_none()
        # if it exists, proceed.
        if tracker_data:
            all_log_data = Tracker_log.query.filter_by(tracker_id=tracker_data.id).all()
            if all_log_data:
                try:
                    for log_data in all_log_data:                                
                        db.session.delete(log_data)
                    db.session.commit()
                except:
                    app.logger.exception(f'Error ocurred while deleting all logs')
                    # if any internal error occurs, rollback the database
                    db.session.rollback()
                    flash('Internal error occurred, wasn\'t able to delete tracker log', 'error')
                    return redirect(url_for('home_page'))
            
                flash('Succesfully deleted all tracker logs', 'success')
                return redirect(url_for('show_tracker_log', id=tracker_id))
            else:
                return show_normal_404()
        else:
            return show_normal_404()
    except:
        app.logger.exception("error occurred")
        abort(500)