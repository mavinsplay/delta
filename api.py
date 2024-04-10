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

parser_for_link_post = reqparse.RequestParser()
parser_for_link_post.add_argument('database_name', required=True)
parser_for_link_post.add_argument('sourse_link', required=True)
parser_for_link_post.add_argument('db_link', required=True)
parser_for_link_post.add_argument('api_key', required=True)



access_level = {
    'user': [],
    'admin': ['GET'],
    'developer': ['GET', 'DELETE', 'POST', 'PUT'],
}

db_access_level = {
    'user': [],
    'admin': ['GET', 'DELETE'],
    'developer': ['GET', 'DELETE', 'POST', 'PUT']
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
        
def abort_if_no_link(link_id):
    session = create_session()
    link = session.query(Upload_DB).get(link_id)
    if not link:
        abort(404, message=f"Link {link_id} not found")


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
    

class DbLinksResourse(Resource):
    def get(self, link_id):
        args = parser_for_get.parse_args()
        abort_if_no_access('GET', args['api_key'])
        abort_if_no_link(link_id)
        session = create_session()
        link = session.query(Upload_DB).get(link_id)
        return jsonify({'link': link.to_dict(
            only=('id', 'user_id', 'database_name', 'sourse_link', 'db_link'))})

    def delete(self, link_id):
        args = parser_for_get.parse_args()
        abort_if_no_access('DELETE', args['api_key'])
        abort_if_no_link(link_id)
        session = create_session()
        link = session.query(Upload_DB).get(link_id)
        session.delete(link)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, link_id):
        args = parser_for_link_post.parse_args()
        abort_if_no_access('PUT', args['api_key'])
        abort_if_no_link(link_id)
        session = create_session()
        link = session.query(Upload_DB).get(link_id)
        user_id = link.user.id
        link.user_id=user_id
        link.database_name=args['database_name']
        link.database_name=args['database_name']
        link.sourse_link=args['sourse_link']
        link.db_link=args['db_link']
        session.merge(link)
        session.commit()
        return jsonify({'link': link.to_dict(
            only=('id', 'user_id', 'database_name', 'sourse_link', 'db_link'))})
        
class DbLinksResourseList(Resource):
    def get(self):
        args = parser_for_get.parse_args()
        abort_if_no_access('GET', args['api_key'])
        session = create_session()
        links = session.query(Upload_DB).all()
        return jsonify({'links': [item.to_dict(
            only=('id', 'user_id', 'database_name', 'sourse_link', 'db_link')) for item in links]})

    def post(self):
        args = parser_for_link_post.parse_args()
        abort_if_no_access('POST', args['api_key'])
        session = create_session()
        user = session.query(ApiKeyAsoc).filter(ApiKeyAsoc.key == args['api_key']).first()
        link = Upload_DB(
            user_id=user.id,
            database_name=args['database_name'],
            sourse_link=args['sourse_link'],
            db_link=args['db_link']
        )
        session.add(link)
        session.commit()
        return jsonify({'id': link.id})