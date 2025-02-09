from boilersaas.utils.db import db
from web.model import Channel
from datetime import datetime, timezone
from web.logger import logger
from sqlalchemy.exc import SQLAlchemyError



def get_or_create_channel(data):
    
    try:
        channel_id = str(data.get('channel_id'))
        existing_channel = Channel.query.filter_by(channel_id=channel_id).first()
        if existing_channel is not None:
            logger.info("Channel already exists.")
            return existing_channel
        
        logger.info("Creating new channel.")    
        new_channel = Channel(
            channel_id=channel_id,
            author=data.get('channel'),
            channel_url=data.get('channel_url'),
            channel_follower_count=data.get('channel_follower_count'),
            updated_at=datetime.now(timezone.utc)
        )
        db.session.add(new_channel)
        db.session.commit()
        return new_channel
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error in get_or_create_channel: {e}")
        return None

def get_channel_by_id(channel_id):
    channel = Channel.query.get(channel_id)
    if not channel:
        return None
    return channel

def get_channels(page=1, order_by='channel_popularity', per_page=20, search='',hiddens=None):
    """
    Retrieves a paginated list of channels with customizable sorting and filtering options.

    Parameters:
    - page (int, optional): The page number of results to return. Defaults to 1.
    - order_by (str, optional): The order in which to return the channels. 
        - 'recent' (default): Orders by most recently created channels first (descending by creation date).
        - 'old': Orders by oldest channels first (ascending by creation date).
        - 'popular': Orders by channels with the most followers first (descending by follower count).
        - 'small_channel': Orders by channels with the fewest followers first (ascending by follower count).
    - per_page (int, optional): The number of results per page. Defaults to 20.
    - hiddens (bool, optional): If provided, filters channels by their hidden status (True for hidden, False for visible).

    Returns:
    - A paginated list of channels based on the specified criteria.

    Note:
    - The 'error_out=False' ensures that invalid page requests will return an empty result set rather than throwing an error.
    """

    
    query = Channel.query
    

    if order_by == 'az':
        query = query.order_by(Channel.author.asc())
    elif order_by == 'added':
        query = query.order_by(Channel.id.desc())
    else:
        # as popularity is the default and only one other
        query = query.order_by(Channel.channel_follower_count.desc())
        
    if hiddens is not None:
        query = query.filter_by(hidden=hiddens)
        
    if search:
        query = query.filter(Channel.author.ilike(f"%{search}%"))
    
    results = query.paginate(page=page, per_page=per_page, error_out=False)
    count = query.count()
    return results,count

def get_hidden_channels():
    return Channel.query.filter_by(hidden=True).all()

def get_channels_with_feat(feat):
    if feat == 'hidden':
        return get_hidden_channels()
    elif feat == 'not_followable':
        return Channel.query.filter_by(followable=False).all()
    elif feat == 'followable':
        return Channel.query.filter_by(followable=True).all()
    elif feat == 'not_hidden':
        return Channel.query.filter_by(hidden=False).all()
    else:
        return {'error': 'Invalid feat'}

def get_unfollowable_channels():
    return Channel.query.filter_by(followable=False).all()

def channel_toggle_followable(channel_id):
    channel = Channel.query.get(channel_id)
    if not channel:
        return {"error": "Channel not found"}
    
    # Toggle the followable status
    channel.followable = not channel.followable

    db.session.commit()
    return {"message":  f"channel_followable set to {channel.followable}"}


def channel_toggle_visibility(channel_id):
    channel = Channel.query.get(channel_id)
    if not channel:
        return {"error": "Channel not found"}
    
    channel.hidden = not channel.hidden
    # If the channel is hidden, set followable to False
    # But not necessary to set followable to True if channel is unhidden
    if channel.hidden:
        channel.followable = False
    db.session.commit()
    
    return {"message": f"Channel visibility toggled to {not channel.hidden}"}


def get_channel_to_check():   
    channel = Channel.query.filter(Channel.channel_id != 'None',Channel.hidden == False,Channel.followable == True).order_by(Channel.updated_at.asc()).first() # yeah, mysterious channel with None id appears. @TODO

    return channel