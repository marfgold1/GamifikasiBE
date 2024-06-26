# import json
from flask import Flask
from flask_restx import Api
from db import init_db
from routes.level import api as level_api
from routes.stats import api as stat_api
from routes.leaderboard import api as leaderboard_api

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-KEY'
    }
}

app = Flask(__name__)
# app.config['SERVER_NAME'] = '127.0.0.1:5000'
# app.config['APPLICATION_ROOT'] = '/'
# app.config['PREFERRED_URL_SCHEME'] = 'http'
app.config['RESTX_VALIDATE'] = True
app.config['RESTX_MASK_SWAGGER'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
api = Api(app,
          version='1.0',
          title='Gamification API',
          description='API for game levels and leaderboards',
          authorizations=authorizations)

# Register namespaces
api.add_namespace(level_api, path='/level')
api.add_namespace(stat_api, path='/stats')
api.add_namespace(leaderboard_api, path='/leaderboard')

# Initialize database
init_db(app)

# with app.app_context():
#     urlvars = False  # Build query strings in URLs
#     swagger = True  # Export Swagger specifications
#     data = api.as_postman(urlvars=urlvars, swagger=swagger)
#     print(json.dumps(data))

if __name__ == '__main__':
    app.run(debug=True)
