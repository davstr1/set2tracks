from operator import is_
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user


from web.controller import channel_toggle_visibility, get_hidden_channels, get_hidden_sets, get_set_searches, set_toggle_visibility
from web.logger import logger
from web.routes.routes_utils import is_admin
from web.routes.set_routes import sets
from web.routes.routes_utils import tpl_utils


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
    
    
@admin_bp.route('/admin/hidden_sets')
def hidden_sets():
    if not is_admin():
        flash('You are not an admin', 'error')      
        return redirect(url_for('set.sets'))
    
    sets = get_hidden_sets()
    
    return render_template('admin/hidden_sets.html', sets=sets,tpl_utils=tpl_utils)


@admin_bp.route('/admin/hidden_channels')
def hidden_channels():
    if not is_admin():
        flash('You are not an admin', 'error')      
        return redirect(url_for('set.sets'))
    
    channels = get_hidden_channels()
    
    return render_template('admin/hidden_channels.html', channels=channels,tpl_utils=tpl_utils)


@admin_bp.route('/admin/tags')
def tags(featured=False,sort_by='nb_results'):
    if not is_admin():
        flash('You are not an admin', 'error')      
        return redirect(url_for('set.sets'))
    
    tags = get_set_searches(sort_by=sort_by,featured=featured)

    
    return render_template('admin/tags.html',tpl_utils=tpl_utils)
