from flask import Flask, request, redirect, url_for, flash, abort
from flask import render_template
from flask import current_app as app
from flask_security import login_required
import flask_login
from application.models import *
from datetime import datetime


# ================================================HOME PAGE===============================================================
# default home page, required to login to see
@app.route('/')
@login_required
def home_page():
    try:
        # this will contain info about trackers of this logged in user
        trackers = []
        # get all trackers made by this user
        for i in Tracker.query.filter_by(user_id=flask_login.current_user.id).all():
            # get the last updated value of this tracker
            updated_at = Tracker_log.query.filter_by(tracker_id=i.id).order_by(Tracker_log.timestamp.desc()).all()
            updated_at = updated_at[0].timestamp if updated_at else "Never"
            # add the info gathered to the list of trackers above.
            trackers.append({'id': i.id, 'name': i.name, 'description': i.description, 'updated_at': updated_at})
        return render_template('home.html', title='Home Page', trackers = trackers)
    except:
        app.logger.exception("error occurred")
        abort(500)

# ========================================================================================================================