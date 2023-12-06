"""
form_utils.py

Utilities for forms, including profile edting, collection management,
and password strength check functions.
"""

import re

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length

class EditProfileForm(FlaskForm):
    """Form for editing profile information."""
    bio = TextAreaField('Bio', validators=[Length(min=0, max=140)])
    favorite_genre = TextAreaField('Favorite genre', validators=[Length(min=0, max=30)])
    submit = SubmitField('Submit')

class AddToCollectionForm(FlaskForm):
    """Form for adding content to a collection."""
    dropdown = SelectField("Add to existing collection", choices=[])
    submit = SubmitField("Add to collection")

class CreateCollectionForm(FlaskForm):
    """Form for creating collections."""
    name = StringField("Name", validators=[Length(min=0, max=50)])
    description = TextAreaField("Description", validators=[Length(min=0, max=100)])
    submit = SubmitField("Create and add content")

class DeleteCollectionForm(FlaskForm):
    """Form for deleting collections."""
    submit = SubmitField("Delete collection")

def password_strength_check(password):
    """
    Checks the strength of the given password, returns valid boolean, dictionary of errors
    A password is considered strong if at least 10 characters long and contains at least
    1 digit, 1 symbol, 1 uppercase letter, and 1 lowercase letter
    """
    # Length
    length_error = len(password) < 10

    # Content: digits, uppercase, lowercase, symbol
    digit_error = re.search(r"\d", password) is None
    uppercase_error = re.search(r"[A-Z]", password) is None
    lowercase_error = re.search(r"[a-z]", password) is None
    symbol_error = re.search(r"\W", password) is None

    # Overall check
    valid = not (length_error or digit_error or uppercase_error or lowercase_error or symbol_error)

    # Errors
    errors = {
        'length_error' : "Must be at least 10 characters" if length_error else None,
        'digit_error' : "Must contain at least 1 digit" if digit_error else None,
        'uppercase_error' : "Must contain at least 1 uppercase letter" if uppercase_error else None,
        'lowercase_error' : "Must contain at least 1 lowercase letter" if lowercase_error else None,
        'symbol_error' : "Must contain at least 1 symbol" if symbol_error else None,
    }

    return valid, errors
