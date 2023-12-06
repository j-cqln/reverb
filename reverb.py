"""
reverb.py

Main app that defines all routes.
"""

#!/usr/bin/env python

import os

from flask import Flask, request, make_response, redirect, url_for, render_template,\
    send_from_directory, flash, get_flashed_messages, jsonify

from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# To-do: move direct handling of db into database.py
from utils.models import Users, Friendships, ReviewContent, JournalEntryContent

from utils.database import db_init, create_user, update_profile, create_friendship,\
    accept_friendship, reject_friendship, remove_friendship, is_friend, get_friends,\
    get_user_by_id, get_reverb_results, get_collections_by_user_id, get_random_friend,\
    get_random_user, get_most_reviewed_content

from utils.database import create_collection, add_content_to_collection,\
    get_collection_content, delete_content_from_collection,\
    get_random_collection, get_collection_by_id, delete_collection,\
    set_favorite_content, get_favorite_content

from utils.database import get_reviews_by_user_id, get_reviews_by_content_id, post_review,\
    get_friend_count, get_number_of_reviews_by_user

from utils.database import post_journal_entry, get_journal_entries_by_user_and_content,\
    get_journal_entries_by_user, edit_entry, delete_entry, delete_review

from utils.spotify import get_spotify_results, get_content_info,\
    get_content_several_ids, get_random_content

from utils.form_utils import EditProfileForm, AddToCollectionForm,\
    CreateCollectionForm, DeleteCollectionForm, password_strength_check

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, template_folder="html")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "reverb.db")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

