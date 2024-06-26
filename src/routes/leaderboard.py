from flask_restx import Namespace, Resource, fields
from sqlalchemy import select
from sqlalchemy.orm import attributes

from middleware import api_key_required
from models.leaderboard import Leaderboard as LeaderboardModel
from models.level import Level as LevelModel
from db import db

api = Namespace('Leaderboard', description='Game Leaderboard Management')
leaderboard_item = api.model('LeaderboardLevelItem', {
    'ProfileName': fields.String(
        required=True, description='Player\'s profile name'),
    'Value': fields.Integer(required=True, description='Point or time value'),
})
leaderboard_model = api.model('LeaderboardLevel', {
    'LevelId': fields.Integer(
        description='Unique ID of the level, should exist in Level'),
    'Boards': fields.List(
        fields.List(
            fields.List(
                fields.Nested(leaderboard_item), max_items=10,
            ),
            min_items=2, max_items=2,
        ),
        required=True,
        min_items=2, max_items=2,
        description='Boards[GameType][GameMode][i] = LeaderboardItem')
})
leaderboard_response_model = api.inherit(
    'LeaderboardLevelResponse', leaderboard_item, {
        'Rank': fields.Integer(
            description='Rank of the added item', required=True),
    },
)
leaderboard_request_model = api.model('LeaderboardLevelRequest', {
    'GameType': fields.Integer(description='Game type, 0: single, 1: coop',
                               minimum=0, maximum=1,
                               required=True),
    'GameMode': fields.Integer(description='Game mode, 0: point, 1: time',
                               minimum=0, maximum=1,
                               required=True),
    'ProfileName': fields.String(description='In-game profile name',
                                 min_length=3, max_length=32,
                                 required=True),
    'Value': fields.Integer(description='Point value or time in milliseconds',
                            required=True)
})
sort_on_mode = {
    0: lambda lastVal, newVal: lastVal <= newVal,  # point, ascending
    1: lambda lastVal, newVal: lastVal >= newVal,  # time, descending
}


@api.route('/level/<int:id>')
@api.param('id', 'Level identifier')
@api.response(404, 'Level doesn\'t found')
class LevelLeaderboard(Resource):
    @api.marshal_with(leaderboard_model)
    def get(self, id):
        '''Get leaderboard of a level'''
        level = db.session.scalar(
            select(LevelModel.Id).where(LevelModel.Id == id))
        if level is None:
            api.abort(404, f"Level {id} not found")
        d = LeaderboardModel.query.get(id)
        if d is None:
            d = LeaderboardModel.default(id)
        return d

    @api.expect(leaderboard_request_model)
    @api.marshal_with(leaderboard_response_model)
    @api.response(204, 'Not in the top 10')
    def post(self, id):
        '''Add a new leaderboard item to a level, if needed'''
        level = db.session.scalar(
            select(LevelModel.Id).where(LevelModel.Id == id))
        if level is None:
            api.abort(404, f"Level {id} not found")

        leaderboard = LeaderboardModel.query.get(id)
        is_new = False
        if leaderboard is None:
            leaderboard = LeaderboardModel.default(id)
            is_new = True

        request_data = api.payload
        game_type = request_data['GameType']
        game_mode = request_data['GameMode']
        profile_name = request_data['ProfileName']
        value = request_data['Value']

        # Check where it belongs to the leaderboard (if at all)
        boards = leaderboard.Boards[game_type][game_mode]
        is_found = False
        record_idx = -1
        for idx, item in enumerate(boards):
            record_idx = idx
            if sort_on_mode[game_mode](item['Value'], value):
                is_found = True
                break
        if not is_found:
            if record_idx >= 9:  # no space left
                return {'message': 'not in the top 10!'}, 204
            record_idx += 1
        # Insert new LeaderboardItem to record_idx
        boards.insert(record_idx, {
            'ProfileName': profile_name, 'Value': value})
        if len(boards) > 10:
            boards.pop()  # remove the last item if > 10
        if is_new:
            db.session.add(leaderboard)
        else:
            attributes.flag_modified(leaderboard, 'Boards')
        db.session.commit()
        return {
            'Rank': record_idx + 1,
            **boards[record_idx],
        }, 200

    @api.doc('delete_leaderboard', security='apikey')
    @api.response(204, 'Leaderboard successfully deleted')
    @api_key_required
    def delete(self, id):
        '''Delete leaderboard of a level'''
        d = LeaderboardModel.query.get(id)
        if d is None:
            api.abort(404, f"Level {id} leaderboard not found")
        db.session.delete(d)
        db.session.commit()
        return 'Leaderboard successfully deleted!', 204
