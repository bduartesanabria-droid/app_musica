from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length


class ProfileForm(FlaskForm):
    first_name = StringField("Nombre",    validators=[DataRequired(), Length(max=60)])
    last_name  = StringField("Apellido",  validators=[DataRequired(), Length(max=60)])
    bio        = TextAreaField("Biografía", validators=[Length(max=500)])
