"""
database.py

Backend utilities for managing the database.
"""

#!/usr/bin/env python

import random

from flask import url_for

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_, func
from utils.models import Base, ContentItem
from utils.models import Users, Reviews, Friendships, JournalEntry
from utils.models import Collections, Content, CollectionsContent
from utils.spotify import get_content_several_ids, get_content_image

# To-do: error handling e.g. null or repeat values

db = SQLAlchemy(model_class=Base)
Base.query = db.session.query_property()

def db_init(app):
    """Function that initializes the db and creates the tables if necessary"""
    db.init_app(app)

    # Creates the logs, tables if the db doesnt already exist
    with app.app_context():
        db.create_all()

### USERS ###
def create_user(username, password):
    """Add a user to the database"""
    new_user = Users(username=username)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return new_user.id

def update_profile(user_id, bio, favorite_genre):
    """Update user profile in database with the specified bio and favorite genre."""
    user = get_user_by_id(user_id)
    user.bio = bio
    user.favorite_genre = favorite_genre
    db.session.commit()

def get_user_by_id(user_id):
    """Get user information using user id"""
    user = db.session.query(Users).filter(Users.id == user_id).first()

    return user if user else None

### FRIENDS/HOMIES ###
def create_friendship(requester, requested):
    """Adds a new friendship link in the database"""
    new_friend = Friendships(user_id1=requester)
    new_friend.user_id2 = requested

    db.session.add(new_friend)
    db.session.commit()

def is_friend(requester_id, requested_id):
    """Checks if friendship exists"""
    accepted = Friendships.query.filter(
        ((Friendships.user_id1 == requester_id) & (Friendships.user_id2 == requested_id)) |
        ((Friendships.user_id1 == requested_id) & (Friendships.user_id2 == requester_id)),
        Friendships.status.in_(['accepted'])
    ).first()

    requested = Friendships.query.filter(
        ((Friendships.user_id1 == requester_id) & (Friendships.user_id2 == requested_id)) |
        ((Friendships.user_id1 == requested_id) & (Friendships.user_id2 == requester_id)),
        Friendships.status.in_(['pending'])
    ).first()

    return bool(accepted), bool(requested)

def accept_friendship(request_id):
    """Accepts friend request"""
    friend_request = Friendships.query.get(request_id)
    if friend_request and friend_request.status == 'pending':
        friend_request.status = 'accepted'
        db.session.commit()

def reject_friendship(request_id):
    """Rejects friend request"""
    friend_request = Friendships.query.get(request_id)
    if friend_request and friend_request.status == 'pending':
        db.session.delete(friend_request)
        db.session.commit()

def remove_friendship(request_id):
    """Deletes friendship connection"""
    friendship = Friendships.query.get(request_id)
    if friendship and (friendship.status == 'accepted' or friendship.status == 'pending'):
        db.session.delete(friendship)
        db.session.commit()

def get_friends(user_id):
    """Fetching all friendships where the user is either user_id1 or user_id2"""
    friendships = Friendships.query.filter(
        or_(Friendships.user_id1 == user_id, Friendships.user_id2 == user_id),
        Friendships.status.in_(['accepted', 'pending'])
    ).all()

    # Separate lists for friends and pending requests (both sent and received)
    friends = []
    pending_requests_sent = []
    pending_requests_received = []

    for friendship in friendships:
        is_pending = friendship.status == 'pending'
        is_requester = friendship.user_id1 == user_id
        other_user_id = friendship.user_id2 if is_requester else friendship.user_id1
        other_user = Users.query.get(other_user_id)

        if is_pending:
            if is_requester:
                pending_requests_sent.append((other_user, friendship.id))
            else:
                pending_requests_received.append((other_user, friendship.id))
        else:
            friends.append((other_user, friendship.id))

    return friends, pending_requests_sent, pending_requests_received

