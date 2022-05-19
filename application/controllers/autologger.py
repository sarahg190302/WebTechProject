from flask import Flask, request, redirect, url_for, flash, abort
from flask import render_template
from flask import current_app as app
from flask_security import login_required
import flask_login, json
from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField, HiddenField)
from wtforms.validators import InputRequired, Length, AnyOf, ValidationError
from application.models import *
from datetime import datetime, timedelta
import collections
import scipy.stats as ss
import numpy as np

from .custom_handles import *

timerange_format = '%m/%d/%Y %I:%M %p'

@app.route('/tracker/<int:tracker_id>/autolog/<int:size>')
@login_required
def auto_log(tracker_id, size):
    try:
        tracker_data = Tracker.query.filter_by(user_id=flask_login.current_user.id, id=tracker_id).one_or_none()
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
                'choices': [i.id for i in tracker_data.ttype] if len(datatypes) > 0 else ''
            }

            if data['type'] == 'integer':
                x = np.arange(-10, 11)
                xU, xL = x + 0.5, x - 0.5 
                prob = ss.norm.cdf(xU, scale = 3) - ss.norm.cdf(xL, scale = 3)
                prob = prob / prob.sum() # normalize the probabilities so their sum is 1
                random_num = np.random.choice(x, size = size, p = prob)
                for i in range(len(random_num)):
                    log = Tracker_log(tracker_id = tracker_data.id, note = f"Auto Value {i+1}", timestamp = datetime.now() - timedelta(i))
                    db.session.add(log)
                    db.session.flush()
                    x = Tracker_log_value(log_id = log.id, value = int(random_num[i]))
                    db.session.add(x)
                
                db.session.commit()
            
            elif data['type'] == 'float':
                random_num = np.random.random(size=size)
                for i in range(len(random_num)):
                    log = Tracker_log(tracker_id = tracker_data.id, note = f"Auto Value {i+1}", timestamp = datetime.now() - timedelta(i))
                    db.session.add(log)
                    db.session.flush()
                    x = Tracker_log_value(log_id = log.id, value = float(random_num[i] * size))
                    db.session.add(x)
                
                db.session.commit()
            
            elif data['type'] == 'ms':
                random_num = np.random.choice(data['choices'], size=size)
                for i in range(len(random_num)):
                    log = Tracker_log(tracker_id = tracker_data.id, note = f"Auto Value {i+1}", timestamp = datetime.now() - timedelta(i))
                    db.session.add(log)
                    db.session.flush()
                    x = Tracker_log_value(log_id = log.id, value = int(random_num[i]))
                    db.session.add(x)
                
                db.session.commit()
            
            elif data['type'] == 'timerange':            
                for i in range(size):
                    rands = np.random.randint(low=1, high=1000, size=2)
                    start = datetime.now() - timedelta(int(max(rands)))
                    end = datetime.now() - timedelta(int(min(rands)))
                    start = datetime.strftime(start, timerange_format)
                    end = datetime.strftime(end, timerange_format)

                    log = Tracker_log(tracker_id = tracker_data.id, note = f"Auto Value {i+1}", timestamp = datetime.now() - timedelta(i))
                    db.session.add(log)
                    db.session.flush()
                    x = Tracker_log_value(log_id = log.id, value = str(start + ' - ' + end))
                    db.session.add(x)
                
                db.session.commit()
                
            return redirect(url_for("show_tracker_log", id = tracker_id, period='a'))
        else:
            return show_normal_404()
    except:
        app.logger.exception("error occurred")
        abort(500)