import datetime
import json
import http.client
from flask import Flask,render_template,request,jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
from sqlalchemy import JSON, true
#import mysql.connector

datospac = ""
notelefono = ""
app = Flask(__name__)

## Configuracion BD SQLLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tamarapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

## Definicion de tablas con sus columnas
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fechahora = db.Column(db.DateTime, default=datetime.datetime.today)
    mensajelog = db.Column(db.TEXT)

## Creacion tabla si no existe
with app.app_context():
    db.create_all()

## Ordenacion de registros por fecha, hora
def ordenar_fechahora(registros):
    return sorted(registros, key=lambda x:x.fechahora, reverse=True)

@app.route('/')

## Obtener registros de la tabla
def index():
    registros = Log.query.all()
    registros_ordenados = ordenar_fechahora(registros)
    return render_template('index.html',registros=registros_ordenados)

## Funcion de Guardar en BD Array de mensajes
mensajes_log = []

def agregar_mensajes_log(texto):
    mensajes_log.append(texto)
    #Guardar el mensaje en BD
    nuevo_registro = Log(mensajelog=texto)
    db.session.add(nuevo_registro)
    db.session.commit()

## TOKEN de Verificacion para la configuracion
TOKEN_TWSCODE = "TWSCodeJG#75"

## Creacion de WwbHook
@app.route('/webhook',methods=['GET','POST'])
def webhook():
    if request.method == 'GET':
        challenge = verificar_token(request)
        return challenge
    elif request.method == 'POST':
        reponse = recibir_mensajes(request)
        return reponse

def verificar_token(req):
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')

    #and challenge
    if token == TOKEN_TWSCODE:
        return challenge
    else:
        return jsonify({'error':'TOKEN INVALIDO'}),401
    
## Recepcion de Mensajes WhatApps
def recibir_mensajes(req):
    try:
        req = request.get_json()
        entry = req['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        objeto_mensaje = value['messages']
        agregar_mensajes_log(json.dumps(objeto_mensaje[0]))

        if objeto_mensaje:
            messages = objeto_mensaje[0]

            if "type" in messages:
                tipo = messages["type"]
                agregar_mensajes_log(json.dumps(messages))


                if tipo == "interactive":
                    tipo_interactivo = messages["interactive"]["type"]

                    if tipo_interactivo == "button_reply":
                        text = messages["interactive"]["button_reply"]["id"]
                        notelefono = messages["from"]

                        enviar_mensaje_whatapps(text,notelefono)
                    
                    elif tipo_interactivo == "list_reply":
                        text = messages["interactive"]["list_reply"]["id"]
                        notelefono = messages["from"]

                        enviar_mensaje_whatapps(text,notelefono)


                if "text" in messages:
                    text = messages["text"]["body"] ## Cuerpo del Mensaje
                    notelefono = messages["from"] ## No Telefono
                    
                    LenCedula = len(text)
                    IsNumeroCedula = text.isdigit()

                    if IsNumeroCedula:
                        if LenCedula>=7:
                             traer_datoscedula(text)
                        else:
                            enviar_mensaje_whatapps(text,notelefono)
                    else:
                        enviar_mensaje_whatapps(text,notelefono)

                    #Guardar Log en la BD
                    agregar_mensajes_log(json.dumps(messages))

        return jsonify({'message':'EVENT_RECEIVED'})
    except Exception as e:
        return jsonify({'error':'ERROR'})

## Envio de Mensajes Respuesta a Whatapps
def enviar_mensaje_whatapps(texto,number):
    texto = texto.lower()
    if ("hola" in texto) or ("buenos dias" in texto) or ("buenas tardes" in texto):   
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🚀 Hola Bienvenido!!, Por favor, ingresa un número #️⃣ para recibir información.\n \n1️⃣. Información de Citas. ❔\n2️⃣. Ubicación Sedes. 📍\n3️⃣. Horario de Atención. 📄\n4️⃣. Regresar al Menú. 🕜"
            }
        }
    elif "1" == texto:
       data =  {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,            
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🚀Por favor, ingresa un número de Identificacion/Cedula"
            }        
        }
    elif "2" in texto:
         data = {
            "messaging_product": "whatsapp",
            "to": number,
            "type": "location",
            "location": {
                "latitude": "-11.005167253247674",
                "longitude": "-74.8043525197199",
                "name": "TAMARA Imagenes",
                "address": "Alto Prado"
            }
        }       
    elif "3" in texto:
         data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "📅 Horario de Atención : Lunes a Viernes. \n🕜 Horario : 8:00 am a 6:00 pm 🤓"
            }
        }       
    else:
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🚀 Hola, visita mi web https://tamaraimagenes.com para más información.\n \n📌Por favor, ingresa un número #️⃣ para recibir información.\n \n1️⃣. Información de Citas. ❔\n2️⃣. Ubicación Sedes. 📍\n3️⃣. Horario de Atención. 📄\n4️⃣. Regresar al Menú. 🕜"
            }
        }
    ## Convertir a el diccionario en formato json
    data = json.dumps(data)        
    Connect_META(data)
    ## "body": "🚀 Hola, visita mi web https://tamaraimagenes.com para más información.\n \n📌Por favor, ingresa un número #️⃣ para recibir información.\n \n1️⃣. Información de Citas. ❔\n2️⃣. Ubicación Sedes. 📍\n3️⃣. Enviar temario en PDF. 📄\n4️⃣. Audio explicando curso. 🎧\n5️⃣. Video de Introducción. ⏯️\n6️⃣. Hablar con AnderCode. 🙋‍♂️\n7️⃣. Horario de Atención. 🕜 \n0️⃣. Regresar al Menú. 🕜"

