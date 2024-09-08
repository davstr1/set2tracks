from operator import is_
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user


from web.controller import channel_toggle_visibility, set_toggle_visibility
from web.logger import logger
from web.routes.routes_utils import is_admin



admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/set/hide/<int:set_id>', methods=['GET'])  
def set_visibility_toggle(set_id):
    
    if not is_admin():
        flash('You are not an admin', 'error')
        return redirect(url_for('set.sets'))
   
    result = set_toggle_visibility(set_id)
    
    if isinstance(result, dict) and 'error' in result:
        flash(result['error'], 'error')
    elif isinstance(result, dict) and 'message' in result:
        flash(result['message'], 'success')
        
    return redirect(url_for('set.sets'))


@admin_bp.route('/admin/channel/hide/<int:channel_id>', methods=['GET'])  
def channel_visibility_toggle(channel_id):

    if not is_admin():
        flash('You are not an admin', 'error')
        return redirect(url_for('set.sets'))
    
    result = channel_toggle_visibility(channel_id)
    
    if isinstance(result, dict) and 'error' in result:
        flash(result['error'], 'error')
    elif isinstance(result, dict) and 'message' in result:
        flash(result['message'], 'success')
    
    return redirect(url_for('set.sets'))
        
    #return render_template(url_for('set',set_id=set_id))