### SEARCH ###
def get_reverb_results(query, user, collection):
    """Get search results for Reverb content, e.g. users and collections."""
    query = "%" + query + "%"
    results = []

    if user:
        user_results = db.session.query(Users).filter(Users.username.like(query)).all()

        for row in user_results:
            # Placeholder
            placeholder = "/static/assets/app/user.png"
            content_item = ContentItem(content_id=row.id,
                                    content_type="user",
                                    name=row.username,
                                    image=placeholder)
            results.append(content_item)

    if collection:
        user_results = db.session.query(Collections).filter(Collections.name.like(query)).all()

        for row in user_results:
            content_item = ContentItem(content_id=row.id,
                                    content_type="collection",
                                    name=row.name,
                                    image=row.image,
                                    artists=[row.user.username])
            results.append(content_item)

    return results

### REVIEWS ###
def post_review(user_id, content_type, content_id, rating, text):
    """Post review or update review if already exists"""
    existing_review = db.session.query(Reviews).filter(
        and_(
            Reviews.user_id == user_id,
            Reviews.content_type == content_type,
            Reviews.content_id == content_id
        )
    ).first()

    if existing_review is None:
        review = Reviews(user_id=user_id,
                         content_type=content_type,
                         content_id=content_id,
                         rating=rating,
                         text=text)
        db.session.add(review)
    else:
        existing_review.content_type = content_type
        existing_review.rating = rating
        existing_review.text = text

    db.session.commit()

def get_reviews_by_user_id(user_id):
    """Get reviews by user id"""
    reviews = db.session.query(Reviews).filter(Reviews.user_id == user_id).all()

    content = { "tracks": [], "albums": [] }

    reviews_by_type = { "tracks": [], "albums": [] }

    for review in reviews:
        if review.content_type == "track":
            content["tracks"].append(review.content_id)
            reviews_by_type["tracks"].append(review)
        else:
            content["albums"].append(review.content_id)
            reviews_by_type["albums"].append(review)

    return reviews_by_type, content

def get_reviews_by_content_id(content_type, content_id):
    """Get reviews by content type and id"""
    reviews = db.session.query(Reviews).filter(
        and_(
            Reviews.content_type == content_type,
            Reviews.content_id == content_id
        )
    ).all()

    return reviews

### COLLECTIONS ###
def create_collection(user_id, name, description, image):
    """Add colletion to database"""
    collection = Collections(user_id=user_id, name=name, description=description, image=image)

    db.session.add(collection)
    db.session.commit()

    return collection.id

def add_content_to_collection(collection_id, spotify_id, spotify_type):
    """Add content to collection and create content row"""
    content_id = create_content(spotify_id, spotify_type)

    collection_content = CollectionsContent(collection_id=collection_id,
                                            content_id=content_id)

    content = get_collection_content(collection_id)

    if len(content) == 1:
        db.session.query(Collections).filter(
                    Collections.id == collection_id
                    ).update({"image": content[0].image})

        db.session.commit()

    db.session.add(collection_content)
    db.session.commit()

def create_content(spotify_id, spotify_type):
    """Add content row to table"""
    check = db.session.query(Content).filter(Content.spotify_id == spotify_id).first()
    if check:
        return check.id

    content = Content(spotify_id=spotify_id, spotify_type=spotify_type)

    db.session.add(content)
    db.session.commit()

    return content.id

def get_collections_by_user_id(user_id):
    """Get collections by user id"""
    collections = db.session.query(Collections).filter(Collections.user_id == user_id).all()

    content = []
    for collection in collections:
        content_item = ContentItem(content_id=collection.id,
                                    content_type="collection",
                                    name=collection.name,
                                    artists=[collection.user.username],
                                    image=collection.image)

        content.append(content_item)

    return content