## Envio de datos Cedula
def enviar_datos(datos,number):
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "VIENE DE TRAER"+datos
            }
        }
        ## Convertir a el diccionario en formato json
        data = json.dumps(data)        
        Connect_META(data)

## Funcion Verifica Cedula en BD
def traer_datoscedula(nocedula):
    enviar_datos("TRAER CEDULA",notelefono)
    # url_base = "https://api.tvmaze.com/search/shows"
    # param = {"q":"mcgyver"}
    # api_url = "https://appsintranet.grupocampbell.com/ApiCampbell/api/Pacientes"
    # args = {"CodigoEmp": "C30", "criterio": nocedula}
    # #args = {"CodigoEmp": "C30", "criterio": "'"+nocedula+"'","ipServidor": "192.168.2.235","bdDatos": "bd","dbPort": 3396,"bdUser": "jgarcia","bdPass": "lili2004"}
    # #responpost = requests.post(url_base, json=param)
    # responget = requests.get(api_url, json=args)
    # arraydata = responget.json()
    # for key, value in arraydata.items():
    #     #print(key, ":", value)
    #     if value == "1": 
    #        datospac = arraydata["Paciente"]
    #        print("Datos a Enviar: ", datospac)
    #        break

    # enviar_datos(datospac,notelefono)
    #conectar_mysql(nocedula)
    #validar_cedula(nocedula)

## Funcion Extraer Data Response.json
# def extract_key_value(json_data, key):
#     """Extracts a specific key-value pair from a JSON data"""
#     data = json.loads(json_data)
#     value = data.get(key)
#     return value

# def find_key(d,value): 
#     for k, v in d.items(): 
#        if v == value: 
#             return k 
#     return None 

#### Conexion Render/META
## Convertir a el diccionario en formato json
def Connect_META(data):
    ## Conexion META
    print("Mensaje en META: ", data)
    headers = {
        "Content-Type" : "application/json",
        "Authorization" : "Bearer EAAFojfaX74gBOwuQJbKefKYthc6xToVgiZAIjsd5ry2hBIOkH2y7wBIZCgzQxReECvL9B8yaJFzoq2iAbMtEVFjSAbbzJlZAvSbu9xOvwZCXTSPneJdZANd3wPwoNhfrZB3fwLPJXDob0Nj5fRbdqmQ239r5X4JiZAZAKCHcDD9njtElF3ji83cRVvGeyZBVeG5IUUgWAi9ryzkyOTVB5yYZCGZCLcZD"
    }
    connection = http.client.HTTPSConnection("graph.facebook.com")

    try:
        connection.request("POST","/v21.0/489807960875135/messages", data, headers)
        response = connection.getresponse()
        print(response.status, response.reason)
    except Exception as e:
        agregar_mensajes_log(json.dumps(e))
    finally:
        connection.close()

## Conexion a Web API
##def conectar_mysql(nocedula):
    #response = requests.post(f"{BASE_URL}/products", json=new_product)   
    # db = mysql.connector.connect(
	# host='localhost',
	# user=’username’,
	# password=’password’
    # )

    # sql = "select name,car_number from drivers"
    # cursor = db.cursor()
    # cursor.execute(sql)

    # results = cursor.fetchall()

## Ejecucion en Entorno Virtual
if __name__ == '__main__':
    app.run(debug=True)

