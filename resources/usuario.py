from flask_restful import Resource, reqparse
from models.usuario import UserModel
from flask_jwt_extended import create_access_token, jwt_required, get_raw_jwt
from werkzeug.security import safe_str_cmp
from blacklist import BLACKLIST

atributos = reqparse.RequestParser()
atributos.add_argument('login', type=str, required=True, help='O login não pode ser deixado em branco.')
atributos.add_argument('senha', type=str, required=True, help='A senha não pode ser deixado em branco.')


class User(Resource):
    # /usuarios/{user_id}
    def get(self, user_id):
        user = UserModel.find_user(user_id)
        if user:
            return user.json()
        return {'message': 'Usuario nao encontrado.'}, 404  # not found

    @jwt_required
    def delete(self, user_id):
        user = UserModel.find_user(user_id)
        if user:
            try:
                user.delete_user()
                return {'message': 'Usuario deletado'}
            except:
                return {'message': 'Um erro ocorreu ao tentar deletar o usuario'}, 500
        return {'message': 'Usuario nao encontrado.'}, 404


class UserRegister(Resource):
    # /cadastro
    def post(self):
        dados = atributos.parse_args()

        if UserModel.find_by_login(dados['login']):
            return {"message": "O login '{}' já existe.".format(dados['login'])}

        user = UserModel(**dados)
        user.save_user()
        return {'message': 'Usuario criado com sucesso!'}, 201


class UserLogin(Resource):

    @classmethod
    def post(cls):
        dados = atributos.parse_args()
        user = UserModel.find_by_login(dados['login'])

        if user and safe_str_cmp(user.senha, dados['senha']):
            token_de_acesso = create_access_token(identity=user.user_id)
            return {'access_token': token_de_acesso}, 200
        return {'message': 'Usuario ou senha incorretos.'}


class UserLogout(Resource):

    @jwt_required
    def post(self):
        jwt_id = get_raw_jwt()['jti']  # Jwt Token Identifier
        BLACKLIST.add(jwt_id)
        return {'message': 'Deslogado com sucesso!'}, 200
