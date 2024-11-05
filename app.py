from datetime import datetime
import json
import http.client
from flask import Flask,render_template,request,jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import true

app = Flask(__name__)

## Configuracion BD SQLLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tamarapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

## Definicion de tablas con sus columnas
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fechahora = db.Column(db.DateTime, default=datetime.utcnow)
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
        
        if objeto_mensaje:
            messages = objeto_mensaje[0]

            if "type" in messages:
                tipo = messages["type"]
                agregar_mensajes_log(json.dumps(messages))


                if tipo == "interactive":
                    tipo_interactivo = messages["interactive"]["type"]

                    if tipo_interactivo == "button_reply":
                        text = messages["interactive"]["button_reply"]["id"]
                        numero = messages["from"]

                        enviar_mensaje_whatapps(text,numero)
                    
                    elif tipo_interactivo == "list_reply":
                        text = messages["interactive"]["list_reply"]["id"]
                        numero = messages["from"]

                        enviar_mensaje_whatapps(text,numero)


                if "text" in messages:
                    text = messages["text"]["body"] ## Cuerpo del Mensaje
                    numero = messages["from"] ## No Telefono
                    enviar_mensaje_whatapps(text,numero)

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
    elif "1" in texto:
       data =  {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,            
             "type": "text",
            "text": {
                "preview_url": False,
                "body": "🚀Por favor, ingresa un número de Identificacion/Cedula"
            }        }
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
    ## "body": "🚀 Hola, visita mi web https://tamaraimagenes.com para más información.\n \n📌Por favor, ingresa un número #️⃣ para recibir información.\n \n1️⃣. Información de Citas. ❔\n2️⃣. Ubicación Sedes. 📍\n3️⃣. Enviar temario en PDF. 📄\n4️⃣. Audio explicando curso. 🎧\n5️⃣. Video de Introducción. ⏯️\n6️⃣. Hablar con AnderCode. 🙋‍♂️\n7️⃣. Horario de Atención. 🕜 \n0️⃣. Regresar al Menú. 🕜"

    #### Conexion Render/META
    ## Convertir a el diccionario en formato json
    data = json.dumps(data)        

    ## Conexion META
    headers = {
        "Content-Type" : "application/json",
        "Authorization" : "Bearer EAAFojfaX74gBO5L7MqhiVRv4MLleZBRIeSBYmZCisn4D8PGvH008N88Lio5jQiUEKJJQpFpxkV6GtZA4FVK08nm3ZAITNe3ZAd9MTXmBGcJa3Y1fDoe11MjnKMLwCPYlFmCdOP7JIRDwEdvPtf20eKlHBjCZBDu7DKZBDvHNwtTB8HrNukoh1PcgZAeV2ftlRC3M6EyoNxcAueTj3PAqZCh8Gpn0s"
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

## Funcion Verifica Cedula en BD

## Conexion a Web API


## Ejecucion en Entorno Virtual
if __name__ == '__main__':
    app.run(debug=True)

