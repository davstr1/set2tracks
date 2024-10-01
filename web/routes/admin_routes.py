from operator import is_
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user


from lang import Lang
from web.controller import channel_toggle_followable, channel_toggle_visibility, get_channels_with_feat, get_hidden_channels, get_hidden_sets, get_set_searches, queue_discard_set, queue_reset_set, remove_set_temp_files, search_toggle_featured, set_toggle_visibility
from web.logger import logger
from web.model import SetQueue
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
        
    return redirect(url_for('set.set',set_id=set_id))


@admin_bp.route('/admin/channel/toggle_visible/<int:channel_id>', methods=['GET'])  
def channel_visibility_toggle(channel_id):

    if not is_admin():
        flash('You are not an admin', 'error')
        return redirect(url_for('set.sets'))
    
    result = channel_toggle_visibility(channel_id)
    
    if isinstance(result, dict) and 'error' in result:
        flash(result['error'], 'error')
    elif isinstance(result, dict) and 'message' in result:
        flash(result['message'], 'success')
    
    return redirect(request.referrer or url_for('set.sets'))
        
    #return render_template(url_for('set',set_id=set_id))
   
@admin_bp.route('/admin/channel/toggle_followable/<int:channel_id>', methods=['GET'])  
def channel_followability_toggle(channel_id):

    if not is_admin():
        flash('You are not an admin', 'error')
        return redirect(url_for('set.sets'))
    
    result = channel_toggle_followable(channel_id)
    
    if isinstance(result, dict) and 'error' in result:
        flash(result['error'], 'error')
    elif isinstance(result, dict) and 'message' in result:
        flash(result['message'], 'success')
    
    return redirect(request.referrer or url_for('set.sets'))
    
@admin_bp.route('/admin')
def admin():
    if not is_admin():
        flash('You are not an admin', 'error')
        return redirect(url_for('set.sets'))
    
    l = {
        'page_title': Lang.ADMIN + ' - ' + 'Dashboard', 
    }
    
    return render_template('admin/index.html',tpl_utils=tpl_utils,l=l)
    
    
@admin_bp.route('/admin/hidden_sets')
def hidden_sets():
    if not is_admin():
        flash('You are not an admin', 'error')      
        return redirect(url_for('set.sets'))
    
    sets = get_hidden_sets()
    
    l = {
        'page_title': Lang.ADMIN + ' - ' + 'Hidden Sets', 
    }
    
    return render_template('admin/hidden_sets.html', sets=sets,tpl_utils=tpl_utils,l=l)


@admin_bp.route('/admin/channels',methods=['GET'])
def channels():
    if not is_admin():
        flash('You are not an admin', 'error')      
        return redirect(url_for('set.sets'))
    
    feat = request.args.get('feat', 'hidden')    
    channels = get_channels_with_feat(feat)
    
    l = {
        'page_title': Lang.ADMIN + ' - ' + 'Hidden Channels', 
    }
    
    return render_template('admin/channels.html', channels=channels,tpl_utils=tpl_utils,l=l)


@admin_bp.route('/admin/tags')
def tags(featured=None,sort_by='nb_results'):
    if not is_admin():
        flash('You are not an admin', 'error')      
        return redirect(url_for('set.sets'))
    
    tags = get_set_searches(sort_by=sort_by,featured=featured)
    
    l = {
        'page_title': Lang.ADMIN + ' - ' + 'Tags', 
    }
    
    return render_template('admin/tags.html',tags=tags,tpl_utils=tpl_utils,l=l)


@admin_bp.route('/admin/tag_toggle/<int:tag_id>', methods=['GET'])
def tag_toggle(tag_id):
    if not is_admin():
        flash('You are not an admin', 'error')      
        return redirect(url_for('set.sets'))
    
    result = search_toggle_featured(tag_id)
        
    return redirect(url_for('admin.tags'))



@admin_bp.route('/sets/queue/<int:queue_id>/discard', methods=['GET'])
def queue_discard(queue_id):
    if not is_admin():
        return redirect(url_for('users.login', next=url_for('set.sets_queue')))
    
    set_queue_item = SetQueue.query.get(queue_id)
    if not set_queue_item:
        flash('Set not found in queue.', 'error')
        return redirect(request.referrer or url_for('set.sets_queue'))

    if set_queue_item.status != 'failed' and set_queue_item.status != 'processing':
        flash('Only failed or processing sets can be discarded.', 'error')
        return redirect(request.referrer or url_for('set.sets_queue'))
    
    
    queue_discard_set(set_queue_item)
    
    flash('Set discarded.', 'success')
    return redirect(request.referrer or url_for('set.sets_queue'))


@admin_bp.route('/sets/queue/<int:queue_id>/reset', methods=['GET'])
def queue_reset(queue_id):
    if not is_admin():
        return redirect(url_for('users.login', next=url_for('set.sets_queue')))
    
    set_queue_item = SetQueue.query.get(queue_id)
    if not set_queue_item:
        flash('Set not found in queue.', 'error')
        return redirect(request.referrer or url_for('set.sets_queue'))

    if set_queue_item.status == 'pending':
        flash('Pending sets can not be discarded.', 'error')
        return redirect(request.referrer or url_for('set.sets_queue'))
    
    
    result = queue_reset_set(set_queue_item)
    
    if isinstance(result, dict) and 'error' in result:
        flash(result['error'], 'error')
    else:
        flash('Set reset.', 'success')
        
    return redirect(request.referrer or url_for('set.sets_queue'))
