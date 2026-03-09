from flask import Flask, render_template
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from routes.shop_routes import shop_bp
from routes.admin_routes import admin_bp
from routes.marketing_routes import marketing_bp, public_bp
import config

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Register Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(marketing_bp)
app.register_blueprint(public_bp)

if __name__ == '__main__':
    app.run(debug=True)
