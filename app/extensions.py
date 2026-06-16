from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db           = SQLAlchemy()
migrate      = Migrate()
login_manager = LoginManager()
bcrypt       = Bcrypt()
mail         = Mail()
csrf         = CSRFProtect()
limiter      = Limiter(key_func=get_remote_address)