def get_collection_content(collection_id):
    """Get collection content"""
    collection_content = db.session.query(Content).join(
        CollectionsContent, CollectionsContent.content_id == Content.id).filter(
        CollectionsContent.collection_id == collection_id).all()

    content_dict = { "tracks": [], "albums": [] }

    for c in collection_content:
        if c.spotify_type == "track":
            content_dict["tracks"].append(c.spotify_id)
        elif c.spotify_type == "album":
            content_dict["albums"].append(c.spotify_id)

    content = get_content_several_ids(content_dict)

    content_list = []
    for c in content:
        content_item = ContentItem(content_id=c.content_id,
                                    content_type=c.content_type,
                                    name=c.name,
                                    artists=c.artists,
                                    image=c.image)

        content_list.append(content_item)

    return content_list

def get_random_collection():
    """Get random collection"""
    collection = db.session.query(Collections).order_by(func.random()).first()

    return collection

def get_collection_by_id(collection_id):
    """Get collection by collection id"""
    collection = db.session.query(Collections).filter(Collections.id == collection_id).first()

    return collection

def delete_content_from_collection(collection_id, spotify_type, spotify_id):
    """Remove content from collection"""
    try:
        content = db.session.query(Content).join(
            CollectionsContent, CollectionsContent.content_id == Content.id).filter(
            CollectionsContent.collection_id == collection_id).first()

        content_id = db.session.query(Content.id).filter(
            and_(
                Content.spotify_type == spotify_type,
                Content.spotify_id == spotify_id
            )
        ).first()[0]

        db.session.query(CollectionsContent).filter(
            CollectionsContent.collection_id == collection_id,
            CollectionsContent.content_id == content_id
        ).delete()

        db.session.commit()

        # if the content being deleted is the first content item
        if content.id == content_id:
            # get first content item after deletion
            content = db.session.query(Content).join(
                CollectionsContent, CollectionsContent.content_id == Content.id).filter(
                CollectionsContent.collection_id == collection_id).first()

            if content:
                image = get_content_image(content.spotify_type, content.spotify_id)

                db.session.query(Collections).filter(
                    Collections.id == collection_id
                    ).update({"image": image})

                db.session.commit()
    except Exception as e:
        # if something went wrong in deletion, rollback
        db.session.rollback()
        raise e

def delete_collection(collection_id):
    """Delete collection. Deletes rows from contentcollection and collection tables."""
    try:
        # delete rows associated with collection_id
        db.session.query(CollectionsContent).filter(
            CollectionsContent.collection_id == collection_id
        ).delete()

        # delete the collection
        db.session.query(Collections).filter(
            Collections.id == collection_id
        ).delete()

        db.session.commit()
    except Exception as e:
        # if something went wrong in deletion, rollback
        db.session.rollback()
        raise e

### MOST REVIEWED CONTENT ###
def get_most_reviewed_content(user_id=None):
    """Get most reviewed track and album, optionally for a specific user."""
    top_content = {"tracks": [], "albums": []}

    query_filter = [Reviews.content_type == "track"]
    if user_id:
        query_filter.append(Reviews.user_id == user_id)

    track = db.session.query(Reviews.content_id).filter(*query_filter).group_by(
        Reviews.content_id).order_by(func.count(
        Reviews.id).desc()).first()

    track = track[0] if track else ""
    top_content["tracks"].append(track)

    query_filter = [Reviews.content_type == "album"]
    if user_id:
        query_filter.append(Reviews.user_id == user_id)

    album = db.session.query(Reviews.content_id).filter(*query_filter).group_by(
        Reviews.content_id).order_by(func.count(
        Reviews.id).desc()).first()

    album = album[0] if album else ""
    top_content["albums"].append(album)

    content = get_content_several_ids(top_content)

    return content

### JOURNAL ENTRIES ###
def post_journal_entry(user_id, content_id, text, content_type):
    """Post journal entry or update if already exists"""
    existing_entry = db.session.query(JournalEntry).filter(
        and_(
            JournalEntry.user_id == user_id,
            JournalEntry.content_id == content_id
        )
    ).first()

    if existing_entry is None:
        # No existing entry, create a new one
        entry = JournalEntry(user_id=user_id,
                                content_id=content_id,
                                text=text,
                                content_type=content_type)
        db.session.add(entry)
    else:
        # Existing entry found, update it
        existing_entry.text = text
        existing_entry.content_type = content_type  # Update this if needed
    db.session.commit()
    return "Entry added successfully"

