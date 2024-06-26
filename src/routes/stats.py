from flask_restx import Namespace, Resource, fields
from sqlalchemy import select
from sqlalchemy.orm import attributes
from middleware import api_key_required
from models.stats import LevelStat as LevelStatModel
from models.level import Level as LevelModel
from db import db

api = Namespace('Statistics', description='Game Statistics Management')
level_stat_model = api.model('LevelStat', {
    'LevelId': fields.Integer(description='Unique ID of the level'),
    'TotalCompleted': fields.List(
        fields.List(fields.Integer,
                    min_items=2, max_items=2),
        description='TotalCompleted[GameType][GameMode]',
        min_items=2, max_items=2
    ),
    'Averages': fields.List(
        fields.List(fields.Float, min_items=2, max_items=2),
        description='Averages[GameType][GameMode]',
        min_items=2, max_items=2,
    ),
    'CountStars': fields.List(
        fields.List(
            fields.List(
                fields.Integer,
                min_items=4, max_items=4,
            ),
            min_items=2, max_items=2,
        ),
        description='CountStars[GameType][GameMode][StarCount]',
        min_items=2, max_items=2,
    ),
})
level_update_stat_model = api.model('LevelUpdateStat', {
    'GameType': fields.Integer(description='Game type, 0: single, 1: coop',
                               minimum=0, maximum=1,
                               required=True),
    'GameMode': fields.Integer(description='Game mode, 0: point, 1: time',
                               minimum=0, maximum=1,
                               required=True),
    'Value': fields.Integer(description='Point or time in milliseconds',
                            required=True)
})
sort_on_mode = {
    0: lambda val, thresh: val >= thresh,  # point, ascending
    1: lambda val, thresh: val <= thresh,  # time, descending
}


@api.route('/level/<int:id>')
@api.response(404, 'Level doesn\'t exist')
@api.param('id', 'Level identifier')
class LevelStats(Resource):
    @api.marshal_with(level_stat_model)
    def get(self, id):
        '''Get statistics of a level'''
        level = db.session.scalar(
            select(LevelModel.Id).where(LevelModel.Id == id))
        if level is None:
            api.abort(404, f"Level {id} not found")
        stat = LevelStatModel.query.get(id)
        if stat is None:
            stat = LevelStatModel.default(id)
        return stat

    @api.expect(level_update_stat_model)
    @api.marshal_with(level_stat_model)
    def post(self, id):
        '''Update statistics of a level'''
        thresh = db.session.scalar(
            select(LevelModel.Thresholds).where(LevelModel.Id == id))
        if thresh is None:
            api.abort(404, f"Level {id} not found")
        level_stat = LevelStatModel.query.get(id)
        is_new = False
        if level_stat is None:
            level_stat = LevelStatModel.default(id)
            is_new = True
        request_data = api.payload
        game_type = request_data['GameType']
        game_mode = request_data['GameMode']
        value = request_data['Value']
        tot = level_stat.TotalCompleted[game_type][game_mode] + 1
        level_stat.TotalCompleted[game_type][game_mode] = tot
        level_stat.Averages[game_type][game_mode] = (
            level_stat.Averages[game_type][game_mode] *
            (tot - 1) + value
        ) / tot

        thresh = thresh[game_type][game_mode]
        for i in range(3, -1, -1):
            if i == 0:
                level_stat.CountStars[game_type][game_mode][0] += 1
            elif sort_on_mode[game_mode](value, thresh[i - 1]):
                level_stat.CountStars[game_type][game_mode][i] += 1
                break

        if is_new:
            db.session.add(level_stat)
        else:
            attributes.flag_modified(level_stat, 'TotalCompleted')
            attributes.flag_modified(level_stat, 'Averages')
            attributes.flag_modified(level_stat, 'CountStars')
        db.session.commit()

        return level_stat

    @api.doc('delete_level_stat', security='apikey')
    @api.response(204, 'Level stat deleted')
    @api_key_required
    def delete(self, id):
        '''Delete statistics of a level'''
        stat = LevelStatModel.query.get(id)
        if stat is None:
            api.abort(404, f"Level {id} stat not found")
        db.session.delete(stat)
        db.session.commit()
        return 'Level stat deleted', 204
