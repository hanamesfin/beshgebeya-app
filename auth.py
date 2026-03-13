import os
from flask import Blueprint, redirect, url_for, session, flash, current_app
from authlib.integrations.flask_client import OAuth
from werkzeug.routing import BuildError

auth_bp = Blueprint("auth", __name__)

oauth = OAuth()

google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)

# ---------------------------
# Google Login
# ---------------------------
@auth_bp.route("/login/google")
def login_google():

    if not os.environ.get("GOOGLE_CLIENT_ID") or not os.environ.get("GOOGLE_CLIENT_SECRET"):
        flash("Google OAuth is not configured correctly.", "error")
        return redirect(url_for("login"))

    # Generate correct redirect URI: https for production, http for local
    is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RENDER') == 'true'
    scheme = "https" if is_production else "http"
    redirect_uri = url_for("auth.google_callback", _external=True, _scheme=scheme)

    # Normalize local redirect URI to 'localhost' to match Google Console typical settings
    if not is_production:
        redirect_uri = redirect_uri.replace("127.0.0.1", "localhost")

    current_app.logger.info(f"[OAuth] Redirect URI -> {redirect_uri}")

    return google.authorize_redirect(redirect_uri)


# ---------------------------
# Google Callback
# ---------------------------
@auth_bp.route("/auth/callback")
def google_callback():

    from app import db, User, Branch

    try:
        token = google.authorize_access_token()

        # Safely fetch user profile
        user_info = token.get("userinfo")
        if not user_info:
            resp = google.get("userinfo")
            user_info = resp.json()

        social_id = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("picture")

    except Exception as e:

        current_app.logger.error(f"[OAuth ERROR] {str(e)}")
        flash("Google authentication failed.", "error")

        return redirect(url_for("login"))

    if not social_id:
        flash("Failed to retrieve Google account information.", "error")
        return redirect(url_for("login"))

    # ---------------------------
    # Find Existing User
    # ---------------------------
    user = User.query.filter_by(google_id=social_id).first()

    if not user and email:
        user = User.query.filter_by(email=email).first()
        if user:
            user.google_id = social_id
            db.session.commit()

    # ---------------------------
    # Create New User
    # ---------------------------
    if not user:

        base_username = email.split("@")[0] if email else f"google_{social_id[:8]}"
        username = base_username
        count = 1

        while User.query.filter_by(username=username).first():
            username = f"{base_username}_{count}"
            count += 1

        branch = Branch.query.first()

        user = User(
            username=username,
            email=email,
            name=name or username,
            branch_id=branch.id if branch else 1,
            is_admin=(User.query.count() == 0),
            is_approved=(User.query.count() == 0)
        )

        user.google_id = social_id

        db.session.add(user)
        db.session.commit()

    # ---------------------------
    # Access Control
    # ---------------------------
    if user.is_denied:
        flash("Your account has been denied access.", "error")
        return redirect(url_for("login"))

    if not user.is_approved:
        flash("Your account is awaiting admin approval.", "warning")
        return redirect(url_for("login"))

    # ---------------------------
    # Login User
    # ---------------------------
    session.clear()

    session["user_id"] = user.id
    session["username"] = user.username
    session["is_admin"] = user.is_admin

    session["user"] = {
        "name": user.name,
        "email": user.email,
        "picture": picture
    }

    flash("Successfully logged in with Google!", "success")

    landing_page = getattr(user, "landing_page", None) or "dashboard"

    try:
        return redirect(url_for(landing_page))
    except (BuildError, AttributeError):
        return redirect(url_for("dashboard"))