def get_journal_entries_by_user_and_content(user_id, content_id):
    """Get journal entries by user id and content id"""
    entries = db.session.query(JournalEntry).filter(
        and_(
            JournalEntry.user_id == user_id,
            JournalEntry.content_id == content_id
        )
    ).all()
    return entries

def get_journal_entries_by_user(user_id):
    """Get journal entries by user id"""
    entries = db.session.query(JournalEntry).filter(JournalEntry.user_id == user_id).all()

    content = { "tracks": [], "albums": [] }

    ordered_entries = []

    for entry in entries:
        if entry.content_type == "track":
            content["tracks"].append(entry.content_id)
            ordered_entries.append(entry)
        elif entry.content_type == "album":
            content["albums"].append(entry.content_id)
            ordered_entries.append(entry)

    return ordered_entries, content

def set_favorite_content(user_id, content_type, content_id):
    """Set favorite content for the specified user id and content type."""
    user = Users.query.get(user_id)

    if user:
        if content_type == "track":
            user.favorite_track = content_id

        elif content_type == "album":
            user.favorite_album = content_id

        db.session.commit()

def get_favorite_content(user_id, content_type):
    """Get currently set favorite content for the specified user id and content type."""
    user = Users.query.get(user_id)

    if user:
        content_id = None

        if content_type == "track":
            content_id = user.favorite_track

        elif content_type == "album":
            content_id = user.favorite_album

        return content_id

    return None

def delete_entry(user_id, content_id):
    """Delete journal entry by user id and content id"""
    entry = db.session.query(JournalEntry).filter(
        and_(
            JournalEntry.user_id == user_id,
            JournalEntry.content_id == content_id
        )
    ).first()

    if entry:
        db.session.delete(entry)
        db.session.commit()
    else:
        # Handle the case where no entry was found
        print(f"No entry found for user_id {user_id} and content_id {content_id}")

def delete_review(user_id, content_id):
    """Delete review by user id and content id"""
    review = db.session.query(Reviews).filter(
        and_(
            Reviews.user_id == user_id,
            Reviews.content_id == content_id
        )
    ).first()

    if review:
        db.session.delete(review)
        db.session.commit()
    else:
        # Handle the case where no entry was found
        print(f"No review found for user_id {user_id} and content_id {content_id}")

def edit_entry(user_id, content_id, text):
    """Edit journal entry by user id and content id"""
    entry = db.session.query(JournalEntry).filter(
        and_(
            JournalEntry.user_id == user_id,
            JournalEntry.content_id == content_id
        )
    ).first()

    entry.text = text
    db.session.commit()

def get_number_of_reviews_by_user(user_id):
    """Get number of reviews by user id"""
    reviews = db.session.query(Reviews).filter(Reviews.user_id == user_id).all()
    return len(reviews)

def get_friend_count(user_id):
    """Get number of friends by user id"""
    friends = db.session.query(Friendships).filter(
        and_(
            (Friendships.user_id1 == user_id) | (Friendships.user_id2 == user_id),
            Friendships.status == "accepted"
        )
    ).all()
    return len(friends)

def get_random_friend(user_id):
    """Get random friend by user id"""
    friends = db.session.query(Friendships).filter(
        and_(
            (Friendships.user_id1 == user_id) | (Friendships.user_id2 == user_id),
            Friendships.status == "accepted"
        )
    ).all()

    friend = random.choice(friends) if friends else None

    if friend:
        friend_id = friend.user_id2 if str(friend.user_id1) == user_id else friend.user_id1
        friend = get_user_by_id(friend_id)

    return friend

def get_random_user(user_id):
    """Get a random user not with the specified user id."""
    user = db.session.query(Users).filter(Users.id != user_id).order_by(func.random()).first()

    return user