db_init(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    """Load specified user."""
    return Users.query.get(int(user_id))

@app.route("/", methods=["GET"])
def index():
    """Index (front page) page content."""
    html = render_template("index.html")
    response = make_response(html)
    return response

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register/sign up page content."""
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        check_password = request.form.get("check_password")

        # If the username or is nonalphanumeric, flash an error message
        if not username.isalnum():
            flash("Username must be alphanumeric.")
            return redirect(url_for("register"))

        if password != check_password:
            flash("Passwords do not match.")
            return redirect(url_for("register"))

        if username == "" or len(username) > 20:
            flash("Username must be between 1 and 20 characters.")
            return redirect(url_for("register"))

        # Check username exists
        existing_user = Users.query.filter_by(username=username).first()

        if existing_user:
            flash("Username already exists!")
            return redirect(url_for("register"))

        # Check password validity
        valid, errors = password_strength_check(password)

        if valid:
            create_user(username, password)
            flash("User successfully registered!")

            return redirect(url_for("login"))

        else:
            for error in errors.values():
                if error is not None:
                    flash(error)

            return redirect(url_for("register"))

    html = render_template("register.html")
    response = make_response(html)
    return response

@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page content."""
    # Redirect to home page if logged in
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    # Login with password check
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = Users.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get("next")

            return redirect(next_page) if next_page else redirect(url_for("search"))

        flash("Invalid username or password.")

    html = render_template("login.html")
    response = make_response(html)

    return response

@app.route("/home", methods=["GET"])
@login_required
def home():
    """Reverb home page (user feed) content."""
    current_user_id = current_user.get_id()
    current_user_obj = get_user_by_id(current_user_id)

    random_user = get_random_user(current_user_id)

    # Random top Spotify content
    slides = get_random_content("track", 5)
    album = get_random_content("album", 1)[0]
    collection = get_random_collection()

    # Top Reverb content
    top_content = get_most_reviewed_content()

    # Top friends content
    friends = get_friend_count(current_user_id)
    friend_content = []

    if friends > 0:
        the_friend = get_random_friend(current_user_id)
        friend_content = get_most_reviewed_content(the_friend.get_id())

    html = render_template("home.html",
                           current_user=current_user_obj,
                           random_user=random_user,
                           slides=slides,
                           collection=collection,
                           album=album,
                           results=top_content,
                           friends=friends,
                           friend_content=friend_content)

    response = make_response(html)

    return response

@app.route("/user/", methods=["GET"])
def display_profiles():
    """Profile"""
    return not_found("No profile requested.")

@app.route("/user/<int:user_id>", methods=["GET"])
@login_required
def display_profile(user_id):
    """Display user profile"""
    current_user_id = current_user.get_id()
    current_user_obj = get_user_by_id(current_user_id)

    random_user = get_random_user(current_user_id)

    user = get_user_by_id(user_id)

    if not user:
        return not_found("User not found.")

    # User reviews
    reviews, content = get_reviews_by_user_id(user_id)

    # get list of reviews in same order as content
    reviews_list = []
    for r in reviews["tracks"]:
        reviews_list.append(r)

    for r in reviews["albums"]:
        reviews_list.append(r)

    content_items = get_content_several_ids(content)

    friends, pending_sent, pending_received = get_friends(user_id)

    reviews_content = []
    count = len(reviews_list)

    for i in range(count):
        r = reviews_list[i]
        c = content_items[i]

        review = ReviewContent(c.image, c.name, c.artists,
                                c.content_type, c.content_id,
                                r.rating, r.text)
        reviews_content.append(review)

    # User collections
    collections = get_collections_by_user_id(user_id)

    # Follows the same pattern as above
    journal_entries, journal_content = get_journal_entries_by_user(user_id)
    journal_content_items= get_content_several_ids(journal_content)

    journal_entries_content =[]
    count = len(journal_entries)

    friends_count = get_friend_count(user_id)
    reviews_count = get_number_of_reviews_by_user(user_id)

    for i in range(count):
        r = journal_entries[i]
        c = journal_content_items[i]
        entry = JournalEntryContent(c.image, c.name, c.content_type, c.content_id, r.text)
        journal_entries_content.append(entry)

    html = render_template("profile.html",
                            current_user=current_user_obj,
                            random_user=random_user,
                            user=user,
                            reviews=reviews_content,
                            results=collections,
                            journal_entries=journal_entries_content,
                            friends=friends,
                            pending_friends_sent=pending_sent,
                            pending_friends_received=pending_received,
                            friends_count=friends_count,
                            reviews_count=reviews_count)

    response = make_response(html)

    return response

@app.route("/edit_profile/<int:user_id>", methods=["GET", "POST"])
@login_required
def edit_profile(user_id):
    """Profile editing page cteont."""
    current_user_id = current_user.get_id()
    current_user_obj = get_user_by_id(current_user_id)

    random_user = get_random_user(current_user_id)

    user = get_user_by_id(user_id)

    # Redirect back since should not be able to edit other user's profiles
    if current_user_obj.id != user_id:
        return redirect(url_for("display_profile", user_id=user_id))

    form = EditProfileForm(bio=current_user.bio, favorite_genre=current_user.favorite_genre)

    # User favorite track/album
    track = None

    if user.favorite_track:
        track = get_content_info("track", user.favorite_track)

    album = None

    if user.favorite_album:
        album = get_content_info("album", user.favorite_album)

    results = [result for result in [track, album] if result]

    # Update changes
    if form.validate_on_submit():
        update_profile(user_id, form.bio.data, form.favorite_genre.data)
        flash("Your profile changes have been saved.")
        return redirect(url_for("display_profile", user_id=user_id))

    elif request.method == "GET":
        form.bio.data = current_user.bio

    return render_template("edit_profile.html",
                           current_user=current_user_obj,
                           random_user=random_user,
                           user=user,
                           results=results,
                           form=form)

@app.route("/send_friend_request/<int:requested_id>", methods=["POST", "GET"])
@login_required
def send_friend_request(requested_id):
    """Send a friend request"""
    requester_id = current_user.id
    requested_user = get_user_by_id(requested_id)

    if requested_id == current_user.id:
        flash("Invalid username or password.")
        return redirect(url_for("display_profile", user_id=requested_id))

    # Check if already friend or pending friend request exists
    accepted, requested = is_friend(requester_id, requested_id)

    if accepted:
        flash(f"Friend {requested_user.username} already exists!")
        return redirect(url_for("display_profile", user_id=requested_id))

    if requested:
        flash(f"Friend request {requested_user.username} already exists!")
        return redirect(url_for("display_profile", user_id=requested_id))

    # Only add friend if no existing friend/request
    create_friendship(requester_id, requested_id)
    flash("Friend request sent!")

    return redirect(url_for("display_profile", user_id=requested_id))

@app.route("/accept_friend_request/<int:request_id>", methods=["POST"])
@login_required
def accept_friend_request(request_id):
    """Route for accepting friend requests"""
    accept_friendship(request_id)

    return redirect(url_for("display_profile", user_id=current_user.id))

@app.route("/reject_friend_request/<int:request_id>", methods=["POST"])
@login_required
def reject_friend_request(request_id):
    """Route for rejecting friend requests"""
    reject_friendship(request_id)

    return redirect(url_for("display_profile", user_id=current_user.id))

@app.route("/remove_friend/<int:request_id>", methods=["POST"])
@login_required
def remove_friend(request_id):
    """Deleting friends"""
    remove_friendship(request_id)

    return redirect(url_for("display_profile", user_id=current_user.id))

@app.route("/submit_review/<content_type>/<content_id>", methods=["POST"])
@login_required
def submit_review(content_type, content_id):
    """Post review to database"""
    current_user_id = current_user.get_id()

    rating = request.form["rating"]
    text = request.form["form-text"]

    post_review(current_user_id, content_type, content_id, rating, text)

    return redirect(url_for("content", content_type=content_type, content_id=content_id))

def get_search_results():
    """Helper function for getting search results."""
    # Content types
    filters = {"track": None, "album": None, "user": None, "collection": None}

    for key in filters:
        filters[key] = request.args.get(key)

    # Get queries for each searchable content type
    query = request.args.get("query")
    if not query:
        query = ""

    # Retrieve Spotify & Reverb results
    results = ""
    if query:
        spotify_results = get_spotify_results(query, filters["track"], filters["album"])
        reverb_results = get_reverb_results(query, filters["user"], filters["collection"])

        results = spotify_results + reverb_results

    # Filter results based on selected content types
    filtered_results = []

    for result in results:
        if filters[result.content_type] == "true":
            filtered_results.append(result)

    return query, filtered_results

@app.route("/search", methods=["GET"])
@login_required
def search():
    """Search page content for the Reverb application."""
    current_user_id = current_user.get_id()
    current_user_obj = get_user_by_id(current_user_id)

    random_user = get_random_user(current_user_id)

    query, results = get_search_results()

    html = render_template("search.html",
                           query=query,
                           current_user=current_user_obj,
                           random_user=random_user,
                           results=results)

    response = make_response(html)

    return response

@app.route("/search_results", methods=["GET"])
@login_required
def search_results():
    """Search results content for the Reverb application."""
    query, results = get_search_results()

    html = render_template("search_results.html",
                           query=query,
                           results=results)

    response = make_response(html)

    return response

@app.route("/content/<content_type>/<content_id>", methods=["GET", "POST"])
@login_required
def content(content_type, content_id):
    """Display corresponding content page after clicking search result"""
    current_user_id = current_user.get_id()
    current_user_obj = get_user_by_id(current_user_id)

    random_user = get_random_user(current_user_id)

    # Content based on type
    # User
    if content_type == "user":
        user = get_user_by_id(content_id)
        if not user:
            return not_found(f"{content_type} with id {content_id} does not exist")

        return redirect(url_for("display_profile", user_id=content_id))

    # Music
    elif content_type in ["track", "album"]:
        content_info = get_content_info(content_type, content_id)

        if not content_info:
            return not_found(f"{content_type} with id {content_id} does not exist")

        # get existing colletions to populate dropdown menu
        collections = get_collections_by_user_id(current_user_id)

        addform = AddToCollectionForm()
        addform.dropdown.choices = [(c.content_id, c.name) for c in collections]

        createform = CreateCollectionForm()

        if addform.validate_on_submit():
            collection_id = addform.dropdown.data

            add_content_to_collection(collection_id, content_id, content_type)

        elif createform.validate_on_submit():
            name = createform.name.data
            description = createform.description.data

            collection_id = create_collection(current_user_id,
                                                name,
                                                description,
                                                content_info.image)
            add_content_to_collection(collection_id, content_id, content_type)

            return redirect(url_for("content", content_type=content_type, content_id=content_id))

        reviews = get_reviews_by_content_id(content_type, content_id)

        html = render_template("content.html",
                            content_type=content_type,
                            content_id=content_id,
                            current_user=current_user_obj,
                            random_user=random_user,
                            results=[content_info],
                            addform=addform,
                            createform=createform,
                            collections=collections,
                            reviews=reviews)

    # Collection
    elif content_type == "collection":
        collection = get_collection_by_id(content_id)
        if collection:
            collection_content = get_collection_content(content_id)
        else:
            return not_found("Collection not found.")

        deleteform = DeleteCollectionForm()

        if deleteform.validate_on_submit():
            delete_collection(content_id)
            return redirect(url_for("display_profile", user_id=current_user_id))

        html = render_template("collections.html",
                               content_type=content_type,
                               current_user_id=int(current_user_id),
                               random_user=random_user,
                               collection=collection,
                               deleteform=deleteform,
                               results=collection_content)

    # Error
    else:
        return not_found("Invalid content type. Please ensure URL contains only 'track' or 'album' after '/content/'")

    response = make_response(html)
    return response

@app.route("/delete_from_collection", methods=["POST"])
@login_required
def delete_from_collection():
    """Delete a song or album from the collection"""
    collection_id = request.form["collection_id"]
    spotify_id = request.form["spotify_id"]
    spotify_type = request.form["spotify_type"]

    delete_content_from_collection(collection_id, spotify_type, spotify_id)

    return redirect(url_for("content", content_type="collection", content_id=collection_id))

@app.route("/update_favorite", methods=["POST"])
@login_required
def update_favorite():
    """Updating favorite content."""
    current_user_id = current_user.get_id()

    content_id = request.form["content_id"]
    content_type = request.form["content_type"]

    # Toggle favorite/unfavorite based on user's existing selection
    if get_favorite_content(current_user_id, content_type) == content_id:
        set_favorite_content(current_user_id, content_type, None)
    else:
        set_favorite_content(current_user_id, content_type, content_id)

    return redirect(url_for("content", content_type=content_type, content_id=content_id))

@app.route("/get_journal_entries/<content_id>", methods=["GET"])
@login_required
def get_journal_entries(content_id):
    """Get journal entries for a specific content item."""
    current_user_id = current_user.get_id()
    entries = get_journal_entries_by_user_and_content(current_user_id, content_id)
    return jsonify([entry.to_dict() for entry in entries])  # Convert entries to a dictionary format

@app.route("/add_journal_entry", methods=["POST"])
@login_required
def add_journal_entry():
    """Add a journal entry for a specific content item."""
    # Get form data
    current_user_id = current_user.get_id()
    content_id = request.form["content_id"]
    content_type = request.form["content_type"]
    entry_text = request.form["entry_text"]

    # Logic to add the journal entry
    post_journal_entry(current_user_id, content_id, entry_text, content_type)
    return redirect(url_for("content", content_id=content_id, content_type=content_type))

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    """Route for logging out"""
    logout_user()
    return redirect(url_for("index"))

@app.errorhandler(404)
@login_required
def not_found(error):
    """Error page content."""
    current_user_id = current_user.get_id()

    random_user = get_random_user(current_user_id)

    return render_template("error.html",
                            current_user_id=current_user_id,
                            random_user=random_user,
                            error_msg=error), 404

@app.route("/edit_journal_entry", methods=["GET", "POST"])
@login_required
def edit_journal_entry():
    """Edit a journal entry for a specific content item."""
    user_id = current_user.get_id()
    content_id = request.form["content_id"]
    content_type = request.form["content_type"]
    entry_text = request.form["entry_text"]

    # Logic to update the journal entry
    edit_entry(user_id, content_id, entry_text)
    flash("Journal entry updated.")
    return redirect(url_for("content", content_id=content_id, content_type=content_type))

@app.route("/delete_journal_entry", methods=["POST"])
@login_required
def delete_journal_entry():
    """Delete a journal entry for a specific content item."""
    user_id = current_user.get_id()
    content_id = request.form["content_id"]
    content_type = request.form["content_type"]

    # Logic to delete the journal entry
    delete_entry(user_id, content_id)
    flash("Journal entry deleted.")
    return redirect(url_for("content", content_id=content_id, content_type=content_type))

@app.route("/delete_review_card", methods=["POST"])
@login_required
def delete_review_card():
    """Delete a review card for a specific content item."""
    user_id = current_user.get_id()
    content_id = request.form["content_id"]
    content_type = request.form["content_type"]

    # Logic to delete the review card
    delete_review(user_id, content_id)
    return redirect(url_for("content", content_id=content_id, content_type=content_type))
