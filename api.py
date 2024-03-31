from flask import jsonify
from flask_restful import abort, Resource
from sql import *
from flask_restful import reqparse

parser_for_post = reqparse.RequestParser()
parser_for_post.add_argument('username', required=True)
parser_for_post.add_argument('email', required=True)
parser_for_post.add_argument('hashed_password', required=True)
parser_for_post.add_argument('access_level', required=True, type=int)
parser_for_post.add_argument('api_key', required=True)

parser_for_get = reqparse.RequestParser()
parser_for_get.add_argument('api_key', required=True)

access_level = {
    'user': [],
    'admin': ['GET'],
    'developer': ['GET', 'DELETE', 'POST', 'PUT'],
}


def abort_if_user_not_found(user_id):
    session = create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404, message=f"User {user_id} not found")


def abort_if_no_access(method, api_key):
    session = create_session()
    asoc = session.query(ApiKeyAsoc).filter(ApiKeyAsoc.key == api_key).first()
    if asoc:
        if method not in access_level[asoc.user.access_level.level]:
            abort(403, message="access denied. You do not have permission")
    else:
        abort(403, message="access denied. Api key is not available")


class UsersResource(Resource):
    def get(self, user_id):
        args = parser_for_get.parse_args()
        abort_if_no_access('GET', args['api_key'])
        abort_if_user_not_found(user_id)
        session = create_session()
        user = session.query(User).get(user_id)
        return jsonify({'user': user.to_dict(
            only=('id', 'username', 'email', 'access', 'modified_date'))})

    def delete(self, user_id):
        args = parser_for_get.parse_args()
        abort_if_no_access('DELETE', args['api_key'])
        abort_if_user_not_found(user_id)
        session = create_session()
        user = session.query(User).get(user_id)
        session.delete(user)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, user_id):
        args = parser_for_post.parse_args()
        abort_if_no_access('PUT', args['api_key'])
        abort_if_user_not_found(user_id)
        session = create_session()
        user = session.query(User).get(user_id)
        user.username=args['username']
        user.email=args['email']
        user.hashed_password=sha256(args['hashed_password'].encode('utf-8')).hexdigest()
        user.access=args['access_level']
        session.merge(user)
        session.commit()
        return jsonify({'user': user.to_dict(
            only=('id', 'username', 'email', 'access', 'modified_date'))})


class UsersListResource(Resource):
    def get(self):
        args = parser_for_get.parse_args()
        abort_if_no_access('GET', args['api_key'])
        session = create_session()
        user = session.query(User).all()
        return jsonify({'users': [item.to_dict(
            only=('id', 'username', 'email', 'access', 'modified_date')) for item in user]})

    def post(self):
        args = parser_for_post.parse_args()
        abort_if_no_access('POST', args['api_key'])
        session = create_session()
        user = User(
            username=args['username'],
            email=args['email'],
            hashed_password=sha256(
                args['hashed_password'].encode('utf-8')).hexdigest(),
            access=args['access_level']

        )
        session.add(user)
        session.commit()
        return jsonify({'id': user.id})
