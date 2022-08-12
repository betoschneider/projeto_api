from flask_restful import Resource, reqparse
from models.hotel import HotelModel
from flask_jwt_extended import jwt_required
import sqlite3

def normalize_path_params(cidade=None,
                          estrelas_min=0,
                          estrelas_max=5,
                          diaria_min=0,
                          diaria_max=10000,
                          limit=50,
                          offset=0, **dados):
    if cidade:
        return {'estrelas_min': estrelas_min,
                'estrelas_max': estrelas_max,
                'diaria_min': diaria_min,
                'diaria_max': diaria_max,
                'cidade': cidade,
                'limit': limit,
                'offset': offset}
    return {'estrelas_min': estrelas_min,
            'estrelas_max': estrelas_max,
            'diaria_min': diaria_min,
            'diaria_max': diaria_max,
            'limit': limit,
            'offset': offset}

# path /hoteis?cidade=Rio de Janeiro&estrelas_min=4&diarias_max=400
path_params = reqparse.RequestParser()
path_params.add_argument('cidade', type=str)
path_params.add_argument('estrelas_min', type=float)
path_params.add_argument('estrelas_max', type=float)
path_params.add_argument('diaria_min', type=float)
path_params.add_argument('diaria_max', type=float)
path_params.add_argument('limit', type=int) # qtd de elementos que deseja exibir
path_params.add_argument('offset', type=int) # qtd de elementos que deseja pular

class Hoteis(Resource):
    def get(self):
        dados = path_params.parse_args()
        dados_validos = {chave:dados[chave] for chave in dados if dados[chave] is not None} # somente dados não nulos
        parametros = normalize_path_params(**dados_validos)

        connection = sqlite3.connect('banco.db')
        cursor = connection.cursor()

        if not parametros.get('cidade'):
            consulta = "SELECT * FROM hoteis \
                       WHERE (estrelas >= ? and estrelas <= ?) \
                       and (diaria >= ? and diaria <= ?) \
                       LIMIT ? OFFSET ?"
            valor_parametro = tuple([parametros[chave] for chave in parametros])
            resultado = cursor.execute(consulta, valor_parametro)
        else:
            consulta = "SELECT * FROM hoteis \
                                   WHERE (estrelas >= ? and estrelas <= ?) \
                                   and (diaria >= ? and diaria <= ?) \
                                   and (cidade = ?) \
                                   LIMIT ? OFFSET ?"
            valor_parametro = tuple([parametros[chave] for chave in parametros])
            resultado = cursor.execute(consulta, valor_parametro)

        hoteis = []
        for linha in resultado:
            hoteis.append({'hotel_id': linha[0],
                           'nome': linha[1],
                           'estrelas': linha[2],
                           'diaria': linha[3],
                           'cidade': linha[4]})

        #return {'hoteis': [hotel.json() for hotel in HotelModel.query.all()]} # consulta com query de HotelModel
        return {'hoteis': hoteis}

class Hotel(Resource):
    #atributos pro post
    atributos = reqparse.RequestParser()
    atributos.add_argument('nome', type=str, required=True, help="O campo 'nome' não pode ser deixado em branco.")
    atributos.add_argument('estrelas', type=float, required=True, help="O campo 'estrelas' não pode ser deixado em branco.")
    atributos.add_argument('diaria', type=float)
    atributos.add_argument('cidade', type=str)

    def get(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            return hotel.json()
        return {'message': 'Hotel nao encontrado.'}, 404 #not found
    @jwt_required
    def post(self, hotel_id):
        if HotelModel.find_hotel(hotel_id):
            return {"message": "Hotel id '%s' já existe." % hotel_id}

        dados = Hotel.atributos.parse_args() #transforma em dicionario
        hotel = HotelModel(hotel_id, **dados)
        try:
            hotel.save_hotel()
        except:
            return {'message': 'Houve um erro interno e os dados nao foram salvos.'}, 500 #internal server error
        return hotel.json(), 200

    @jwt_required
    def put(self, hotel_id):
        dados = Hotel.atributos.parse_args()  # transforma em dicionario
        hotel_encontrado = HotelModel.find_hotel(hotel_id)
        if hotel_encontrado:
            hotel_encontrado.update_hotel(**dados)
            hotel_encontrado.save_hotel()
            return hotel_encontrado.json(), 200 #sucesso
        hotel = HotelModel(hotel_id, **dados)
        try:
            hotel.save_hotel()
        except:
            return {'message': 'Houve um erro interno e os dados nao foram salvos.'}, 500  # internal server error
        return hotel.json(), 201

    @jwt_required
    def delete(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            try:
                hotel.delete_hotel()
                return {'message': 'Hotel deletado'}
            except:
                return {'message': 'Um erro ocorreu ao tentar deletar o hotel'}, 500
        return {'message': 'Hotel nao encontrado.'}, 404