from flask_restx import Namespace, Resource, fields
from sqlalchemy import select
from middleware import api_key_required
from models.level import Level as LevelModel
from db import db

api = Namespace('Levels', description='Level Management')
level_id = api.model('LevelId', {
    'Id': fields.Integer(readOnly=True,
                         description='The unique identifier of a level'),
})
level_short = api.model('LevelShort', {
    'Name': fields.String(required=True, description='Name of the level',
                          maxLength=50),
    'Summary': fields.String(required=True,
                             description='Summary of the level',
                             maxLength=100),
    'Thresholds': fields.List(
        fields.List(
            fields.List(fields.Integer, min_items=3, max_items=3),
            min_items=2, max_items=2,
        ),
        min_items=2, max_items=2,
        required=True,
        description='Thresholds[GameType][GameMode][i], '
        'where GameType=0..1, GameMode=0..1, and i=0..2'),
})
level_full = api.inherit('LevelFull', level_short, {
    'SystemDescription': fields.String(
        description='System description of the level', required=True),
    'LevelSchema': fields.String(
        description='Data schema of the level', required=True),
})

level_list = api.inherit('LevelList', level_id, level_short)
level_detail = api.inherit('LevelDetail', level_id, level_short, level_full)


@api.route('/')
class LevelList(Resource):
    @api.doc('list_levels')
    @api.marshal_list_with(level_list)
    def get(self):
        '''List all levels'''
        return db.session.execute(select(
            LevelModel.Id, LevelModel.Name,
            LevelModel.Summary, LevelModel.Thresholds)).all()

    @api.doc('create_level', security='apikey')
    @api.expect(level_full)
    @api.marshal_with(level_detail, code=201)
    @api_key_required
    def post(self):
        '''Create a new level'''
        d = api.payload
        if 'Id' in d:
            api.abort(400, message='Id should not be provided')
        new_level = LevelModel(**d)
        db.session.add(new_level)
        db.session.commit()
        return new_level, 201


@api.route('/<int:id>')
@api.response(404, 'Level doesn\'t exist')
class Level(Resource):
    @api.doc('get_level')
    @api.marshal_with(level_detail)
    def get(self, id):
        '''Fetch a level given its id'''
        level = LevelModel.query.get(id)
        if level is None:
            api.abort(404, message=f"Level {id} doesn't exist")
        return level

    @api.doc('delete_level', security='apikey')
    @api.response(204, 'Level successfully deleted')
    @api_key_required
    def delete(self, id):
        '''Delete a level given its id'''
        level = LevelModel.query.get(id)
        if level is None:
            api.abort(404, message=f"Level {id} doesn't exist")
        db.session.delete(level)
        db.session.commit()
        return 'Level successfully deleted!', 204

    @api.doc('update_level', security='apikey')
    @api.expect(level_full)
    @api.response(204, 'Level successfully updated')
    @api_key_required
    def put(self, id):
        '''Update a level given its id'''
        level = LevelModel.query.get(id)
        if level is None:
            api.abort(404, message=f"Level {id} doesn't exist")

        data = api.payload
        for key, value in data.items():
            if key != 'Id' and hasattr(level, key):
                setattr(level, key, value)
        db.session.commit()
        return 'Level successfully updated!', 204
