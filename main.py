
"""@author: rjimenez,
version: 06/22"""
import binascii
import socket
import threading
import googlemaps
import mysql.connector
from datetime import datetime, timedelta
import requests
from requests.exceptions import HTTPError
from requests.structures import CaseInsensitiveDict
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import time
import sys

original_stdout = sys.stdout
now = datetime.now()

mydb = mysql.connector.connect(host="localhost", user="root", password="testing", database="telehelp")
mycursor = mydb.cursor()
query = "SELECT * FROM googlemaps "
mycursor.execute(query)
for (servertabla) in mycursor:
    KeyMapsGoogle = servertabla[0]


class ClientThread(threading.Thread):

    def desencripta(self, dato_recibido_en_bytes):
        in_bytes = dato_recibido_en_bytes[11:-5]

        hex_bytes = binascii.hexlify(in_bytes)

        CLAVE_PUBLICA = b'5E358EDA203DCE5056112FD80573FBDB'
        key = binascii.unhexlify(CLAVE_PUBLICA)
        IV_PUBLICA = b'DB48B53D690B6488C2973EC4F295D685'
        iv = binascii.unhexlify(IV_PUBLICA)
        CLAVE_PRIVADA = b'D02008B99B86C7EBF5E59CCC7157D3CA'
        key1 = binascii.unhexlify(CLAVE_PRIVADA)
        IV_PRIVADA = b'D990195F1BAD534104806D732E0AFB8B'
        iv1 = binascii.unhexlify(IV_PRIVADA)
        try:
            cipher = AES.new(key, AES.MODE_CBC, iv=iv)
            original_data = cipher.decrypt(in_bytes)

            cipherx = AES.new(key1, AES.MODE_CBC, iv=iv1)
            original_datax = cipherx.decrypt(in_bytes)

            if b'[3G' in original_data:
                return original_data
            elif b'[3G' in original_datax:
                return original_datax

        except:
            pass

    def encripta(self, entrada):

        CLAVE_PRIVADA = b'D02008B99B86C7EBF5E59CCC7157D3CA'
        key1 = binascii.unhexlify(CLAVE_PRIVADA)
        IV_PRIVADA = b'D990195F1BAD534104806D732E0AFB8B'
        iv1 = binascii.unhexlify(IV_PRIVADA)

        cipher1 = AES.new(key1, AES.MODE_CBC, iv1)
        ciphered_data1 = cipher1.encrypt(pad(entrada, 16, style='pkcs7'))

        cipher2 = AES.new(key1, AES.MODE_CBC, iv=iv1)

        preambulo = b'\xffAQSH'

        longcuadro = hex(len(ciphered_data1) + 11)
        longcuadro = str(longcuadro.replace('0x', ''))
        longcuadro = binascii.unhexlify(longcuadro)
        longcuadro = b'\x00' + longcuadro

        campoAmpliado = b'\x01\x1E\x00\x00'

        import struct
        from time import time
        curTime = int(time())
        marcaTiempo = struct.pack(">i", curTime)

        mensajerespuestaparcial = preambulo + longcuadro + campoAmpliado + ciphered_data1 + marcaTiempo
        n = 0
        a = mensajerespuestaparcial[0]

        while n < len(mensajerespuestaparcial) - 1:
            b = mensajerespuestaparcial[n + 1]
            c = a ^ b
            n = n + 1
            a = c

        bitxor = hex(c)

        if len(bitxor) % 2 == 0:
            bitxor = str(bitxor.replace('0x', ''))
            bitxor = binascii.unhexlify(bitxor)
        else:
            bitxor = str(bitxor.replace('0x', '0'))
            bitxor = binascii.unhexlify(bitxor)

        mensajEnviar = mensajerespuestaparcial + bitxor

        return mensajEnviar

    def __init__(self, clientAddress, clientsocket):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        print("Nuevo cliente agregado: ", clientAddress)

    def run(self):
        print("Connection from : ", clientAddress)
        socket_abierto = True
        while socket_abierto:
            sys.stdout = open(str(datetime.now().strftime('%Y-%m-%d')) + '.txt', 'a')
            dato_recibido_en_bytes = self.csocket.recv(1024).strip()
            if dato_recibido_en_bytes != b'':
                if b'*G3[' in dato_recibido_en_bytes:  # 0. Videollamada
                    dato_recibido_en_str = dato_recibido_en_bytes.decode()
                    dato_recibido_en_str = ''.join(reversed(dato_recibido_en_str))

                    if "videocall" in dato_recibido_en_str:
                        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " Recibido desde el cliente:",
                              dato_recibido_en_str)

                        respuesta_en_str = "{}".format(dato_recibido_en_str[0:14] + "*000D*app_videocall]")
                        mydb = mysql.connector.connect(host="localhost", user="root",
                                                       password="testing",
                                                       database="telehelp")
                        mycursor = mydb.cursor()
                        sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento) VALUES (%s, %s, %s, %s)"
                        val = (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), respuesta_en_str, respuesta_en_str[4:14],
                               "app_videocall")
                        mycursor.execute(sql, val)
                        mydb.commit()
                        print(mycursor.rowcount, "Solicitud de Videollamada ingresada.")

                        funcon = mysql.connector.connect(host="localhost", user="root",
                                                         password="testing",
                                                         database="telehelp")
                        funcursor = funcon.cursor()
                        query = "SELECT * FROM dispositivos WHERE IMEI=%s"
                        IMEI = str(dato_recibido_en_str[4:14])
                        print(str(IMEI))
                        funcursor.execute(query, (IMEI,))

                        for (userName) in funcursor:
                            linea = userName[5]
                            codUsuario = userName[6]
                            latitudconsulta = userName[9]
                            longitudconsulta = userName[10]
                            FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            print(linea)
                            print(codUsuario)
                            print(latitudconsulta)
                            print(longitudconsulta)
                            print(FECHAORA)

                        funcursor1 = funcon.cursor()
                        query1 = "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1"
                        funcursor1.execute(query1, (IMEI,))

                        for (servertabla) in funcursor1:
                            Idevento = servertabla[0]
                            print(Idevento)

                            url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(KeyMapsGoogle)
                            headers = CaseInsensitiveDict()
                            headers["Content-Length"] = "0"
                            resp = requests.post(url, headers=headers, verify=False)
                            result = resp.json()['results'][0]
                            geodata = dict()
                            geodata['address'] = result['formatted_address']
                            print(geodata['address'])

                            url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                            headers = CaseInsensitiveDict()
                            headers["Accept"] = "application/json"
                            headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                            headers["Content-Type"] = "application/json"

                            data = """{
                                                                "Id" :""" + str(Idevento) + """,
                                                                "TelefonoAsociado" : """ + """\"""" + str(
                                linea) + """\"""" + """,
                                                                "UsuarioCodigo" :""" + """\"""" + str(
                                codUsuario) + """\"""" + """,
                                                                "TipoEvento" : "VIDEOLLAMADA",
                                                                "Accion" : "A",
                                                                "Fecha y Hora" : """ + """\"""" + str(
                                FECHAORA) + """\"""" + """,
                                                                "Direccion" :""" + """\"""" + str(
                                geodata['address']) + """\"""" + """,
                                                                "Latitud" : """ + """\"""" + str(
                                latitudconsulta) + """\"""" + """,
                                                                "Longitud" : """ + """\"""" + str(
                                longitudconsulta) + """\"""" + """
                                                                }"""

                            print(data)
                            print(str(data) + " " + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                            resp = requests.post(url, headers=headers, data=data, verify=False)
                            print(resp.json())

                elif b'AQSH' in dato_recibido_en_bytes:
                    print("dato recibido en bytes: " + str(dato_recibido_en_bytes))
                    cantidad_cadenas = dato_recibido_en_bytes.count(b'\xffAQSH')
                    print("Cantidad de Mensajes: " + str(cantidad_cadenas))
                    separa = dato_recibido_en_bytes.split(b'\xffAQSH')
                    del separa[0]
                    for x in separa:
                        mensaje = b'\xffAQSH' + x
                        mensajeEncript = self.desencripta(mensaje)
                        print(str(mensajeEncript))
                        dato_recibido_en_str = mensajeEncript.decode(errors='ignore')
                        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " Recibido desde el cliente:",
                              str(dato_recibido_en_str))

                        if b'KI' in mensajeEncript:  # 1. Encrypt
                            respuesta_en_str = dato_recibido_en_str[0:14] + "*0005*KI,30]"
                            respuesta_en_bytes = bytes(respuesta_en_str, encoding='utf8')
                            mensajeResp = self.encripta(respuesta_en_bytes)
                            self.csocket.send(mensajeResp)

                        elif b'LK' in mensajeEncript:
                            respuesta_en_str = "{}".format(dato_recibido_en_str[0:14] + "*0002*LK]")
                            respuesta_en_bytes = bytes(respuesta_en_str, encoding='utf8')
                            mensajeResp = self.encripta(respuesta_en_bytes)
                            self.csocket.send(mensajeResp)

                            # **** Encendido GPS ****
                            respuesta_en_str4 = "{}".format(dato_recibido_en_str[0:14] + "*000C*APPLOCK,DW-1]")
                            respuesta_en_bytes4 = bytes(respuesta_en_str4, encoding='utf8')
                            mensajeResp4 = self.encripta(respuesta_en_bytes4)
                            self.csocket.send(mensajeResp4)

                            # **** Envío de datos ****
                            respuesta_en_str3 = "{}".format(dato_recibido_en_str[0:14] + "*000A*UPLOAD,600]")
                            respuesta_en_bytes3 = bytes(respuesta_en_str3, encoding='utf8')
                            mensajeResp3 = self.encripta(respuesta_en_bytes3)
                            self.csocket.send(mensajeResp3)

                            # **** Configuro Número Telefónico para el SOS y Caída ****
                            respuesta_en_str1 = "{}".format(
                                dato_recibido_en_str[0:14] + "*000D*SOS1,19201923]")  # + "*000E*SOS1,098694249]"
                            respuesta_en_bytes1 = bytes(respuesta_en_str1, encoding='utf8')
                            mensajeResp1 = self.encripta(respuesta_en_bytes1)
                            self.csocket.send(mensajeResp1)

                            respuesta_en_str6 = "{}".format(
                                dato_recibido_en_str[0:14] + "*0002*CR]")  # [SG*5678901234*0002*CR]
                            respuesta_en_bytes6 = bytes(respuesta_en_str6, encoding='utf8')
                            mensajeResp6 = self.encripta(respuesta_en_bytes6)
                            self.csocket.send(mensajeResp6)

                            cadena = dato_recibido_en_str[20:]
                            arrayCadena = cadena.split(",")
                            bat = arrayCadena[3]
                            bat = bat.split("]")
                            bat= bat[0]
                            #bat = bat.replace("]", "")
                            print("NIVEL DE BATERIA: ", bat)

                            if int(bat)<30:
                                print("La bateria es menor a 30%")
                                respuesta_en_str8 = "{}".format(
                                    dato_recibido_en_str[
                                    0:14] + "*0034*MESSAGE,0042004100540045005200490041002000420041004A0041]")
                                respuesta_en_bytes8 = bytes(respuesta_en_str8, encoding='utf8')
                                mensajeResp8 = self.encripta(respuesta_en_bytes8)
                                self.csocket.send(mensajeResp8)



                            # **** Estado para la conexión/desconexión ****

                            IMEI = dato_recibido_en_str[4:14]
                            print(IMEI)
                            funcon = mysql.connector.connect(host="localhost", user="root",
                                                             password="testing",
                                                             database="telehelp")
                            funcursor = funcon.cursor()
                            query = ("SELECT * FROM lk WHERE IMEI=%s")
                            funcursor.execute(query, (IMEI,))

                            for (userName) in funcursor:
                                ultimoLK = userName[1]
                                proximoLK = userName[2]
                                Alarma = userName[3]
                                Sensibilidad = userName[4]
                                print(Sensibilidad)

                                respuesta_en_str5 = "{}".format(
                                    dato_recibido_en_str[0:14] + "*0009*LSSET," + str(
                                        Sensibilidad) + "+6]")  # [3G*4504816144*0009*LSSET,X+6]
                                print(respuesta_en_str5)
                                respuesta_en_bytes5 = bytes(respuesta_en_str5, encoding='utf8')
                                mensajeResp5 = self.encripta(respuesta_en_bytes5)
                                self.csocket.send(mensajeResp5)

                                ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                proximoLK = datetime.strptime(ahora, '%Y-%m-%d %H:%M:%S') + timedelta(minutes=6)
                                print("El próximo LK de este dispositivo será: " + str(proximoLK))
                                mydb = mysql.connector.connect(host="localhost", user="root",
                                                               password="testing",
                                                               database="telehelp")
                                mycursor = mydb.cursor()

                                sql = "UPDATE lk SET Date = %s, Alarma = %s, Proxima = %s WHERE IMEI = %s"
                                val = (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "NO", proximoLK, IMEI)
                                mycursor.execute(sql, val)
                                mydb.commit()
                                print("LK del IMEI: " + str(IMEI) + " fue recibido")
                                print("Dispositivo NO ALARMADO")

                            funcon = mysql.connector.connect(host="localhost", user="root",
                                                             password="testing",
                                                             database="telehelp")
                            funcursor = funcon.cursor()
                            query = ("SELECT * FROM lk WHERE IMEI=%s")
                            funcursor.execute(query, (IMEI,))

                            for (userName) in funcursor:
                                ultimoLK = userName[1]
                                proximoLK = userName[2]
                                Alarma = userName[3]

                                ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                proximoLK = datetime.strptime(ahora, '%Y-%m-%d %H:%M:%S') + timedelta(minutes=6)
                                print("El próximo LK de este dispositivo será: " + str(proximoLK))
                                mydb = mysql.connector.connect(host="localhost", user="root",
                                                               password="testing",
                                                               database="telehelp")
                                mycursor = mydb.cursor()

                                sql = "UPDATE lk SET Date = %s, Alarma = %s, Proxima = %s WHERE IMEI = %s"
                                val = (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "NO", proximoLK, IMEI)
                                mycursor.execute(sql, val)
                                mydb.commit()
                                print("LK del IMEI: " + str(IMEI) + " fue recibido")
                                print("Dispositivo NO ALARMADO")


                        elif b'UD' in mensajeEncript or b'AL' in mensajeEncript:
                            if b'00010000' in mensajeEncript or b'00010001' in mensajeEncript:
                                inicio = time.time()
                                print("Se recibió SOS")

                                print("Se recibe SOS " + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                dato_recibido_en_str = mensajeEncript.decode()
                                respuesta_en_str = "{}".format(dato_recibido_en_str[0:14] + "*0002*AL]")
                                print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " Recibido desde el cliente:",
                                      str(mensajeEncript))

                                respuesta_en_str6 = "{}".format(
                                    dato_recibido_en_str[0:14] + "*0002*CR]")  # [SG*5678901234*0002*CR]
                                respuesta_en_bytes6 = bytes(respuesta_en_str6, encoding='utf8')
                                mensajeResp6 = self.encripta(respuesta_en_bytes6)
                                self.csocket.send(mensajeResp6)

                                print(str(mensajeEncript) + "\n")

                                IMEI = dato_recibido_en_str[4:14]
                                print(IMEI)
                                cadena = dato_recibido_en_str[20:]
                                arrayCadena = cadena.split(",")
                                Alarmas = arrayCadena[16]
                                print(arrayCadena[3])  # si es A o V
                                if "A" == arrayCadena[3]:
                                    if arrayCadena[5] == "S":
                                        latitud = "-" + arrayCadena[4]
                                    else:
                                        latitud = arrayCadena[4]

                                    if arrayCadena[7] == "W":
                                        longitud = "-" + arrayCadena[6]
                                    else:
                                        longitud = arrayCadena[6]

                                    # se actualiza la ubicación en la BD
                                    mydb = mysql.connector.connect(host="localhost", user="root",
                                                                   password="testing",
                                                                   database="telehelp")
                                    mycursor = mydb.cursor()

                                    sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                    val = (
                                        float(latitud), float(longitud), datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        IMEI)
                                    mycursor.execute(sql, val)
                                    mydb.commit()
                                    print("registro de ubicacion actualizado")

                                    # Insertar el evento en la BD
                                    sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento) VALUES (%s, %s, %s, %s)"
                                    val = (
                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'), respuesta_en_str,
                                        respuesta_en_str[4:14],
                                        "SOS")
                                    mycursor.execute(sql, val)
                                    mydb.commit()
                                    print("Alerta SOS ingresada.")

                                    funcon = mysql.connector.connect(host="localhost", user="root",
                                                                     password="testing",
                                                                     database="telehelp")
                                    funcursor = funcon.cursor()
                                    query = "SELECT * FROM dispositivos WHERE IMEI=%s"
                                    IMEI = str(dato_recibido_en_str[4:14])
                                    print(str(IMEI))
                                    funcursor.execute(query, (IMEI,))

                                    for (userName) in funcursor:
                                        linea = userName[5]
                                        codUsuario = userName[6]
                                        latitudconsulta = userName[9]
                                        longitudconsulta = userName[10]
                                        FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        print(linea)
                                        print(codUsuario)
                                        print(latitudconsulta)
                                        print(longitudconsulta)
                                        print(FECHAORA)

                                    funcursor1 = funcon.cursor()
                                    query1 = "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1"
                                    funcursor1.execute(query1, (IMEI,))

                                    for (servertabla) in funcursor1:
                                        Idevento = servertabla[0]
                                        print(Idevento)

                                        url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                            latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                            KeyMapsGoogle)
                                        headers = CaseInsensitiveDict()
                                        headers["Content-Length"] = "0"
                                        retries = 3

                                        for n in range(retries):
                                            try:
                                                response = requests.post(url, headers=headers, verify=False)
                                                response.raise_for_status()  # 200,201,202,203,204,205,206,207,208,226
                                                result = response.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                    "Id" :""" + str(Idevento) + """,
                                                                                    "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                    "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                    "TipoEvento" : "SOS",
                                                                                    "Accion" : "A",
                                                                                    "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                    "Direccion" :""" + """\"""" + str(
                                                    geodata["address"]) + """\"""" + """,
                                                                                    "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                    "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                    }"""

                                                print(data)

                                                print("\n" + str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")
                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())
                                                fin = time.time()
                                                print(fin - inicio)

                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code

                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411,
                                                            412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"

                                                    data = """{
                                                                                        "Id" :""" + str(Idevento) + """,
                                                                                        "TelefonoAsociado" : """ + """\"""" + str(
                                                        linea) + """\"""" + """,
                                                                                        "UsuarioCodigo" :""" + """\"""" + str(
                                                        codUsuario) + """\"""" + """,
                                                                                        "TipoEvento" : "SOS",
                                                                                        "Accion" : "A",
                                                                                        "Fecha y Hora" : """ + """\"""" + str(
                                                        FECHAORA) + """\"""" + """,
                                                                                        "Direccion" :""" + """\"""" + str(
                                                        latitudconsulta) + "," + str(
                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,
                                                                                        "Latitud" : """ + """\"""" + str(
                                                        latitudconsulta) + """\"""" + """,
                                                                                        "Longitud" : """ + """\"""" + str(
                                                        longitudconsulta) + """\"""" + """
                                                                                        }"""
                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    fin = time.time()
                                                    print(fin - inicio)

                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                elif "V" == arrayCadena[3]:
                                    arrSplit = dato_recibido_en_str.split(",")
                                    baseEstation = int(arrSplit[17])
                                    print("numero de estaciones base: " + str(baseEstation))

                                    if baseEstation >= 1:
                                        MCC1 = int(arrSplit[19])
                                        print("MCC: " + str(MCC1))
                                        MNC1 = int(arrSplit[20])
                                        print("MNC: " + str(MNC1))
                                        if MNC1 == 10:
                                            carrier1 = "CLARO"
                                            print(carrier1)
                                        elif MNC1 == 7:
                                            carrier1 = "MOVISTAR"
                                            print(carrier1)
                                        elif MNC1 == 1:
                                            carrier1 = "ANTEL"
                                            print(carrier1)

                                        locationAreaCode1 = int(arrSplit[21])
                                        print("LAC: " + str(locationAreaCode1))
                                        cellId1 = int(arrSplit[22])
                                        print("CellId: " + str(cellId1))
                                        signalStrength1 = int(arrSplit[23]) - 100

                                    cellTowers = "{" + "\n" + "\"cellId\": " + str(
                                        cellId1) + "," + "\n" + "\"locationAreaCode\": " + str(
                                        locationAreaCode1) + "," + "\n" + "\"mobileCountryCode\": " + str(
                                        MCC1) + "," + "\n" + "\"mobileNetworkCode\": " + str(
                                        MNC1) + "," + "\n" + "\"signalStrength\": " + str(
                                        signalStrength1) + "\n" + "}" + "\n"

                                    wifi = 17 + (6 * int(arrSplit[17])) + 1
                                    wifinumber = int(arrSplit[wifi])
                                    print("Número de redes wifi: " + str(wifinumber))

                                    if wifinumber == 0:
                                        # Insertar el evento en la BD
                                        mydb = mysql.connector.connect(host="localhost", user="root",
                                                                       password="testing",
                                                                       database="telehelp")
                                        mycursor = mydb.cursor()
                                        sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento) VALUES (%s, %s, %s, %s)"
                                        val = (
                                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), respuesta_en_str,
                                            respuesta_en_str[4:14],
                                            "SOS")
                                        mycursor.execute(sql, val)
                                        mydb.commit()
                                        print("Alerta SOS ingresada.")

                                        funcon = mysql.connector.connect(host="localhost", user="root",
                                                                         password="testing",
                                                                         database="telehelp")
                                        funcursor = funcon.cursor()
                                        query = "SELECT * FROM dispositivos WHERE IMEI=%s"
                                        IMEI = str(dato_recibido_en_str[4:14])
                                        print(str(IMEI))
                                        funcursor.execute(query, (IMEI,))

                                        for (userName) in funcursor:
                                            linea = userName[5]
                                            codUsuario = userName[6]
                                            latitudconsulta = userName[9]
                                            longitudconsulta = userName[10]
                                            FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            print(linea)
                                            print(codUsuario)
                                            print(latitudconsulta)
                                            print(longitudconsulta)
                                            print(FECHAORA)

                                        funcursor1 = funcon.cursor()
                                        query1 = "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1"
                                        funcursor1.execute(query1, (IMEI,))

                                        for (servertabla) in funcursor1:
                                            Idevento = servertabla[0]
                                            print(Idevento)

                                            url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                KeyMapsGoogle)
                                            headers = CaseInsensitiveDict()
                                            headers["Content-Length"] = "0"
                                            retries = 3

                                            for n in range(retries):
                                                try:
                                                    response = requests.post(url, headers=headers, verify=False)
                                                    response.raise_for_status()  # 200,201,202,203,204,205,206,207,208,226
                                                    result = response.json()['results'][0]
                                                    geodata = dict()
                                                    geodata['address'] = result['formatted_address']
                                                    print(geodata['address'])

                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"

                                                    data = """{
                                                                                                                                                                    "Id" :""" + str(
                                                        Idevento) + """,
                                                                                                                                                                    "TelefonoAsociado" : """ + """\"""" + str(
                                                        linea) + """\"""" + """,
                                                                                                                                                                    "UsuarioCodigo" :""" + """\"""" + str(
                                                        codUsuario) + """\"""" + """,
                                                                                                                                                                    "TipoEvento" : "SOS",
                                                                                                                                                                    "Accion" : "A",
                                                                                                                                                                    "Fecha y Hora" : """ + """\"""" + str(
                                                        FECHAORA) + """\"""" + """,
                                                                                                                                                                    "Direccion" :""" + """\"""" + str(
                                                        geodata['address']) + """\"""" + """,
                                                                                                                                                                    "Latitud" : """ + """\"""" + str(
                                                        latitudconsulta) + """\"""" + """,
                                                                                                                                                                    "Longitud" : """ + """\"""" + str(
                                                        longitudconsulta) + """\"""" + """
                                                                                                                                                                    }"""

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    fin = time.time()
                                                    print(fin - inicio)

                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                                    break

                                                except HTTPError as exc:
                                                    code = exc.response.status_code

                                                    if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                                411, 412, 413, 414, 415, 422]:
                                                        url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                        headers = CaseInsensitiveDict()
                                                        headers["Accept"] = "application/json"
                                                        headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                        headers["Content-Type"] = "application/json"

                                                        data = """{
                                                                                                                                                                                                                        "Id" :""" + str(
                                                            Idevento) + """,
                                                                                                                                                                                                                        "TelefonoAsociado" : """ + """\"""" + str(
                                                            linea) + """\"""" + """,
                                                                                                                                                                                                                        "UsuarioCodigo" :""" + """\"""" + str(
                                                            codUsuario) + """\"""" + """,
                                                                                                                                                                                                                        "TipoEvento" : "SOS",
                                                                                                                                                                                                                        "Accion" : "A",
                                                                                                                                                                                                                        "Fecha y Hora" : """ + """\"""" + str(
                                                            FECHAORA) + """\"""" + """,
                                                                                                                                                                                                                        "Direccion" :""" + """\"""" + str(
                                                            latitudconsulta) + "," + str(
                                                            longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,
                                                                                                                                                                                                                        "Latitud" : """ + """\"""" + str(
                                                            latitudconsulta) + """\"""" + """,
                                                                                                                                                                                                                        "Longitud" : """ + """\"""" + str(
                                                            longitudconsulta) + """\"""" + """
                                                                                                                                                                                                                        }"""

                                                        print(data)

                                                        print("\n" + str(data) + " " + str(
                                                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                        resp = requests.post(url, headers=headers, data=data,
                                                                             verify=False)
                                                        print(resp.json())
                                                        fin = time.time()
                                                        print(fin - inicio)

                                                        respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                        self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                    elif wifinumber == 1:
                                        redeswifi = "{" + "\n" + "\"macAddress\": " + "\"" + arrSplit[
                                            wifi + 2] + "\"" + "," + "\n" + "\"signalStrength\": " + arrSplit[
                                                        wifi + 3] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}" + "\n"

                                        jsonUbicacion = "{" + "\n" + "\"homeMobileCountryCode\": " + str(
                                            MCC1) + "," + "\n" + "\"homeMobileNetworkCode\": " + str(
                                            MNC1) + "," + "\n" + "\"radioType\":  \"gsm\"" + "," + "\n" + "\"carrier\": " + "\"" + str(
                                            carrier1) + "\"" + "," + "\n" + "\"considerIp\": true" + "," + "\n" "\"cellTowers\": [" + "\n" + cellTowers + "]" + "," + "\n" + "\"wifiAccessPoints\": [" + "\n" + redeswifi + "]" + "\n" + "}" + "\n"
                                        print(jsonUbicacion)

                                        url = "https://www.googleapis.com/geolocation/v1/geolocate?key=" + str(
                                            KeyMapsGoogle)
                                        retries = 3

                                        for n in range(retries):
                                            try:

                                                res = requests.post(url, data=jsonUbicacion, verify=False)

                                                divide = res.text.split(": ")

                                                if "lat" in res.text:
                                                    resplat = divide[2]
                                                    resplat = resplat[0:9]

                                                if "lng" in res.text:
                                                    resplng = divide[3]
                                                    resplng = resplng[0:9]

                                                mydb = mysql.connector.connect(host="localhost", user="root",
                                                                               password="testing",
                                                                               database="telehelp")
                                                mycursor = mydb.cursor()

                                                sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                                val = (
                                                    float(resplat), float(resplng),
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), IMEI)
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("registro de ubicacion actualizado")

                                                sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento) VALUES (%s, %s, %s, %s)"
                                                val = (
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), respuesta_en_str,
                                                    respuesta_en_str[4:14],
                                                    "SOS")
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("Alerta SOS ingresada.")
                                                funcon = mysql.connector.connect(host="localhost", user="root",
                                                                                 password="testing",
                                                                                 database="telehelp")
                                                funcursor = funcon.cursor()
                                                query = ("SELECT * FROM dispositivos WHERE IMEI=%s")
                                                IMEI = str(dato_recibido_en_str[4:14])
                                                print(str(IMEI))
                                                funcursor.execute(query, (IMEI,))

                                                for (userName) in funcursor:
                                                    linea = userName[5]
                                                    codUsuario = userName[6]
                                                    latitudconsulta = userName[9]
                                                    longitudconsulta = userName[10]
                                                    FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                    print(linea)
                                                    print(codUsuario)
                                                    print(latitudconsulta)
                                                    print(longitudconsulta)
                                                    print(FECHAORA)

                                                funcursor1 = funcon.cursor()
                                                query1 = (
                                                    "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1")
                                                funcursor1.execute(query1, (IMEI,))

                                                for (servertabla) in funcursor1:
                                                    Idevento = servertabla[0]
                                                    print(Idevento)

                                                url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                    latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                    KeyMapsGoogle)
                                                headers = CaseInsensitiveDict()
                                                headers["Content-Length"] = "0"
                                                resp = requests.post(url, headers=headers, verify=False)
                                                result = resp.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                                                        "Id" :""" + str(
                                                    Idevento) + """,
                                                                                                                        "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                                                        "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                                                        "TipoEvento" : "SOS",
                                                                                                                        "Accion" : "A",
                                                                                                                        "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                                                        "Direccion" :""" + """\"""" + str(
                                                    geodata['address']) + """\"""" + """,
                                                                                                                        "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                                                        "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                                                        }"""

                                                print(data)

                                                print(str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())
                                                fin = time.time()
                                                print(fin - inicio)
                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))
                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code
                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                            411, 412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"
                                                    data = """{

                                                                                                                                                                                                                    "Id" :""" + str(

                                                        Idevento) + """,

                                                                                                                                                                                                                    "TelefonoAsociado" : """ + """\"""" + str(

                                                        linea) + """\"""" + """,

                                                                                                                                                                                                                    "UsuarioCodigo" :""" + """\"""" + str(

                                                        codUsuario) + """\"""" + """,

                                                                                                                                                                                                                    "TipoEvento" : "SOS",

                                                                                                                                                                                                                    "Accion" : "A",

                                                                                                                                                                                                                    "Fecha y Hora" : """ + """\"""" + str(

                                                        FECHAORA) + """\"""" + """,

                                                                                                                                                                                                                    "Direccion" :""" + """\"""" + str(

                                                        latitudconsulta) + "," + str(

                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,

                                                                                                                                                                                                                    "Latitud" : """ + """\"""" + str(

                                                        latitudconsulta) + """\"""" + """,

                                                                                                                                                                                                                    "Longitud" : """ + """\"""" + str(

                                                        longitudconsulta) + """\"""" + """

                                                                                                                                                                                                                    } """

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    fin = time.time()
                                                    print(fin - inicio)
                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                    elif wifinumber == 2:
                                        redeswifi = "{" + "\n" + "\"macAddress\": " + "\"" + arrSplit[
                                            wifi + 2] + "\"" + "," + "\n" + "\"signalStrength\": " + arrSplit[
                                                        wifi + 3] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 5] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 6] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}" + "\n"
                                        jsonUbicacion = "{" + "\n" + "\"homeMobileCountryCode\": " + str(
                                            MCC1) + "," + "\n" + "\"homeMobileNetworkCode\": " + str(
                                            MNC1) + "," + "\n" + "\"radioType\":  \"gsm\"" + "," + "\n" + "\"carrier\": " + "\"" + str(
                                            carrier1) + "\"" + "," + "\n" + "\"considerIp\": true" + "," + "\n" "\"cellTowers\": [" + "\n" + cellTowers + "]" + "," + "\n" + "\"wifiAccessPoints\": [" + "\n" + redeswifi + "]" + "\n" + "}" + "\n"
                                        print(jsonUbicacion)

                                        url = "https://www.googleapis.com/geolocation/v1/geolocate?key=" + str(
                                            KeyMapsGoogle)
                                        retries = 3

                                        for n in range(retries):
                                            try:

                                                res = requests.post(url, data=jsonUbicacion, verify=False)

                                                divide = res.text.split(": ")

                                                if "lat" in res.text:
                                                    resplat = divide[2]
                                                    resplat = resplat[0:9]

                                                if "lng" in res.text:
                                                    resplng = divide[3]
                                                    resplng = resplng[0:9]

                                                mydb = mysql.connector.connect(host="localhost", user="root",
                                                                               password="testing",
                                                                               database="telehelp")
                                                mycursor = mydb.cursor()

                                                sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                                val = (
                                                    float(resplat), float(resplng),
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), IMEI)
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("registro de ubicacion actualizado")
                                                sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento) VALUES (%s, %s, %s, %s)"
                                                val = (
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), respuesta_en_str,
                                                    respuesta_en_str[4:14],
                                                    "SOS")
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("Alerta SOS ingresada.")
                                                funcon = mysql.connector.connect(host="localhost", user="root",
                                                                                 password="testing",
                                                                                 database="telehelp")
                                                funcursor = funcon.cursor()
                                                query = ("SELECT * FROM dispositivos WHERE IMEI=%s")
                                                IMEI = str(dato_recibido_en_str[4:14])
                                                print(str(IMEI))
                                                funcursor.execute(query, (IMEI,))

                                                for (userName) in funcursor:
                                                    linea = userName[5]
                                                    codUsuario = userName[6]
                                                    latitudconsulta = userName[9]
                                                    longitudconsulta = userName[10]
                                                    FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                    print(linea)
                                                    print(codUsuario)
                                                    print(latitudconsulta)
                                                    print(longitudconsulta)
                                                    print(FECHAORA)

                                                funcursor1 = funcon.cursor()
                                                query1 = (
                                                    "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1")
                                                funcursor1.execute(query1, (IMEI,))

                                                for (servertabla) in funcursor1:
                                                    Idevento = servertabla[0]
                                                    print(Idevento)

                                                url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                    latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                    KeyMapsGoogle)
                                                headers = CaseInsensitiveDict()
                                                headers["Content-Length"] = "0"
                                                resp = requests.post(url, headers=headers, verify=False)
                                                result = resp.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                                                                                                "Id" :""" + str(
                                                    Idevento) + """,
                                                                                                                                                                "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                                                                                                "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                                                                                                "TipoEvento" : "SOS",
                                                                                                                                                                "Accion" : "A",
                                                                                                                                                                "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                                                                                                "Direccion" :""" + """\"""" + str(
                                                    geodata['address']) + """\"""" + """,
                                                                                                                                                                "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                                                                                                "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                                                                                                }"""

                                                print(data)

                                                print(str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())
                                                fin = time.time()
                                                print(fin - inicio)
                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))
                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code
                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                            411, 412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"
                                                    data = """{

                                                                                                                                                                                                                                                            "Id" :""" + str(

                                                        Idevento) + """,

                                                                                                                                                                                                                                                            "TelefonoAsociado" : """ + """\"""" + str(

                                                        linea) + """\"""" + """,

                                                                                                                                                                                                                                                            "UsuarioCodigo" :""" + """\"""" + str(

                                                        codUsuario) + """\"""" + """,

                                                                                                                                                                                                                                                            "TipoEvento" : "SOS",

                                                                                                                                                                                                                                                            "Accion" : "A",

                                                                                                                                                                                                                                                            "Fecha y Hora" : """ + """\"""" + str(

                                                        FECHAORA) + """\"""" + """,

                                                                                                                                                                                                                                                            "Direccion" :""" + """\"""" + str(

                                                        latitudconsulta) + "," + str(

                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,

                                                                                                                                                                                                                                                            "Latitud" : """ + """\"""" + str(

                                                        latitudconsulta) + """\"""" + """,

                                                                                                                                                                                                                                                            "Longitud" : """ + """\"""" + str(

                                                        longitudconsulta) + """\"""" + """

                                                                                                                                                                                                                                                            } """

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    fin = time.time()
                                                    print(fin - inicio)
                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))


                                    elif wifinumber == 3:
                                        redeswifi = "{" + "\n" + "\"macAddress\": " + "\"" + arrSplit[
                                            wifi + 2] + "\"" + "," + "\n" + "\"signalStrength\": " + arrSplit[
                                                        wifi + 3] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " \
                                                    + "\"" + arrSplit[
                                                        wifi + 5] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 6] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 8] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 9] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}" + "\n"
                                        jsonUbicacion = "{" + "\n" + "\"homeMobileCountryCode\": " + str(
                                            MCC1) + "," + "\n" + "\"homeMobileNetworkCode\": " + str(
                                            MNC1) + "," + "\n" + "\"radioType\":  \"gsm\"" + "," + "\n" + "\"carrier\": " + "\"" + str(
                                            carrier1) + "\"" + "," + "\n" + "\"considerIp\": true" + "," + "\n" "\"cellTowers\": [" + "\n" + cellTowers + "]" + "," + "\n" + "\"wifiAccessPoints\": [" + "\n" + redeswifi + "]" + "\n" + "}" + "\n"
                                        print(jsonUbicacion)

                                        url = "https://www.googleapis.com/geolocation/v1/geolocate?key=" + str(
                                            KeyMapsGoogle)
                                        retries = 3

                                        for n in range(retries):
                                            try:

                                                res = requests.post(url, data=jsonUbicacion, verify=False)

                                                divide = res.text.split(": ")

                                                if "lat" in res.text:
                                                    resplat = divide[2]
                                                    resplat = resplat[0:9]

                                                if "lng" in res.text:
                                                    resplng = divide[3]
                                                    resplng = resplng[0:9]

                                                mydb = mysql.connector.connect(host="localhost", user="root",
                                                                               password="testing",
                                                                               database="telehelp")
                                                mycursor = mydb.cursor()

                                                sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                                val = (
                                                    float(resplat), float(resplng),
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), IMEI)
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("registro de ubicacion actualizado")
                                                sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento) VALUES (%s, %s, %s, %s)"
                                                val = (
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), respuesta_en_str,
                                                    respuesta_en_str[4:14],
                                                    "SOS")
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("Alerta SOS ingresada.")
                                                funcon = mysql.connector.connect(host="localhost", user="root",
                                                                                 password="testing",
                                                                                 database="telehelp")
                                                funcursor = funcon.cursor()
                                                query = ("SELECT * FROM dispositivos WHERE IMEI=%s")
                                                IMEI = str(dato_recibido_en_str[4:14])
                                                print(str(IMEI))
                                                funcursor.execute(query, (IMEI,))

                                                for (userName) in funcursor:
                                                    linea = userName[5]
                                                    codUsuario = userName[6]
                                                    latitudconsulta = userName[9]
                                                    longitudconsulta = userName[10]
                                                    FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                    print(linea)
                                                    print(codUsuario)
                                                    print(latitudconsulta)
                                                    print(longitudconsulta)
                                                    print(FECHAORA)

                                                funcursor1 = funcon.cursor()
                                                query1 = (
                                                    "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1")
                                                funcursor1.execute(query1, (IMEI,))

                                                for (servertabla) in funcursor1:
                                                    Idevento = servertabla[0]
                                                    print(Idevento)

                                                url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                    latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                    KeyMapsGoogle)
                                                headers = CaseInsensitiveDict()
                                                headers["Content-Length"] = "0"
                                                resp = requests.post(url, headers=headers, verify=False)
                                                result = resp.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                                                                                                "Id" :""" + str(
                                                    Idevento) + """,
                                                                                                                                                                "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                                                                                                "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                                                                                                "TipoEvento" : "SOS",
                                                                                                                                                                "Accion" : "A",
                                                                                                                                                                "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                                                                                                "Direccion" :""" + """\"""" + str(
                                                    geodata['address']) + """\"""" + """,
                                                                                                                                                                "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                                                                                                "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                                                                                                }"""

                                                print(data)

                                                print(str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())
                                                fin = time.time()
                                                print(fin - inicio)
                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))
                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code
                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                            411, 412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"
                                                    data = """{

                                                                                                                                                                                                                                                            "Id" :""" + str(

                                                        Idevento) + """,

                                                                                                                                                                                                                                                            "TelefonoAsociado" : """ + """\"""" + str(

                                                        linea) + """\"""" + """,

                                                                                                                                                                                                                                                            "UsuarioCodigo" :""" + """\"""" + str(

                                                        codUsuario) + """\"""" + """,

                                                                                                                                                                                                                                                            "TipoEvento" : "SOS",

                                                                                                                                                                                                                                                            "Accion" : "A",

                                                                                                                                                                                                                                                            "Fecha y Hora" : """ + """\"""" + str(

                                                        FECHAORA) + """\"""" + """,

                                                                                                                                                                                                                                                            "Direccion" :""" + """\"""" + str(

                                                        latitudconsulta) + "," + str(

                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,

                                                                                                                                                                                                                                                            "Latitud" : """ + """\"""" + str(

                                                        latitudconsulta) + """\"""" + """,

                                                                                                                                                                                                                                                            "Longitud" : """ + """\"""" + str(

                                                        longitudconsulta) + """\"""" + """

                                                                                                                                                                                                                                                            } """

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    fin = time.time()
                                                    print(fin - inicio)
                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                    elif wifinumber == 4:
                                        redeswifi = "{" + "\n" + "\"macAddress\": " + "\"" + arrSplit[
                                            wifi + 2] + "\"" + "," + "\n" + "\"signalStrength\": " + arrSplit[
                                                        wifi + 3] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 5] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 6] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 8] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 9] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 11] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 12] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}" + "\n"
                                        jsonUbicacion = "{" + "\n" + "\"homeMobileCountryCode\": " + str(
                                            MCC1) + "," + "\n" + "\"homeMobileNetworkCode\": " + str(
                                            MNC1) + "," + "\n" + "\"radioType\":  \"gsm\"" + "," + "\n" + "\"carrier\": " + "\"" + str(
                                            carrier1) + "\"" + "," + "\n" + "\"considerIp\": true" + "," + "\n" "\"cellTowers\": [" + "\n" + cellTowers + "]" + "," + "\n" + "\"wifiAccessPoints\": [" + "\n" + redeswifi + "]" + "\n" + "}" + "\n"
                                        print(jsonUbicacion)

                                        url = "https://www.googleapis.com/geolocation/v1/geolocate?key=" + str(
                                            KeyMapsGoogle)
                                        retries = 3

                                        for n in range(retries):
                                            try:

                                                res = requests.post(url, data=jsonUbicacion, verify=False)

                                                divide = res.text.split(": ")

                                                if "lat" in res.text:
                                                    resplat = divide[2]
                                                    resplat = resplat[0:9]

                                                if "lng" in res.text:
                                                    resplng = divide[3]
                                                    resplng = resplng[0:9]

                                                mydb = mysql.connector.connect(host="localhost", user="root",
                                                                               password="testing",
                                                                               database="telehelp")
                                                mycursor = mydb.cursor()

                                                sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                                val = (
                                                    float(resplat), float(resplng),
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), IMEI)
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("registro de ubicacion actualizado")
                                                sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento) VALUES (%s, %s, %s, %s)"
                                                val = (
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), respuesta_en_str,
                                                    respuesta_en_str[4:14],
                                                    "SOS")
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("Alerta SOS ingresada.")
                                                funcon = mysql.connector.connect(host="localhost", user="root",
                                                                                 password="testing",
                                                                                 database="telehelp")
                                                funcursor = funcon.cursor()
                                                query = ("SELECT * FROM dispositivos WHERE IMEI=%s")
                                                IMEI = str(dato_recibido_en_str[4:14])
                                                print(str(IMEI))
                                                funcursor.execute(query, (IMEI,))

                                                for (userName) in funcursor:
                                                    linea = userName[5]
                                                    codUsuario = userName[6]
                                                    latitudconsulta = userName[9]
                                                    longitudconsulta = userName[10]
                                                    FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                    print(linea)
                                                    print(codUsuario)
                                                    print(latitudconsulta)
                                                    print(longitudconsulta)
                                                    print(FECHAORA)

                                                funcursor1 = funcon.cursor()
                                                query1 = (
                                                    "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1")
                                                funcursor1.execute(query1, (IMEI,))

                                                for (servertabla) in funcursor1:
                                                    Idevento = servertabla[0]
                                                    print(Idevento)

                                                url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                    latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                    KeyMapsGoogle)
                                                headers = CaseInsensitiveDict()
                                                headers["Content-Length"] = "0"
                                                resp = requests.post(url, headers=headers, verify=False)
                                                result = resp.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                                                                                                "Id" :""" + str(
                                                    Idevento) + """,
                                                                                                                                                                "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                                                                                                "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                                                                                                "TipoEvento" : "SOS",
                                                                                                                                                                "Accion" : "A",
                                                                                                                                                                "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                                                                                                "Direccion" :""" + """\"""" + str(
                                                    geodata['address']) + """\"""" + """,
                                                                                                                                                                "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                                                                                                "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                                                                                                }"""

                                                print(data)

                                                print(str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())
                                                fin = time.time()
                                                print(fin - inicio)
                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))
                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code
                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                            411, 412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"
                                                    data = """{

                                                                                                                                                                                                                                                            "Id" :""" + str(

                                                        Idevento) + """,

                                                                                                                                                                                                                                                            "TelefonoAsociado" : """ + """\"""" + str(

                                                        linea) + """\"""" + """,

                                                                                                                                                                                                                                                            "UsuarioCodigo" :""" + """\"""" + str(

                                                        codUsuario) + """\"""" + """,

                                                                                                                                                                                                                                                            "TipoEvento" : "SOS",

                                                                                                                                                                                                                                                            "Accion" : "A",

                                                                                                                                                                                                                                                            "Fecha y Hora" : """ + """\"""" + str(

                                                        FECHAORA) + """\"""" + """,

                                                                                                                                                                                                                                                            "Direccion" :""" + """\"""" + str(

                                                        latitudconsulta) + "," + str(

                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,

                                                                                                                                                                                                                                                            "Latitud" : """ + """\"""" + str(

                                                        latitudconsulta) + """\"""" + """,

                                                                                                                                                                                                                                                            "Longitud" : """ + """\"""" + str(

                                                        longitudconsulta) + """\"""" + """

                                                                                                                                                                                                                                                            } """

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    fin = time.time()
                                                    print(fin - inicio)
                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                    elif wifinumber == 5:
                                        redeswifi = "{" + "\n" + "\"macAddress\": " + "\"" + arrSplit[
                                            wifi + 2] + "\"" + "," + "\n" + "\"signalStrength\": " + arrSplit[
                                                        wifi + 3] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 5] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 6] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 8] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 9] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 11] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 12] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 14] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 15] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}" + "\n"

                                        jsonUbicacion = "{" + "\n" + "\"homeMobileCountryCode\": " + str(
                                            MCC1) + "," + "\n" + "\"homeMobileNetworkCode\": " + str(
                                            MNC1) + "," + "\n" + "\"radioType\":  \"gsm\"" + "," + "\n" + "\"carrier\": " + "\"" + str(
                                            carrier1) + "\"" + "," + "\n" + "\"considerIp\": true" + "," + "\n" "\"cellTowers\": [" + "\n" + cellTowers + "]" + "," + "\n" + "\"wifiAccessPoints\": [" + "\n" + redeswifi + "]" + "\n" + "}" + "\n"
                                        print(jsonUbicacion)

                                        url = "https://www.googleapis.com/geolocation/v1/geolocate?key=" + str(
                                            KeyMapsGoogle)
                                        retries = 3

                                        for n in range(retries):
                                            try:

                                                res = requests.post(url, data=jsonUbicacion, verify=False)

                                                divide = res.text.split(": ")

                                                if "lat" in res.text:
                                                    resplat = divide[2]
                                                    resplat = resplat[0:9]

                                                if "lng" in res.text:
                                                    resplng = divide[3]
                                                    resplng = resplng[0:9]

                                                mydb = mysql.connector.connect(host="localhost", user="root",
                                                                               password="testing",
                                                                               database="telehelp")
                                                mycursor = mydb.cursor()

                                                sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                                val = (
                                                    float(resplat), float(resplng),
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), IMEI)
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("registro de ubicacion actualizado")
                                                sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento) VALUES (%s, %s, %s, %s)"
                                                val = (
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), respuesta_en_str,
                                                    respuesta_en_str[4:14],
                                                    "SOS")
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("Alerta SOS ingresada.")
                                                funcon = mysql.connector.connect(host="localhost", user="root",
                                                                                 password="testing",
                                                                                 database="telehelp")
                                                funcursor = funcon.cursor()
                                                query = ("SELECT * FROM dispositivos WHERE IMEI=%s")
                                                IMEI = str(dato_recibido_en_str[4:14])
                                                print(str(IMEI))
                                                funcursor.execute(query, (IMEI,))

                                                for (userName) in funcursor:
                                                    linea = userName[5]
                                                    codUsuario = userName[6]
                                                    latitudconsulta = userName[9]
                                                    longitudconsulta = userName[10]
                                                    FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                    print(linea)
                                                    print(codUsuario)
                                                    print(latitudconsulta)
                                                    print(longitudconsulta)
                                                    print(FECHAORA)

                                                funcursor1 = funcon.cursor()
                                                query1 = (
                                                    "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1")
                                                funcursor1.execute(query1, (IMEI,))

                                                for (servertabla) in funcursor1:
                                                    Idevento = servertabla[0]
                                                    print(Idevento)

                                                url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                    latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                    KeyMapsGoogle)
                                                headers = CaseInsensitiveDict()
                                                headers["Content-Length"] = "0"
                                                resp = requests.post(url, headers=headers, verify=False)
                                                result = resp.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                                                                                                "Id" :""" + str(
                                                    Idevento) + """,
                                                                                                                                                                "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                                                                                                "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                                                                                                "TipoEvento" : "SOS",
                                                                                                                                                                "Accion" : "A",
                                                                                                                                                                "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                                                                                                "Direccion" :""" + """\"""" + str(
                                                    geodata['address']) + """\"""" + """,
                                                                                                                                                                "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                                                                                                "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                                                                                                }"""

                                                print(data)

                                                print(str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())
                                                fin = time.time()
                                                print(fin - inicio)
                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))
                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code
                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                            411, 412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"
                                                    data = """{

                                                                                                                                                                                                                                                            "Id" :""" + str(

                                                        Idevento) + """,

                                                                                                                                                                                                                                                            "TelefonoAsociado" : """ + """\"""" + str(

                                                        linea) + """\"""" + """,

                                                                                                                                                                                                                                                            "UsuarioCodigo" :""" + """\"""" + str(

                                                        codUsuario) + """\"""" + """,

                                                                                                                                                                                                                                                            "TipoEvento" : "SOS",

                                                                                                                                                                                                                                                            "Accion" : "A",

                                                                                                                                                                                                                                                            "Fecha y Hora" : """ + """\"""" + str(

                                                        FECHAORA) + """\"""" + """,

                                                                                                                                                                                                                                                            "Direccion" :""" + """\"""" + str(

                                                        latitudconsulta) + "," + str(

                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,

                                                                                                                                                                                                                                                            "Latitud" : """ + """\"""" + str(

                                                        latitudconsulta) + """\"""" + """,

                                                                                                                                                                                                                                                            "Longitud" : """ + """\"""" + str(

                                                        longitudconsulta) + """\"""" + """

                                                                                                                                                                                                                                                            } """

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    fin = time.time()
                                                    print(fin - inicio)
                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                            elif b'00200000' in mensajeEncript or b'00020001' in mensajeEncript:
                                print("Se recibió Caída")
                                inicio = time.time()
                                dato_recibido_en_str = mensajeEncript.decode()
                                respuesta_en_str = "{}".format(dato_recibido_en_str[0:14] + "*0002*AL]")
                                print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " Recibido desde el cliente:",
                                      str(mensajeEncript))

                                respuesta_en_str6 = "{}".format(
                                    dato_recibido_en_str[0:14] + "*0002*CR]")  # [SG*5678901234*0002*CR]
                                respuesta_en_bytes6 = bytes(respuesta_en_str6, encoding='utf8')
                                mensajeResp6 = self.encripta(respuesta_en_bytes6)
                                self.csocket.send(mensajeResp6)

                                print(str(mensajeEncript) + "\n")

                                IMEI = dato_recibido_en_str[4:14]
                                print(IMEI)
                                cadena = dato_recibido_en_str[20:]
                                arrayCadena = cadena.split(",")
                                Alarmas = arrayCadena[16]
                                print(arrayCadena[3])  # si es A o V
                                if "A" == arrayCadena[3]:
                                    if arrayCadena[5] == "S":
                                        latitud = "-" + arrayCadena[4]
                                    else:
                                        latitud = arrayCadena[4]

                                    if arrayCadena[7] == "W":
                                        longitud = "-" + arrayCadena[6]
                                    else:
                                        longitud = arrayCadena[6]

                                    # se actualiza la ubicación en la BD
                                    mydb = mysql.connector.connect(host="localhost", user="root",
                                                                   password="testing",
                                                                   database="telehelp")
                                    mycursor = mydb.cursor()

                                    sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                    val = (
                                        float(latitud), float(longitud), datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        IMEI)
                                    mycursor.execute(sql, val)
                                    mydb.commit()
                                    print("registro de ubicacion actualizado")

                                    # Insertar el evento en la BD
                                    sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento) VALUES (%s, %s, %s, %s)"
                                    val = (
                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'), respuesta_en_str,
                                        respuesta_en_str[4:14],
                                        "Caída")
                                    mycursor.execute(sql, val)
                                    mydb.commit()
                                    print("Alerta Caída ingresada.")

                                    funcon = mysql.connector.connect(host="localhost", user="root",
                                                                     password="testing",
                                                                     database="telehelp")
                                    funcursor = funcon.cursor()
                                    query = "SELECT * FROM dispositivos WHERE IMEI=%s"
                                    IMEI = str(dato_recibido_en_str[4:14])
                                    print(str(IMEI))
                                    funcursor.execute(query, (IMEI,))

                                    for (userName) in funcursor:
                                        linea = userName[5]
                                        codUsuario = userName[6]
                                        latitudconsulta = userName[9]
                                        longitudconsulta = userName[10]
                                        FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        print(linea)
                                        print(codUsuario)
                                        print(latitudconsulta)
                                        print(longitudconsulta)
                                        print(FECHAORA)

                                    funcursor1 = funcon.cursor()
                                    query1 = "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1"
                                    funcursor1.execute(query1, (IMEI,))

                                    for (servertabla) in funcursor1:
                                        Idevento = servertabla[0]
                                        print(Idevento)

                                        url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                            latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                            KeyMapsGoogle)
                                        headers = CaseInsensitiveDict()
                                        headers["Content-Length"] = "0"
                                        retries = 3

                                        for n in range(retries):
                                            try:
                                                response = requests.post(url, headers=headers, verify=False)
                                                response.raise_for_status()  # 200,201,202,203,204,205,206,207,208,226
                                                result = response.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                                                            "Id" :""" + str(
                                                    Idevento) + """,
                                                                                                                            "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                                                            "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                                                            "TipoEvento" : "CAIDA",
                                                                                                                            "Accion" : "A",
                                                                                                                            "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                                                            "Direccion" :""" + """\"""" + str(
                                                    geodata['address']) + """\"""" + """,
                                                                                                                            "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                                                            "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                                                            }"""

                                                print(data)

                                                print(str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())
                                                fin = time.time()
                                                print(fin - inicio)
                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code

                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411,
                                                            412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"

                                                    data = """{
                                                                                                                                                                                "Id" :""" + str(
                                                        Idevento) + """,
                                                                                                                                                                                "TelefonoAsociado" : """ + """\"""" + str(
                                                        linea) + """\"""" + """,
                                                                                                                                                                                "UsuarioCodigo" :""" + """\"""" + str(
                                                        codUsuario) + """\"""" + """,
                                                                                                                                                                                "TipoEvento" : "CAIDA",
                                                                                                                                                                                "Accion" : "A",
                                                                                                                                                                                "Fecha y Hora" : """ + """\"""" + str(
                                                        FECHAORA) + """\"""" + """,
                                                                                                                                                                                "Direccion" :""" + """\"""" + str(
                                                        latitudconsulta) + "," + str(
                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,
                                                                                                                                                                                "Latitud" : """ + """\"""" + str(
                                                        latitudconsulta) + """\"""" + """,
                                                                                                                                                                                "Longitud" : """ + """\"""" + str(
                                                        longitudconsulta) + """\"""" + """
                                                                                                                                                                                }"""

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    fin = time.time()
                                                    print(fin - inicio)
                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                elif "V" == arrayCadena[3]:
                                    arrSplit = dato_recibido_en_str.split(",")
                                    baseEstation = int(arrSplit[17])
                                    print("numero de estaciones base: " + str(baseEstation))

                                    if baseEstation >= 1:
                                        MCC1 = int(arrSplit[19])
                                        print("MCC: " + str(MCC1))
                                        MNC1 = int(arrSplit[20])
                                        print("MNC: " + str(MNC1))
                                        if MNC1 == 10:
                                            carrier1 = "CLARO"
                                            print(carrier1)
                                        elif MNC1 == 7:
                                            carrier1 = "MOVISTAR"
                                            print(carrier1)
                                        elif MNC1 == 1:
                                            carrier1 = "ANTEL"
                                            print(carrier1)

                                        locationAreaCode1 = int(arrSplit[21])
                                        print("LAC: " + str(locationAreaCode1))
                                        cellId1 = int(arrSplit[22])
                                        print("CellId: " + str(cellId1))
                                        signalStrength1 = int(arrSplit[23]) - 100

                                    cellTowers = "{" + "\n" + "\"cellId\": " + str(
                                        cellId1) + "," + "\n" + "\"locationAreaCode\": " + str(
                                        locationAreaCode1) + "," + "\n" + "\"mobileCountryCode\": " + str(
                                        MCC1) + "," + "\n" + "\"mobileNetworkCode\": " + str(
                                        MNC1) + "," + "\n" + "\"signalStrength\": " + str(
                                        signalStrength1) + "\n" + "}" + "\n"

                                    wifi = 17 + (6 * int(arrSplit[17])) + 1
                                    wifinumber = int(arrSplit[wifi])
                                    print("Número de redes wifi: " + str(wifinumber))

                                    if wifinumber == 0:
                                        # Insertar el evento en la BD
                                        mydb = mysql.connector.connect(host="localhost", user="root",
                                                                       password="testing",
                                                                       database="telehelp")
                                        mycursor = mydb.cursor()
                                        sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento) VALUES (%s, %s, %s, %s)"
                                        val = (
                                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), respuesta_en_str,
                                            respuesta_en_str[4:14],
                                            "Caída")
                                        mycursor.execute(sql, val)
                                        mydb.commit()
                                        print("Alerta Caída ingresada.")

                                        funcon = mysql.connector.connect(host="localhost", user="root",
                                                                         password="testing",
                                                                         database="telehelp")
                                        funcursor = funcon.cursor()
                                        query = "SELECT * FROM dispositivos WHERE IMEI=%s"
                                        IMEI = str(dato_recibido_en_str[4:14])
                                        print(str(IMEI))
                                        funcursor.execute(query, (IMEI,))

                                        for (userName) in funcursor:
                                            linea = userName[5]
                                            codUsuario = userName[6]
                                            latitudconsulta = userName[9]
                                            longitudconsulta = userName[10]
                                            FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            print(linea)
                                            print(codUsuario)
                                            print(latitudconsulta)
                                            print(longitudconsulta)
                                            print(FECHAORA)

                                        funcursor1 = funcon.cursor()
                                        query1 = "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1"
                                        funcursor1.execute(query1, (IMEI,))

                                        for (servertabla) in funcursor1:
                                            Idevento = servertabla[0]
                                            print(Idevento)

                                            url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                KeyMapsGoogle)
                                            headers = CaseInsensitiveDict()
                                            headers["Content-Length"] = "0"
                                            retries = 3

                                            for n in range(retries):
                                                try:
                                                    response = requests.post(url, headers=headers, verify=False)
                                                    response.raise_for_status()  # 200,201,202,203,204,205,206,207,208,226
                                                    result = response.json()['results'][0]
                                                    geodata = dict()
                                                    geodata['address'] = result['formatted_address']
                                                    print(geodata['address'])

                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"

                                                    data = """{
                                                                                                                                                                    "Id" :""" + str(
                                                        Idevento) + """,
                                                                                                                                                                    "TelefonoAsociado" : """ + """\"""" + str(
                                                        linea) + """\"""" + """,
                                                                                                                                                                    "UsuarioCodigo" :""" + """\"""" + str(
                                                        codUsuario) + """\"""" + """,
                                                                                                                                                                    "TipoEvento" : "CAIDA",
                                                                                                                                                                    "Accion" : "A",
                                                                                                                                                                    "Fecha y Hora" : """ + """\"""" + str(
                                                        FECHAORA) + """\"""" + """,
                                                                                                                                                                    "Direccion" :""" + """\"""" + str(
                                                        geodata['address']) + """\"""" + """,
                                                                                                                                                                    "Latitud" : """ + """\"""" + str(
                                                        latitudconsulta) + """\"""" + """,
                                                                                                                                                                    "Longitud" : """ + """\"""" + str(
                                                        longitudconsulta) + """\"""" + """
                                                                                                                                                                    }"""

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    fin = time.time()
                                                    print(fin - inicio)

                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                                    break

                                                except HTTPError as exc:
                                                    code = exc.response.status_code

                                                    if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                                411, 412, 413, 414, 415, 422]:
                                                        url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                        headers = CaseInsensitiveDict()
                                                        headers["Accept"] = "application/json"
                                                        headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                        headers["Content-Type"] = "application/json"

                                                        data = """{
                                                                                                                                                                                                                        "Id" :""" + str(
                                                            Idevento) + """,
                                                                                                                                                                                                                        "TelefonoAsociado" : """ + """\"""" + str(
                                                            linea) + """\"""" + """,
                                                                                                                                                                                                                        "UsuarioCodigo" :""" + """\"""" + str(
                                                            codUsuario) + """\"""" + """,
                                                                                                                                                                                                                        "TipoEvento" : "CAIDA",
                                                                                                                                                                                                                        "Accion" : "A",
                                                                                                                                                                                                                        "Fecha y Hora" : """ + """\"""" + str(
                                                            FECHAORA) + """\"""" + """,
                                                                                                                                                                                                                        "Direccion" :""" + """\"""" + str(
                                                            latitudconsulta) + "," + str(
                                                            longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,
                                                                                                                                                                                                                        "Latitud" : """ + """\"""" + str(
                                                            latitudconsulta) + """\"""" + """,
                                                                                                                                                                                                                        "Longitud" : """ + """\"""" + str(
                                                            longitudconsulta) + """\"""" + """
                                                                                                                                                                                                                        }"""

                                                        print(data)

                                                        print(str(data) + " " + str(
                                                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                        resp = requests.post(url, headers=headers, data=data,
                                                                             verify=False)
                                                        print(resp.json())
                                                        fin = time.time()
                                                        print(fin - inicio)

                                                        respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                        self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                    elif wifinumber == 1:
                                        redeswifi = "{" + "\n" + "\"macAddress\": " + "\"" + arrSplit[
                                            wifi + 2] + "\"" + "," + "\n" + "\"signalStrength\": " + arrSplit[
                                                        wifi + 3] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}" + "\n"

                                        jsonUbicacion = "{" + "\n" + "\"homeMobileCountryCode\": " + str(
                                            MCC1) + "," + "\n" + "\"homeMobileNetworkCode\": " + str(
                                            MNC1) + "," + "\n" + "\"radioType\":  \"gsm\"" + "," + "\n" + "\"carrier\": " + "\"" + str(
                                            carrier1) + "\"" + "," + "\n" + "\"considerIp\": true" + "," + "\n" "\"cellTowers\": [" + "\n" + cellTowers + "]" + "," + "\n" + "\"wifiAccessPoints\": [" + "\n" + redeswifi + "]" + "\n" + "}" + "\n"
                                        print(jsonUbicacion)

                                        url = "https://www.googleapis.com/geolocation/v1/geolocate?key=" + str(
                                            KeyMapsGoogle)
                                        retries = 3

                                        for n in range(retries):
                                            try:

                                                res = requests.post(url, data=jsonUbicacion, verify=False)

                                                divide = res.text.split(": ")

                                                if "lat" in res.text:
                                                    resplat = divide[2]
                                                    resplat = resplat[0:9]

                                                if "lng" in res.text:
                                                    resplng = divide[3]
                                                    resplng = resplng[0:9]

                                                mydb = mysql.connector.connect(host="localhost", user="root",
                                                                               password="testing",
                                                                               database="telehelp")
                                                mycursor = mydb.cursor()

                                                sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                                val = (
                                                    float(resplat), float(resplng),
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), IMEI)
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("registro de ubicacion actualizado")
                                                sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento) VALUES (%s, %s, %s, %s)"
                                                val = (
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), respuesta_en_str,
                                                    respuesta_en_str[4:14],
                                                    "Caída")
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("Alerta Caída ingresada.")
                                                funcon = mysql.connector.connect(host="localhost", user="root",
                                                                                 password="testing",
                                                                                 database="telehelp")
                                                funcursor = funcon.cursor()
                                                query = ("SELECT * FROM dispositivos WHERE IMEI=%s")
                                                IMEI = str(dato_recibido_en_str[4:14])
                                                print(str(IMEI))
                                                funcursor.execute(query, (IMEI,))

                                                for (userName) in funcursor:
                                                    linea = userName[5]
                                                    codUsuario = userName[6]
                                                    latitudconsulta = userName[9]
                                                    longitudconsulta = userName[10]
                                                    FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                    print(linea)
                                                    print(codUsuario)
                                                    print(latitudconsulta)
                                                    print(longitudconsulta)
                                                    print(FECHAORA)

                                                funcursor1 = funcon.cursor()
                                                query1 = (
                                                    "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1")
                                                funcursor1.execute(query1, (IMEI,))

                                                for (servertabla) in funcursor1:
                                                    Idevento = servertabla[0]
                                                    print(Idevento)

                                                url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                    latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                    KeyMapsGoogle)
                                                headers = CaseInsensitiveDict()
                                                headers["Content-Length"] = "0"
                                                resp = requests.post(url, headers=headers, verify=False)
                                                result = resp.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                                                        "Id" :""" + str(
                                                    Idevento) + """,
                                                                                                                        "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                                                        "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                                                        "TipoEvento" : "CAIDA",
                                                                                                                        "Accion" : "A",
                                                                                                                        "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                                                        "Direccion" :""" + """\"""" + str(
                                                    geodata['address']) + """\"""" + """,
                                                                                                                        "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                                                        "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                                                        }"""

                                                print(data)

                                                print(str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())
                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))
                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code
                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                            411, 412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"
                                                    data = """{

                                                                                                                                                                                                                    "Id" :""" + str(

                                                        Idevento) + """,

                                                                                                                                                                                                                    "TelefonoAsociado" : """ + """\"""" + str(

                                                        linea) + """\"""" + """,

                                                                                                                                                                                                                    "UsuarioCodigo" :""" + """\"""" + str(

                                                        codUsuario) + """\"""" + """,

                                                                                                                                                                                                                    "TipoEvento" : "CAIDA",

                                                                                                                                                                                                                    "Accion" : "A",

                                                                                                                                                                                                                    "Fecha y Hora" : """ + """\"""" + str(

                                                        FECHAORA) + """\"""" + """,

                                                                                                                                                                                                                    "Direccion" :""" + """\"""" + str(

                                                        latitudconsulta) + "," + str(

                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,

                                                                                                                                                                                                                    "Latitud" : """ + """\"""" + str(

                                                        latitudconsulta) + """\"""" + """,

                                                                                                                                                                                                                    "Longitud" : """ + """\"""" + str(

                                                        longitudconsulta) + """\"""" + """

                                                                                                                                                                                                                    } """

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    fin = time.time()
                                                    print(fin - inicio)
                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                    elif wifinumber == 2:
                                        redeswifi = "{" + "\n" + "\"macAddress\": " + "\"" + arrSplit[
                                            wifi + 2] + "\"" + "," + "\n" + "\"signalStrength\": " + arrSplit[
                                                        wifi + 3] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 5] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 6] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}" + "\n"
                                        jsonUbicacion = "{" + "\n" + "\"homeMobileCountryCode\": " + str(
                                            MCC1) + "," + "\n" + "\"homeMobileNetworkCode\": " + str(
                                            MNC1) + "," + "\n" + "\"radioType\":  \"gsm\"" + "," + "\n" + "\"carrier\": " + "\"" + str(
                                            carrier1) + "\"" + "," + "\n" + "\"considerIp\": true" + "," + "\n" "\"cellTowers\": [" + "\n" + cellTowers + "]" + "," + "\n" + "\"wifiAccessPoints\": [" + "\n" + redeswifi + "]" + "\n" + "}" + "\n"
                                        print(jsonUbicacion)

                                        url = "https://www.googleapis.com/geolocation/v1/geolocate?key=" + str(
                                            KeyMapsGoogle)
                                        retries = 3

                                        for n in range(retries):
                                            try:

                                                res = requests.post(url, data=jsonUbicacion, verify=False)

                                                divide = res.text.split(": ")

                                                if "lat" in res.text:
                                                    resplat = divide[2]
                                                    resplat = resplat[0:9]

                                                if "lng" in res.text:
                                                    resplng = divide[3]
                                                    resplng = resplng[0:9]

                                                mydb = mysql.connector.connect(host="localhost", user="root",
                                                                               password="testing",
                                                                               database="telehelp")
                                                mycursor = mydb.cursor()

                                                sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                                val = (
                                                    float(resplat), float(resplng),
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), IMEI)
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("registro de ubicacion actualizado")
                                                sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento) VALUES (%s, %s, %s, %s)"
                                                val = (
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), respuesta_en_str,
                                                    respuesta_en_str[4:14],
                                                    "Caída")
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("Alerta Caída ingresada.")
                                                funcon = mysql.connector.connect(host="localhost", user="root",
                                                                                 password="testing",
                                                                                 database="telehelp")
                                                funcursor = funcon.cursor()
                                                query = ("SELECT * FROM dispositivos WHERE IMEI=%s")
                                                IMEI = str(dato_recibido_en_str[4:14])
                                                print(str(IMEI))
                                                funcursor.execute(query, (IMEI,))

                                                for (userName) in funcursor:
                                                    linea = userName[5]
                                                    codUsuario = userName[6]
                                                    latitudconsulta = userName[9]
                                                    longitudconsulta = userName[10]
                                                    FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                    print(linea)
                                                    print(codUsuario)
                                                    print(latitudconsulta)
                                                    print(longitudconsulta)
                                                    print(FECHAORA)

                                                funcursor1 = funcon.cursor()
                                                query1 = (
                                                    "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1")
                                                funcursor1.execute(query1, (IMEI,))

                                                for (servertabla) in funcursor1:
                                                    Idevento = servertabla[0]
                                                    print(Idevento)

                                                url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                    latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                    KeyMapsGoogle)
                                                headers = CaseInsensitiveDict()
                                                headers["Content-Length"] = "0"
                                                resp = requests.post(url, headers=headers, verify=False)
                                                result = resp.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                                                                                                "Id" :""" + str(
                                                    Idevento) + """,
                                                                                                                                                                "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                                                                                                "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                                                                                                "TipoEvento" : "CAIDA",
                                                                                                                                                                "Accion" : "A",
                                                                                                                                                                "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                                                                                                "Direccion" :""" + """\"""" + str(
                                                    geodata['address']) + """\"""" + """,
                                                                                                                                                                "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                                                                                                "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                                                                                                }"""

                                                print(data)

                                                print(str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())
                                                fin = time.time()
                                                print(fin - inicio)
                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))
                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code
                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                            411, 412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"
                                                    data = """{

                                                                                                                                                                                                                                                            "Id" :""" + str(

                                                        Idevento) + """,

                                                                                                                                                                                                                                                            "TelefonoAsociado" : """ + """\"""" + str(

                                                        linea) + """\"""" + """,

                                                                                                                                                                                                                                                            "UsuarioCodigo" :""" + """\"""" + str(

                                                        codUsuario) + """\"""" + """,

                                                                                                                                                                                                                                                            "TipoEvento" : "CAIDA",

                                                                                                                                                                                                                                                            "Accion" : "A",

                                                                                                                                                                                                                                                            "Fecha y Hora" : """ + """\"""" + str(

                                                        FECHAORA) + """\"""" + """,

                                                                                                                                                                                                                                                            "Direccion" :""" + """\"""" + str(

                                                        latitudconsulta) + "," + str(

                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,

                                                                                                                                                                                                                                                            "Latitud" : """ + """\"""" + str(

                                                        latitudconsulta) + """\"""" + """,

                                                                                                                                                                                                                                                            "Longitud" : """ + """\"""" + str(

                                                        longitudconsulta) + """\"""" + """

                                                                                                                                                                                                                                                            } """

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    fin = time.time()
                                                    print(fin - inicio)
                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))


                                    elif wifinumber == 3:
                                        redeswifi = "{" + "\n" + "\"macAddress\": " + "\"" + arrSplit[
                                            wifi + 2] + "\"" + "," + "\n" + "\"signalStrength\": " + arrSplit[
                                                        wifi + 3] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " \
                                                    + "\"" + arrSplit[
                                                        wifi + 5] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 6] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 8] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 9] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}" + "\n"
                                        jsonUbicacion = "{" + "\n" + "\"homeMobileCountryCode\": " + str(
                                            MCC1) + "," + "\n" + "\"homeMobileNetworkCode\": " + str(
                                            MNC1) + "," + "\n" + "\"radioType\":  \"gsm\"" + "," + "\n" + "\"carrier\": " + "\"" + str(
                                            carrier1) + "\"" + "," + "\n" + "\"considerIp\": true" + "," + "\n" "\"cellTowers\": [" + "\n" + cellTowers + "]" + "," + "\n" + "\"wifiAccessPoints\": [" + "\n" + redeswifi + "]" + "\n" + "}" + "\n"
                                        print(jsonUbicacion)

                                        url = "https://www.googleapis.com/geolocation/v1/geolocate?key=" + str(
                                            KeyMapsGoogle)
                                        retries = 3

                                        for n in range(retries):
                                            try:

                                                res = requests.post(url, data=jsonUbicacion, verify=False)

                                                divide = res.text.split(": ")

                                                if "lat" in res.text:
                                                    resplat = divide[2]
                                                    resplat = resplat[0:9]

                                                if "lng" in res.text:
                                                    resplng = divide[3]
                                                    resplng = resplng[0:9]

                                                mydb = mysql.connector.connect(host="localhost", user="root",
                                                                               password="testing",
                                                                               database="telehelp")
                                                mycursor = mydb.cursor()

                                                sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                                val = (
                                                    float(resplat), float(resplng),
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), IMEI)
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("registro de ubicacion actualizado")
                                                sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento) VALUES (%s, %s, %s, %s)"
                                                val = (
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), respuesta_en_str,
                                                    respuesta_en_str[4:14],
                                                    "Caída")
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("Alerta Caída ingresada.")
                                                funcon = mysql.connector.connect(host="localhost", user="root",
                                                                                 password="testing",
                                                                                 database="telehelp")
                                                funcursor = funcon.cursor()
                                                query = ("SELECT * FROM dispositivos WHERE IMEI=%s")
                                                IMEI = str(dato_recibido_en_str[4:14])
                                                print(str(IMEI))
                                                funcursor.execute(query, (IMEI,))

                                                for (userName) in funcursor:
                                                    linea = userName[5]
                                                    codUsuario = userName[6]
                                                    latitudconsulta = userName[9]
                                                    longitudconsulta = userName[10]
                                                    FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                    print(linea)
                                                    print(codUsuario)
                                                    print(latitudconsulta)
                                                    print(longitudconsulta)
                                                    print(FECHAORA)

                                                funcursor1 = funcon.cursor()
                                                query1 = (
                                                    "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1")
                                                funcursor1.execute(query1, (IMEI,))

                                                for (servertabla) in funcursor1:
                                                    Idevento = servertabla[0]
                                                    print(Idevento)

                                                url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                    latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                    KeyMapsGoogle)
                                                headers = CaseInsensitiveDict()
                                                headers["Content-Length"] = "0"
                                                resp = requests.post(url, headers=headers, verify=False)
                                                result = resp.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                                                                                                "Id" :""" + str(
                                                    Idevento) + """,
                                                                                                                                                                "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                                                                                                "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                                                                                                "TipoEvento" : "CAIDA",
                                                                                                                                                                "Accion" : "A",
                                                                                                                                                                "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                                                                                                "Direccion" :""" + """\"""" + str(
                                                    geodata['address']) + """\"""" + """,
                                                                                                                                                                "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                                                                                                "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                                                                                                }"""

                                                print(data)

                                                print(str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())
                                                fin = time.time()
                                                print(fin - inicio)
                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))
                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code
                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                            411, 412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"
                                                    data = """{

                                                                                                                                                                                                                                                            "Id" :""" + str(

                                                        Idevento) + """,

                                                                                                                                                                                                                                                            "TelefonoAsociado" : """ + """\"""" + str(

                                                        linea) + """\"""" + """,

                                                                                                                                                                                                                                                            "UsuarioCodigo" :""" + """\"""" + str(

                                                        codUsuario) + """\"""" + """,

                                                                                                                                                                                                                                                            "TipoEvento" : "CAIDA",

                                                                                                                                                                                                                                                            "Accion" : "A",

                                                                                                                                                                                                                                                            "Fecha y Hora" : """ + """\"""" + str(

                                                        FECHAORA) + """\"""" + """,

                                                                                                                                                                                                                                                            "Direccion" :""" + """\"""" + str(

                                                        latitudconsulta) + "," + str(

                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,

                                                                                                                                                                                                                                                            "Latitud" : """ + """\"""" + str(

                                                        latitudconsulta) + """\"""" + """,

                                                                                                                                                                                                                                                            "Longitud" : """ + """\"""" + str(

                                                        longitudconsulta) + """\"""" + """

                                                                                                                                                                                                                                                            } """

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    fin = time.time()
                                                    print(fin - inicio)
                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                    elif wifinumber == 4:
                                        redeswifi = "{" + "\n" + "\"macAddress\": " + "\"" + arrSplit[
                                            wifi + 2] + "\"" + "," + "\n" + "\"signalStrength\": " + arrSplit[
                                                        wifi + 3] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 5] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 6] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 8] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 9] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 11] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 12] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}" + "\n"
                                        jsonUbicacion = "{" + "\n" + "\"homeMobileCountryCode\": " + str(
                                            MCC1) + "," + "\n" + "\"homeMobileNetworkCode\": " + str(
                                            MNC1) + "," + "\n" + "\"radioType\":  \"gsm\"" + "," + "\n" + "\"carrier\": " + "\"" + str(
                                            carrier1) + "\"" + "," + "\n" + "\"considerIp\": true" + "," + "\n" "\"cellTowers\": [" + "\n" + cellTowers + "]" + "," + "\n" + "\"wifiAccessPoints\": [" + "\n" + redeswifi + "]" + "\n" + "}" + "\n"
                                        print(jsonUbicacion)

                                        url = "https://www.googleapis.com/geolocation/v1/geolocate?key=" + str(
                                            KeyMapsGoogle)
                                        retries = 3

                                        for n in range(retries):
                                            try:

                                                res = requests.post(url, data=jsonUbicacion, verify=False)

                                                divide = res.text.split(": ")

                                                if "lat" in res.text:
                                                    resplat = divide[2]
                                                    resplat = resplat[0:9]

                                                if "lng" in res.text:
                                                    resplng = divide[3]
                                                    resplng = resplng[0:9]

                                                mydb = mysql.connector.connect(host="localhost", user="root",
                                                                               password="testing",
                                                                               database="telehelp")
                                                mycursor = mydb.cursor()

                                                sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                                val = (
                                                    float(resplat), float(resplng),
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), IMEI)
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("registro de ubicacion actualizado")
                                                sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento) VALUES (%s, %s, %s, %s)"
                                                val = (
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), respuesta_en_str,
                                                    respuesta_en_str[4:14],
                                                    "Caída")
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("Alerta Caída ingresada.")
                                                funcon = mysql.connector.connect(host="localhost", user="root",
                                                                                 password="testing",
                                                                                 database="telehelp")
                                                funcursor = funcon.cursor()
                                                query = ("SELECT * FROM dispositivos WHERE IMEI=%s")
                                                IMEI = str(dato_recibido_en_str[4:14])
                                                print(str(IMEI))
                                                funcursor.execute(query, (IMEI,))

                                                for (userName) in funcursor:
                                                    linea = userName[5]
                                                    codUsuario = userName[6]
                                                    latitudconsulta = userName[9]
                                                    longitudconsulta = userName[10]
                                                    FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                    print(linea)
                                                    print(codUsuario)
                                                    print(latitudconsulta)
                                                    print(longitudconsulta)
                                                    print(FECHAORA)

                                                funcursor1 = funcon.cursor()
                                                query1 = (
                                                    "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1")
                                                funcursor1.execute(query1, (IMEI,))

                                                for (servertabla) in funcursor1:
                                                    Idevento = servertabla[0]
                                                    print(Idevento)

                                                url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                    latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                    KeyMapsGoogle)
                                                headers = CaseInsensitiveDict()
                                                headers["Content-Length"] = "0"
                                                resp = requests.post(url, headers=headers, verify=False)
                                                result = resp.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                                                                                                "Id" :""" + str(
                                                    Idevento) + """,
                                                                                                                                                                "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                                                                                                "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                                                                                                "TipoEvento" : "CAIDA",
                                                                                                                                                                "Accion" : "A",
                                                                                                                                                                "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                                                                                                "Direccion" :""" + """\"""" + str(
                                                    geodata['address']) + """\"""" + """,
                                                                                                                                                                "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                                                                                                "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                                                                                                }"""

                                                print(data)

                                                print(str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())
                                                fin = time.time()
                                                print(fin - inicio)
                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))
                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code
                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                            411, 412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"
                                                    data = """{

                                                                                                                                                                                                                                                            "Id" :""" + str(

                                                        Idevento) + """,

                                                                                                                                                                                                                                                            "TelefonoAsociado" : """ + """\"""" + str(

                                                        linea) + """\"""" + """,

                                                                                                                                                                                                                                                            "UsuarioCodigo" :""" + """\"""" + str(

                                                        codUsuario) + """\"""" + """,

                                                                                                                                                                                                                                                            "TipoEvento" : "CAIDA",

                                                                                                                                                                                                                                                            "Accion" : "A",

                                                                                                                                                                                                                                                            "Fecha y Hora" : """ + """\"""" + str(

                                                        FECHAORA) + """\"""" + """,

                                                                                                                                                                                                                                                            "Direccion" :""" + """\"""" + str(

                                                        latitudconsulta) + "," + str(

                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,

                                                                                                                                                                                                                                                            "Latitud" : """ + """\"""" + str(

                                                        latitudconsulta) + """\"""" + """,

                                                                                                                                                                                                                                                            "Longitud" : """ + """\"""" + str(

                                                        longitudconsulta) + """\"""" + """

                                                                                                                                                                                                                                                            } """

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    fin = time.time()
                                                    print(fin - inicio)
                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                    elif wifinumber == 5:
                                        redeswifi = "{" + "\n" + "\"macAddress\": " + "\"" + arrSplit[
                                            wifi + 2] + "\"" + "," + "\n" + "\"signalStrength\": " + arrSplit[
                                                        wifi + 3] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 5] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 6] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 8] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 9] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 11] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 12] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 14] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 15] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}" + "\n"

                                        jsonUbicacion = "{" + "\n" + "\"homeMobileCountryCode\": " + str(
                                            MCC1) + "," + "\n" + "\"homeMobileNetworkCode\": " + str(
                                            MNC1) + "," + "\n" + "\"radioType\":  \"gsm\"" + "," + "\n" + "\"carrier\": " + "\"" + str(
                                            carrier1) + "\"" + "," + "\n" + "\"considerIp\": true" + "," + "\n" "\"cellTowers\": [" + "\n" + cellTowers + "]" + "," + "\n" + "\"wifiAccessPoints\": [" + "\n" + redeswifi + "]" + "\n" + "}" + "\n"
                                        print(jsonUbicacion)

                                        url = "https://www.googleapis.com/geolocation/v1/geolocate?key=" + str(
                                            KeyMapsGoogle)
                                        retries = 3

                                        for n in range(retries):
                                            try:

                                                res = requests.post(url, data=jsonUbicacion, verify=False)

                                                divide = res.text.split(": ")

                                                if "lat" in res.text:
                                                    resplat = divide[2]
                                                    resplat = resplat[0:9]

                                                if "lng" in res.text:
                                                    resplng = divide[3]
                                                    resplng = resplng[0:9]

                                                mydb = mysql.connector.connect(host="localhost", user="root",
                                                                               password="testing",
                                                                               database="telehelp")
                                                mycursor = mydb.cursor()

                                                sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                                val = (
                                                    float(resplat), float(resplng),
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), IMEI)
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("registro de ubicacion actualizado")
                                                sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento) VALUES (%s, %s, %s, %s)"
                                                val = (
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), respuesta_en_str,
                                                    respuesta_en_str[4:14],
                                                    "Caída")
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("Alerta Caída ingresada.")
                                                funcon = mysql.connector.connect(host="localhost", user="root",
                                                                                 password="testing",
                                                                                 database="telehelp")
                                                funcursor = funcon.cursor()
                                                query = ("SELECT * FROM dispositivos WHERE IMEI=%s")
                                                IMEI = str(dato_recibido_en_str[4:14])
                                                print(str(IMEI))
                                                funcursor.execute(query, (IMEI,))

                                                for (userName) in funcursor:
                                                    linea = userName[5]
                                                    codUsuario = userName[6]
                                                    latitudconsulta = userName[9]
                                                    longitudconsulta = userName[10]
                                                    FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                    print(linea)
                                                    print(codUsuario)
                                                    print(latitudconsulta)
                                                    print(longitudconsulta)
                                                    print(FECHAORA)

                                                funcursor1 = funcon.cursor()
                                                query1 = (
                                                    "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1")
                                                funcursor1.execute(query1, (IMEI,))

                                                for (servertabla) in funcursor1:
                                                    Idevento = servertabla[0]
                                                    print(Idevento)

                                                url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                    latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                    KeyMapsGoogle)
                                                headers = CaseInsensitiveDict()
                                                headers["Content-Length"] = "0"
                                                resp = requests.post(url, headers=headers, verify=False)
                                                result = resp.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                                                                                                "Id" :""" + str(
                                                    Idevento) + """,
                                                                                                                                                                "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                                                                                                "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                                                                                                "TipoEvento" : "CAIDA",
                                                                                                                                                                "Accion" : "A",
                                                                                                                                                                "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                                                                                                "Direccion" :""" + """\"""" + str(
                                                    geodata['address']) + """\"""" + """,
                                                                                                                                                                "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                                                                                                "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                                                                                                }"""

                                                print(data)

                                                print(str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())
                                                fin = time.time()
                                                print(fin - inicio)
                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))
                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code
                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                            411, 412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"
                                                    data = """{

                                                                                                                                                                                                                                                            "Id" :""" + str(

                                                        Idevento) + """,

                                                                                                                                                                                                                                                            "TelefonoAsociado" : """ + """\"""" + str(

                                                        linea) + """\"""" + """,

                                                                                                                                                                                                                                                            "UsuarioCodigo" :""" + """\"""" + str(

                                                        codUsuario) + """\"""" + """,

                                                                                                                                                                                                                                                            "TipoEvento" : "CAIDA",

                                                                                                                                                                                                                                                            "Accion" : "A",

                                                                                                                                                                                                                                                            "Fecha y Hora" : """ + """\"""" + str(

                                                        FECHAORA) + """\"""" + """,

                                                                                                                                                                                                                                                            "Direccion" :""" + """\"""" + str(

                                                        latitudconsulta) + "," + str(

                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,

                                                                                                                                                                                                                                                            "Latitud" : """ + """\"""" + str(

                                                        latitudconsulta) + """\"""" + """,

                                                                                                                                                                                                                                                            "Longitud" : """ + """\"""" + str(

                                                        longitudconsulta) + """\"""" + """

                                                                                                                                                                                                                                                            } """

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    fin = time.time()
                                                    print(fin - inicio)
                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                            else:
                                print("Se recibió Ubicación")

                                print("Se recibe ubicación" + "\n")
                                dato_recibido_en_str = mensajeEncript.decode()
                                print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " Recibido desde el cliente:",
                                      str(mensajeEncript))
                                print(str(mensajeEncript) + "\n")

                                IMEI = dato_recibido_en_str[4:14]
                                print(IMEI)
                                cadena = dato_recibido_en_str[20:]
                                arrayCadena = cadena.split(",")
                                Alarmas = arrayCadena[16]
                                print(arrayCadena[3])  # si es A o V
                                if "A" == arrayCadena[3]:
                                    if arrayCadena[5] == "S":
                                        latitud = "-" + arrayCadena[4]
                                    else:
                                        latitud = arrayCadena[4]

                                    if arrayCadena[7] == "W":
                                        longitud = "-" + arrayCadena[6]
                                    else:
                                        longitud = arrayCadena[6]

                                    # se actualiza la ubicación en la BD
                                    mydb = mysql.connector.connect(host="localhost", user="root",
                                                                   password="testing",
                                                                   database="telehelp")
                                    mycursor = mydb.cursor()

                                    sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                    val = (
                                        float(latitud), float(longitud), datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        IMEI)
                                    mycursor.execute(sql, val)
                                    mydb.commit()
                                    print("registro de ubicacion actualizado")

                                    # Insertar el evento en la BD
                                    sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento, status, visualizado) VALUES (%s, %s, %s, %s, %s, %s)"
                                    val = (
                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "UD", IMEI, "UD", "No aplica",
                                        "No aplica")
                                    mycursor.execute(sql, val)
                                    mydb.commit()
                                    print(mycursor.rowcount, "registro insertado")

                                    funcon = mysql.connector.connect(host="localhost", user="root",
                                                                     password="testing",
                                                                     database="telehelp")
                                    funcursor = funcon.cursor()
                                    query = "SELECT * FROM dispositivos WHERE IMEI=%s"
                                    IMEI = str(dato_recibido_en_str[4:14])
                                    print(str(IMEI))
                                    funcursor.execute(query, (IMEI,))

                                    for (userName) in funcursor:
                                        linea = userName[5]
                                        codUsuario = userName[6]
                                        latitudconsulta = userName[9]
                                        longitudconsulta = userName[10]
                                        FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        print(linea)
                                        print(codUsuario)
                                        print(latitudconsulta)
                                        print(longitudconsulta)
                                        print(FECHAORA)

                                    funcursor1 = funcon.cursor()
                                    query1 = "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1"
                                    funcursor1.execute(query1, (IMEI,))

                                    for (servertabla) in funcursor1:
                                        Idevento = servertabla[0]
                                        print(Idevento)

                                        url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                            latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                            KeyMapsGoogle)
                                        headers = CaseInsensitiveDict()
                                        headers["Content-Length"] = "0"
                                        retries = 3

                                        for n in range(retries):
                                            try:
                                                response = requests.post(url, headers=headers, verify=False)
                                                response.raise_for_status()  # 200,201,202,203,204,205,206,207,208,226
                                                result = response.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                                                            "Id" :""" + str(
                                                    Idevento) + """,
                                                                                                                            "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                                                            "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                                                            "TipoEvento" : "UBICACION",
                                                                                                                            "Accion" : "A",
                                                                                                                            "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                                                            "Direccion" :""" + """\"""" + str(
                                                    geodata['address']) + """\"""" + """,
                                                                                                                            "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                                                            "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                                                            }"""

                                                print(data)

                                                print(str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())

                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code

                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411,
                                                            412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"

                                                    data = """{
                                                                                                                                                                                "Id" :""" + str(
                                                        Idevento) + """,
                                                                                                                                                                                "TelefonoAsociado" : """ + """\"""" + str(
                                                        linea) + """\"""" + """,
                                                                                                                                                                                "UsuarioCodigo" :""" + """\"""" + str(
                                                        codUsuario) + """\"""" + """,
                                                                                                                                                                                "TipoEvento" : "UBICACION",
                                                                                                                                                                                "Accion" : "A",
                                                                                                                                                                                "Fecha y Hora" : """ + """\"""" + str(
                                                        FECHAORA) + """\"""" + """,
                                                                                                                                                                                "Direccion" :""" + """\"""" + str(
                                                        latitudconsulta) + "," + str(
                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,
                                                                                                                                                                                "Latitud" : """ + """\"""" + str(
                                                        latitudconsulta) + """\"""" + """,
                                                                                                                                                                                "Longitud" : """ + """\"""" + str(
                                                        longitudconsulta) + """\"""" + """
                                                                                                                                                                                }"""

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())

                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                elif "V" == arrayCadena[3]:
                                    arrSplit = dato_recibido_en_str.split(",")
                                    baseEstation = int(arrSplit[17])
                                    print("numero de estaciones base: " + str(baseEstation))

                                    if baseEstation >= 1:
                                        MCC1 = int(arrSplit[19])
                                        print("MCC: " + str(MCC1))
                                        MNC1 = int(arrSplit[20])
                                        print("MNC: " + str(MNC1))
                                        if MNC1 == 10:
                                            carrier1 = "CLARO"
                                            print(carrier1)
                                        elif MNC1 == 7:
                                            carrier1 = "MOVISTAR"
                                            print(carrier1)
                                        elif MNC1 == 1:
                                            carrier1 = "ANTEL"
                                            print(carrier1)

                                        locationAreaCode1 = int(arrSplit[21])
                                        print("LAC: " + str(locationAreaCode1))
                                        cellId1 = int(arrSplit[22])
                                        print("CellId: " + str(cellId1))
                                        signalStrength1 = int(arrSplit[23]) - 100

                                    cellTowers = "{" + "\n" + "\"cellId\": " + str(
                                        cellId1) + "," + "\n" + "\"locationAreaCode\": " + str(
                                        locationAreaCode1) + "," + "\n" + "\"mobileCountryCode\": " + str(
                                        MCC1) + "," + "\n" + "\"mobileNetworkCode\": " + str(
                                        MNC1) + "," + "\n" + "\"signalStrength\": " + str(
                                        signalStrength1) + "\n" + "}" + "\n"

                                    wifi = 17 + (6 * int(arrSplit[17])) + 1
                                    wifinumber = int(arrSplit[wifi])
                                    print("Número de redes wifi: " + str(wifinumber))

                                    if wifinumber == 0:
                                        # Insertar el evento en la BD
                                        mydb = mysql.connector.connect(host="localhost", user="root",
                                                                       password="testing",
                                                                       database="telehelp")
                                        mycursor = mydb.cursor()
                                        sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento, status, visualizado) VALUES (%s, %s, %s, %s, %s, %s)"
                                        val = (
                                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "UD", IMEI, "UD", "No aplica",
                                            "No aplica")
                                        mycursor.execute(sql, val)
                                        mydb.commit()
                                        print(mycursor.rowcount, "registro insertado")

                                        funcon = mysql.connector.connect(host="localhost", user="root",
                                                                         password="testing",
                                                                         database="telehelp")
                                        funcursor = funcon.cursor()
                                        query = "SELECT * FROM dispositivos WHERE IMEI=%s"
                                        IMEI = str(dato_recibido_en_str[4:14])
                                        print(str(IMEI))
                                        funcursor.execute(query, (IMEI,))

                                        for (userName) in funcursor:
                                            linea = userName[5]
                                            codUsuario = userName[6]
                                            latitudconsulta = userName[9]
                                            longitudconsulta = userName[10]
                                            FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            print(linea)
                                            print(codUsuario)
                                            print(latitudconsulta)
                                            print(longitudconsulta)
                                            print(FECHAORA)

                                        funcursor1 = funcon.cursor()
                                        query1 = "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1"
                                        funcursor1.execute(query1, (IMEI,))

                                        for (servertabla) in funcursor1:
                                            Idevento = servertabla[0]
                                            print(Idevento)

                                            url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                KeyMapsGoogle)
                                            headers = CaseInsensitiveDict()
                                            headers["Content-Length"] = "0"
                                            retries = 3

                                            for n in range(retries):
                                                try:
                                                    response = requests.post(url, headers=headers, verify=False)
                                                    response.raise_for_status()  # 200,201,202,203,204,205,206,207,208,226
                                                    result = response.json()['results'][0]
                                                    geodata = dict()
                                                    geodata['address'] = result['formatted_address']
                                                    print(geodata['address'])

                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"

                                                    data = """{
                                                                                                                                                                    "Id" :""" + str(
                                                        Idevento) + """,
                                                                                                                                                                    "TelefonoAsociado" : """ + """\"""" + str(
                                                        linea) + """\"""" + """,
                                                                                                                                                                    "UsuarioCodigo" :""" + """\"""" + str(
                                                        codUsuario) + """\"""" + """,
                                                                                                                                                                    "TipoEvento" : "UBICACION",
                                                                                                                                                                    "Accion" : "A",
                                                                                                                                                                    "Fecha y Hora" : """ + """\"""" + str(
                                                        FECHAORA) + """\"""" + """,
                                                                                                                                                                    "Direccion" :""" + """\"""" + str(
                                                        geodata['address']) + """\"""" + """,
                                                                                                                                                                    "Latitud" : """ + """\"""" + str(
                                                        latitudconsulta) + """\"""" + """,
                                                                                                                                                                    "Longitud" : """ + """\"""" + str(
                                                        longitudconsulta) + """\"""" + """
                                                                                                                                                                    }"""

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())

                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                                    break

                                                except HTTPError as exc:
                                                    code = exc.response.status_code

                                                    if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                                411, 412, 413, 414, 415, 422]:
                                                        url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                        headers = CaseInsensitiveDict()
                                                        headers["Accept"] = "application/json"
                                                        headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                        headers["Content-Type"] = "application/json"

                                                        data = """{
                                                                                                                                                                                                                        "Id" :""" + str(
                                                            Idevento) + """,
                                                                                                                                                                                                                        "TelefonoAsociado" : """ + """\"""" + str(
                                                            linea) + """\"""" + """,
                                                                                                                                                                                                                        "UsuarioCodigo" :""" + """\"""" + str(
                                                            codUsuario) + """\"""" + """,
                                                                                                                                                                                                                        "TipoEvento" : "UBICACION",
                                                                                                                                                                                                                        "Accion" : "A",
                                                                                                                                                                                                                        "Fecha y Hora" : """ + """\"""" + str(
                                                            FECHAORA) + """\"""" + """,
                                                                                                                                                                                                                        "Direccion" :""" + """\"""" + str(
                                                            latitudconsulta) + "," + str(
                                                            longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,
                                                                                                                                                                                                                        "Latitud" : """ + """\"""" + str(
                                                            latitudconsulta) + """\"""" + """,
                                                                                                                                                                                                                        "Longitud" : """ + """\"""" + str(
                                                            longitudconsulta) + """\"""" + """
                                                                                                                                                                                                                        }"""

                                                        print(data)

                                                        print(str(data) + " " + str(
                                                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                        resp = requests.post(url, headers=headers, data=data,
                                                                             verify=False)
                                                        print(resp.json())

                                                        respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                        self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                    elif wifinumber == 1:
                                        redeswifi = "{" + "\n" + "\"macAddress\": " + "\"" + arrSplit[
                                            wifi + 2] + "\"" + "," + "\n" + "\"signalStrength\": " + arrSplit[
                                                        wifi + 3] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}" + "\n"

                                        jsonUbicacion = "{" + "\n" + "\"homeMobileCountryCode\": " + str(
                                            MCC1) + "," + "\n" + "\"homeMobileNetworkCode\": " + str(
                                            MNC1) + "," + "\n" + "\"radioType\":  \"gsm\"" + "," + "\n" + "\"carrier\": " + "\"" + str(
                                            carrier1) + "\"" + "," + "\n" + "\"considerIp\": true" + "," + "\n" "\"cellTowers\": [" + "\n" + cellTowers + "]" + "," + "\n" + "\"wifiAccessPoints\": [" + "\n" + redeswifi + "]" + "\n" + "}" + "\n"
                                        print(jsonUbicacion)

                                        url = "https://www.googleapis.com/geolocation/v1/geolocate?key=" + str(
                                            KeyMapsGoogle)
                                        retries = 3

                                        for n in range(retries):
                                            try:

                                                res = requests.post(url, data=jsonUbicacion, verify=False)

                                                divide = res.text.split(": ")

                                                if "lat" in res.text:
                                                    resplat = divide[2]
                                                    resplat = resplat[0:9]

                                                if "lng" in res.text:
                                                    resplng = divide[3]
                                                    resplng = resplng[0:9]

                                                mydb = mysql.connector.connect(host="localhost", user="root",
                                                                               password="testing",
                                                                               database="telehelp")
                                                mycursor = mydb.cursor()

                                                sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                                val = (
                                                    float(resplat), float(resplng),
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), IMEI)
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("registro de ubicacion actualizado")
                                                sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento, status, visualizado) VALUES (%s, %s, %s, %s, %s, %s)"
                                                val = (
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "UD", IMEI, "UD",
                                                    "No aplica",
                                                    "No aplica")
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print(mycursor.rowcount, "registro insertado")
                                                funcon = mysql.connector.connect(host="localhost", user="root",
                                                                                 password="testing",
                                                                                 database="telehelp")
                                                funcursor = funcon.cursor()
                                                query = ("SELECT * FROM dispositivos WHERE IMEI=%s")
                                                IMEI = str(dato_recibido_en_str[4:14])
                                                print(str(IMEI))
                                                funcursor.execute(query, (IMEI,))

                                                for (userName) in funcursor:
                                                    linea = userName[5]
                                                    codUsuario = userName[6]
                                                    latitudconsulta = userName[9]
                                                    longitudconsulta = userName[10]
                                                    FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                    print(linea)
                                                    print(codUsuario)
                                                    print(latitudconsulta)
                                                    print(longitudconsulta)
                                                    print(FECHAORA)

                                                funcursor1 = funcon.cursor()
                                                query1 = (
                                                    "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1")
                                                funcursor1.execute(query1, (IMEI,))

                                                for (servertabla) in funcursor1:
                                                    Idevento = servertabla[0]
                                                    print(Idevento)

                                                url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                    latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                    KeyMapsGoogle)
                                                headers = CaseInsensitiveDict()
                                                headers["Content-Length"] = "0"
                                                resp = requests.post(url, headers=headers, verify=False)
                                                result = resp.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                                                        "Id" :""" + str(
                                                    Idevento) + """,
                                                                                                                        "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                                                        "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                                                        "TipoEvento" : "UBICACION",
                                                                                                                        "Accion" : "A",
                                                                                                                        "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                                                        "Direccion" :""" + """\"""" + str(
                                                    geodata['address']) + """\"""" + """,
                                                                                                                        "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                                                        "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                                                        }"""

                                                print(data)

                                                print(str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())
                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))
                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code
                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                            411, 412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"
                                                    data = """{

                                                                                                                                                                                                                    "Id" :""" + str(

                                                        Idevento) + """,

                                                                                                                                                                                                                    "TelefonoAsociado" : """ + """\"""" + str(

                                                        linea) + """\"""" + """,

                                                                                                                                                                                                                    "UsuarioCodigo" :""" + """\"""" + str(

                                                        codUsuario) + """\"""" + """,

                                                                                                                                                                                                                    "TipoEvento" : "UBICACION",

                                                                                                                                                                                                                    "Accion" : "A",

                                                                                                                                                                                                                    "Fecha y Hora" : """ + """\"""" + str(

                                                        FECHAORA) + """\"""" + """,

                                                                                                                                                                                                                    "Direccion" :""" + """\"""" + str(

                                                        latitudconsulta) + "," + str(

                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,

                                                                                                                                                                                                                    "Latitud" : """ + """\"""" + str(

                                                        latitudconsulta) + """\"""" + """,

                                                                                                                                                                                                                    "Longitud" : """ + """\"""" + str(

                                                        longitudconsulta) + """\"""" + """

                                                                                                                                                                                                                    } """

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                    elif wifinumber == 2:
                                        redeswifi = "{" + "\n" + "\"macAddress\": " + "\"" + arrSplit[
                                            wifi + 2] + "\"" + "," + "\n" + "\"signalStrength\": " + arrSplit[
                                                        wifi + 3] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 5] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 6] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}" + "\n"
                                        jsonUbicacion = "{" + "\n" + "\"homeMobileCountryCode\": " + str(
                                            MCC1) + "," + "\n" + "\"homeMobileNetworkCode\": " + str(
                                            MNC1) + "," + "\n" + "\"radioType\":  \"gsm\"" + "," + "\n" + "\"carrier\": " + "\"" + str(
                                            carrier1) + "\"" + "," + "\n" + "\"considerIp\": true" + "," + "\n" "\"cellTowers\": [" + "\n" + cellTowers + "]" + "," + "\n" + "\"wifiAccessPoints\": [" + "\n" + redeswifi + "]" + "\n" + "}" + "\n"
                                        print(jsonUbicacion)

                                        url = "https://www.googleapis.com/geolocation/v1/geolocate?key=" + str(
                                            KeyMapsGoogle)
                                        retries = 3

                                        for n in range(retries):
                                            try:

                                                res = requests.post(url, data=jsonUbicacion, verify=False)

                                                divide = res.text.split(": ")

                                                if "lat" in res.text:
                                                    resplat = divide[2]
                                                    resplat = resplat[0:9]

                                                if "lng" in res.text:
                                                    resplng = divide[3]
                                                    resplng = resplng[0:9]

                                                mydb = mysql.connector.connect(host="localhost", user="root",
                                                                               password="testing",
                                                                               database="telehelp")
                                                mycursor = mydb.cursor()

                                                sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                                val = (
                                                    float(resplat), float(resplng),
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), IMEI)
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("registro de ubicacion actualizado")
                                                sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento, status, visualizado) VALUES (%s, %s, %s, %s, %s, %s)"
                                                val = (
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "UD", IMEI, "UD",
                                                    "No aplica",
                                                    "No aplica")
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print(mycursor.rowcount, "registro insertado")
                                                funcon = mysql.connector.connect(host="localhost", user="root",
                                                                                 password="testing",
                                                                                 database="telehelp")
                                                funcursor = funcon.cursor()
                                                query = ("SELECT * FROM dispositivos WHERE IMEI=%s")
                                                IMEI = str(dato_recibido_en_str[4:14])
                                                print(str(IMEI))
                                                funcursor.execute(query, (IMEI,))

                                                for (userName) in funcursor:
                                                    linea = userName[5]
                                                    codUsuario = userName[6]
                                                    latitudconsulta = userName[9]
                                                    longitudconsulta = userName[10]
                                                    FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                    print(linea)
                                                    print(codUsuario)
                                                    print(latitudconsulta)
                                                    print(longitudconsulta)
                                                    print(FECHAORA)

                                                funcursor1 = funcon.cursor()
                                                query1 = (
                                                    "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1")
                                                funcursor1.execute(query1, (IMEI,))

                                                for (servertabla) in funcursor1:
                                                    Idevento = servertabla[0]
                                                    print(Idevento)

                                                url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                    latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                    KeyMapsGoogle)
                                                headers = CaseInsensitiveDict()
                                                headers["Content-Length"] = "0"
                                                resp = requests.post(url, headers=headers, verify=False)
                                                result = resp.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                                                                                                "Id" :""" + str(
                                                    Idevento) + """,
                                                                                                                                                                "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                                                                                                "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                                                                                                "TipoEvento" : "UBICACION",
                                                                                                                                                                "Accion" : "A",
                                                                                                                                                                "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                                                                                                "Direccion" :""" + """\"""" + str(
                                                    geodata['address']) + """\"""" + """,
                                                                                                                                                                "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                                                                                                "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                                                                                                }"""

                                                print(data)

                                                print(str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())
                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))
                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code
                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                            411, 412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"
                                                    data = """{

                                                                                                                                                                                                                                                            "Id" :""" + str(

                                                        Idevento) + """,

                                                                                                                                                                                                                                                            "TelefonoAsociado" : """ + """\"""" + str(

                                                        linea) + """\"""" + """,

                                                                                                                                                                                                                                                            "UsuarioCodigo" :""" + """\"""" + str(

                                                        codUsuario) + """\"""" + """,

                                                                                                                                                                                                                                                            "TipoEvento" : "UBICACION",

                                                                                                                                                                                                                                                            "Accion" : "A",

                                                                                                                                                                                                                                                            "Fecha y Hora" : """ + """\"""" + str(

                                                        FECHAORA) + """\"""" + """,

                                                                                                                                                                                                                                                            "Direccion" :""" + """\"""" + str(

                                                        latitudconsulta) + "," + str(

                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,

                                                                                                                                                                                                                                                            "Latitud" : """ + """\"""" + str(

                                                        latitudconsulta) + """\"""" + """,

                                                                                                                                                                                                                                                            "Longitud" : """ + """\"""" + str(

                                                        longitudconsulta) + """\"""" + """

                                                                                                                                                                                                                                                            } """

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                    elif wifinumber == 3:
                                        redeswifi = "{" + "\n" + "\"macAddress\": " + "\"" + arrSplit[
                                            wifi + 2] + "\"" + "," + "\n" + "\"signalStrength\": " + arrSplit[
                                                        wifi + 3] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " \
                                                    + "\"" + arrSplit[
                                                        wifi + 5] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 6] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 8] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 9] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}" + "\n"
                                        jsonUbicacion = "{" + "\n" + "\"homeMobileCountryCode\": " + str(
                                            MCC1) + "," + "\n" + "\"homeMobileNetworkCode\": " + str(
                                            MNC1) + "," + "\n" + "\"radioType\":  \"gsm\"" + "," + "\n" + "\"carrier\": " + "\"" + str(
                                            carrier1) + "\"" + "," + "\n" + "\"considerIp\": true" + "," + "\n" "\"cellTowers\": [" + "\n" + cellTowers + "]" + "," + "\n" + "\"wifiAccessPoints\": [" + "\n" + redeswifi + "]" + "\n" + "}" + "\n"
                                        print(jsonUbicacion)

                                        url = "https://www.googleapis.com/geolocation/v1/geolocate?key=" + str(
                                            KeyMapsGoogle)
                                        retries = 3

                                        for n in range(retries):
                                            try:

                                                res = requests.post(url, data=jsonUbicacion, verify=False)

                                                divide = res.text.split(": ")

                                                if "lat" in res.text:
                                                    resplat = divide[2]
                                                    resplat = resplat[0:9]

                                                if "lng" in res.text:
                                                    resplng = divide[3]
                                                    resplng = resplng[0:9]

                                                mydb = mysql.connector.connect(host="localhost", user="root",
                                                                               password="testing",
                                                                               database="telehelp")
                                                mycursor = mydb.cursor()

                                                sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                                val = (
                                                    float(resplat), float(resplng),
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), IMEI)
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("registro de ubicacion actualizado")
                                                sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento, status, visualizado) VALUES (%s, %s, %s, %s, %s, %s)"
                                                val = (
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "UD", IMEI, "UD",
                                                    "No aplica",
                                                    "No aplica")
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print(mycursor.rowcount, "registro insertado")
                                                funcon = mysql.connector.connect(host="localhost", user="root",
                                                                                 password="testing",
                                                                                 database="telehelp")
                                                funcursor = funcon.cursor()
                                                query = ("SELECT * FROM dispositivos WHERE IMEI=%s")
                                                IMEI = str(dato_recibido_en_str[4:14])
                                                print(str(IMEI))
                                                funcursor.execute(query, (IMEI,))

                                                for (userName) in funcursor:
                                                    linea = userName[5]
                                                    codUsuario = userName[6]
                                                    latitudconsulta = userName[9]
                                                    longitudconsulta = userName[10]
                                                    FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                    print(linea)
                                                    print(codUsuario)
                                                    print(latitudconsulta)
                                                    print(longitudconsulta)
                                                    print(FECHAORA)

                                                funcursor1 = funcon.cursor()
                                                query1 = (
                                                    "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1")
                                                funcursor1.execute(query1, (IMEI,))

                                                for (servertabla) in funcursor1:
                                                    Idevento = servertabla[0]
                                                    print(Idevento)

                                                url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                    latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                    KeyMapsGoogle)
                                                headers = CaseInsensitiveDict()
                                                headers["Content-Length"] = "0"
                                                resp = requests.post(url, headers=headers, verify=False)
                                                result = resp.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                                                                                                "Id" :""" + str(
                                                    Idevento) + """,
                                                                                                                                                                "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                                                                                                "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                                                                                                "TipoEvento" : "UBICACION",
                                                                                                                                                                "Accion" : "A",
                                                                                                                                                                "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                                                                                                "Direccion" :""" + """\"""" + str(
                                                    geodata['address']) + """\"""" + """,
                                                                                                                                                                "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                                                                                                "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                                                                                                }"""

                                                print(data)

                                                print(str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())
                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))
                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code
                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                            411, 412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"
                                                    data = """{

                                                                                                                                                                                                                                                            "Id" :""" + str(

                                                        Idevento) + """,

                                                                                                                                                                                                                                                            "TelefonoAsociado" : """ + """\"""" + str(

                                                        linea) + """\"""" + """,

                                                                                                                                                                                                                                                            "UsuarioCodigo" :""" + """\"""" + str(

                                                        codUsuario) + """\"""" + """,

                                                                                                                                                                                                                                                            "TipoEvento" : "UBICACION",

                                                                                                                                                                                                                                                            "Accion" : "A",

                                                                                                                                                                                                                                                            "Fecha y Hora" : """ + """\"""" + str(

                                                        FECHAORA) + """\"""" + """,

                                                                                                                                                                                                                                                            "Direccion" :""" + """\"""" + str(

                                                        latitudconsulta) + "," + str(

                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,

                                                                                                                                                                                                                                                            "Latitud" : """ + """\"""" + str(

                                                        latitudconsulta) + """\"""" + """,

                                                                                                                                                                                                                                                            "Longitud" : """ + """\"""" + str(

                                                        longitudconsulta) + """\"""" + """

                                                                                                                                                                                                                                                            } """

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                    elif wifinumber == 4:
                                        redeswifi = "{" + "\n" + "\"macAddress\": " + "\"" + arrSplit[
                                            wifi + 2] + "\"" + "," + "\n" + "\"signalStrength\": " + arrSplit[
                                                        wifi + 3] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 5] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 6] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 8] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 9] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 11] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 12] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}" + "\n"
                                        jsonUbicacion = "{" + "\n" + "\"homeMobileCountryCode\": " + str(
                                            MCC1) + "," + "\n" + "\"homeMobileNetworkCode\": " + str(
                                            MNC1) + "," + "\n" + "\"radioType\":  \"gsm\"" + "," + "\n" + "\"carrier\": " + "\"" + str(
                                            carrier1) + "\"" + "," + "\n" + "\"considerIp\": true" + "," + "\n" "\"cellTowers\": [" + "\n" + cellTowers + "]" + "," + "\n" + "\"wifiAccessPoints\": [" + "\n" + redeswifi + "]" + "\n" + "}" + "\n"
                                        print(jsonUbicacion)

                                        url = "https://www.googleapis.com/geolocation/v1/geolocate?key=" + str(
                                            KeyMapsGoogle)
                                        retries = 3

                                        for n in range(retries):
                                            try:

                                                res = requests.post(url, data=jsonUbicacion, verify=False)

                                                divide = res.text.split(": ")

                                                if "lat" in res.text:
                                                    resplat = divide[2]
                                                    resplat = resplat[0:9]

                                                if "lng" in res.text:
                                                    resplng = divide[3]
                                                    resplng = resplng[0:9]

                                                mydb = mysql.connector.connect(host="localhost", user="root",
                                                                               password="testing",
                                                                               database="telehelp")
                                                mycursor = mydb.cursor()

                                                sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                                val = (
                                                    float(resplat), float(resplng),
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), IMEI)
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("registro de ubicacion actualizado")
                                                sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento, status, visualizado) VALUES (%s, %s, %s, %s, %s, %s)"
                                                val = (
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "UD", IMEI, "UD",
                                                    "No aplica",
                                                    "No aplica")
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print(mycursor.rowcount, "registro insertado")
                                                funcon = mysql.connector.connect(host="localhost", user="root",
                                                                                 password="testing",
                                                                                 database="telehelp")
                                                funcursor = funcon.cursor()
                                                query = ("SELECT * FROM dispositivos WHERE IMEI=%s")
                                                IMEI = str(dato_recibido_en_str[4:14])
                                                print(str(IMEI))
                                                funcursor.execute(query, (IMEI,))

                                                for (userName) in funcursor:
                                                    linea = userName[5]
                                                    codUsuario = userName[6]
                                                    latitudconsulta = userName[9]
                                                    longitudconsulta = userName[10]
                                                    FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                    print(linea)
                                                    print(codUsuario)
                                                    print(latitudconsulta)
                                                    print(longitudconsulta)
                                                    print(FECHAORA)

                                                funcursor1 = funcon.cursor()
                                                query1 = (
                                                    "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1")
                                                funcursor1.execute(query1, (IMEI,))

                                                for (servertabla) in funcursor1:
                                                    Idevento = servertabla[0]
                                                    print(Idevento)

                                                url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                    latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                    KeyMapsGoogle)
                                                headers = CaseInsensitiveDict()
                                                headers["Content-Length"] = "0"
                                                resp = requests.post(url, headers=headers, verify=False)
                                                result = resp.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                                                                                                "Id" :""" + str(
                                                    Idevento) + """,
                                                                                                                                                                "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                                                                                                "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                                                                                                "TipoEvento" : "UBICACION",
                                                                                                                                                                "Accion" : "A",
                                                                                                                                                                "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                                                                                                "Direccion" :""" + """\"""" + str(
                                                    geodata['address']) + """\"""" + """,
                                                                                                                                                                "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                                                                                                "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                                                                                                }"""

                                                print(data)

                                                print(str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())
                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))
                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code
                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                            411, 412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"
                                                    data = """{

                                                                                                                                                                                                                                                            "Id" :""" + str(

                                                        Idevento) + """,

                                                                                                                                                                                                                                                            "TelefonoAsociado" : """ + """\"""" + str(

                                                        linea) + """\"""" + """,

                                                                                                                                                                                                                                                            "UsuarioCodigo" :""" + """\"""" + str(

                                                        codUsuario) + """\"""" + """,

                                                                                                                                                                                                                                                            "TipoEvento" : "UBICACION",

                                                                                                                                                                                                                                                            "Accion" : "A",

                                                                                                                                                                                                                                                            "Fecha y Hora" : """ + """\"""" + str(

                                                        FECHAORA) + """\"""" + """,

                                                                                                                                                                                                                                                            "Direccion" :""" + """\"""" + str(

                                                        latitudconsulta) + "," + str(

                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,

                                                                                                                                                                                                                                                            "Latitud" : """ + """\"""" + str(

                                                        latitudconsulta) + """\"""" + """,

                                                                                                                                                                                                                                                            "Longitud" : """ + """\"""" + str(

                                                        longitudconsulta) + """\"""" + """

                                                                                                                                                                                                                                                            } """

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                                    elif wifinumber == 5:
                                        redeswifi = "{" + "\n" + "\"macAddress\": " + "\"" + arrSplit[
                                            wifi + 2] + "\"" + "," + "\n" + "\"signalStrength\": " + arrSplit[
                                                        wifi + 3] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 5] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 6] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 8] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 9] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 11] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 12] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}," + "\n" + "{" + "\n" + "\"macAddress\": " + "\"" + \
                                                    arrSplit[wifi + 14] + "\"" + "," + "\n" + "\"signalStrength\": " + \
                                                    arrSplit[
                                                        wifi + 15] + "," + "\n" + "\"signalToNoiseRatio\": 0" + "\n" + "}" + "\n"

                                        jsonUbicacion = "{" + "\n" + "\"homeMobileCountryCode\": " + str(
                                            MCC1) + "," + "\n" + "\"homeMobileNetworkCode\": " + str(
                                            MNC1) + "," + "\n" + "\"radioType\":  \"gsm\"" + "," + "\n" + "\"carrier\": " + "\"" + str(
                                            carrier1) + "\"" + "," + "\n" + "\"considerIp\": true" + "," + "\n" "\"cellTowers\": [" + "\n" + cellTowers + "]" + "," + "\n" + "\"wifiAccessPoints\": [" + "\n" + redeswifi + "]" + "\n" + "}" + "\n"
                                        print(jsonUbicacion)

                                        url = "https://www.googleapis.com/geolocation/v1/geolocate?key=" + str(
                                            KeyMapsGoogle)
                                        retries = 3

                                        for n in range(retries):
                                            try:

                                                res = requests.post(url, data=jsonUbicacion, verify=False)

                                                divide = res.text.split(": ")

                                                if "lat" in res.text:
                                                    resplat = divide[2]
                                                    resplat = resplat[0:9]

                                                if "lng" in res.text:
                                                    resplng = divide[3]
                                                    resplng = resplng[0:9]

                                                mydb = mysql.connector.connect(host="localhost", user="root",
                                                                               password="testing",
                                                                               database="telehelp")
                                                mycursor = mydb.cursor()

                                                sql = "UPDATE dispositivos SET lat = %s, lng = %s, FechaReg = %s  WHERE IMEI = %s"
                                                val = (
                                                    float(resplat), float(resplng),
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), IMEI)
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print("registro de ubicacion actualizado")
                                                sql = "INSERT INTO server (Fecha, Mensaje, IMEI, Evento, status, visualizado) VALUES (%s, %s, %s, %s, %s, %s)"
                                                val = (
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "UD", IMEI, "UD",
                                                    "No aplica",
                                                    "No aplica")
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                                print(mycursor.rowcount, "registro insertado")
                                                funcon = mysql.connector.connect(host="localhost", user="root",
                                                                                 password="testing",
                                                                                 database="telehelp")
                                                funcursor = funcon.cursor()
                                                query = ("SELECT * FROM dispositivos WHERE IMEI=%s")
                                                IMEI = str(dato_recibido_en_str[4:14])
                                                print(str(IMEI))
                                                funcursor.execute(query, (IMEI,))

                                                for (userName) in funcursor:
                                                    linea = userName[5]
                                                    codUsuario = userName[6]
                                                    latitudconsulta = userName[9]
                                                    longitudconsulta = userName[10]
                                                    FECHAORA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                    print(linea)
                                                    print(codUsuario)
                                                    print(latitudconsulta)
                                                    print(longitudconsulta)
                                                    print(FECHAORA)

                                                funcursor1 = funcon.cursor()
                                                query1 = (
                                                    "SELECT * FROM server WHERE IMEI=%s ORDER BY `server`.id DESC LIMIT 1")
                                                funcursor1.execute(query1, (IMEI,))

                                                for (servertabla) in funcursor1:
                                                    Idevento = servertabla[0]
                                                    print(Idevento)

                                                url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(
                                                    latitudconsulta) + "," + str(longitudconsulta) + "&key=" + str(
                                                    KeyMapsGoogle)
                                                headers = CaseInsensitiveDict()
                                                headers["Content-Length"] = "0"
                                                resp = requests.post(url, headers=headers, verify=False)
                                                result = resp.json()['results'][0]
                                                geodata = dict()
                                                geodata['address'] = result['formatted_address']
                                                print(geodata['address'])

                                                url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                headers = CaseInsensitiveDict()
                                                headers["Accept"] = "application/json"
                                                headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                headers["Content-Type"] = "application/json"

                                                data = """{
                                                                                                                                                                "Id" :""" + str(
                                                    Idevento) + """,
                                                                                                                                                                "TelefonoAsociado" : """ + """\"""" + str(
                                                    linea) + """\"""" + """,
                                                                                                                                                                "UsuarioCodigo" :""" + """\"""" + str(
                                                    codUsuario) + """\"""" + """,
                                                                                                                                                                "TipoEvento" : "UBICACION",
                                                                                                                                                                "Accion" : "A",
                                                                                                                                                                "Fecha y Hora" : """ + """\"""" + str(
                                                    FECHAORA) + """\"""" + """,
                                                                                                                                                                "Direccion" :""" + """\"""" + str(
                                                    geodata['address']) + """\"""" + """,
                                                                                                                                                                "Latitud" : """ + """\"""" + str(
                                                    latitudconsulta) + """\"""" + """,
                                                                                                                                                                "Longitud" : """ + """\"""" + str(
                                                    longitudconsulta) + """\"""" + """
                                                                                                                                                                }"""

                                                print(data)

                                                print(str(data) + " " + str(
                                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                resp = requests.post(url, headers=headers, data=data, verify=False)
                                                print(resp.json())
                                                respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))
                                                break

                                            except HTTPError as exc:
                                                code = exc.response.status_code
                                                if code in [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410,
                                                            411, 412, 413, 414, 415, 422]:
                                                    url = "https://aemirthprod.asesp.local/telehelp/RecibeEvento/"
                                                    headers = CaseInsensitiveDict()
                                                    headers["Accept"] = "application/json"
                                                    headers["Authorization"] = "Basic VEVMRUhFTFA6VEVMRUhFTFA="
                                                    headers["Content-Type"] = "application/json"
                                                    data = """{

                                                                                                                                                                                                                                                            "Id" :""" + str(

                                                        Idevento) + """,

                                                                                                                                                                                                                                                            "TelefonoAsociado" : """ + """\"""" + str(

                                                        linea) + """\"""" + """,

                                                                                                                                                                                                                                                            "UsuarioCodigo" :""" + """\"""" + str(

                                                        codUsuario) + """\"""" + """,

                                                                                                                                                                                                                                                            "TipoEvento" : "UBICACION",

                                                                                                                                                                                                                                                            "Accion" : "A",

                                                                                                                                                                                                                                                            "Fecha y Hora" : """ + """\"""" + str(

                                                        FECHAORA) + """\"""" + """,

                                                                                                                                                                                                                                                            "Direccion" :""" + """\"""" + str(

                                                        latitudconsulta) + "," + str(

                                                        longitudconsulta) + " (ver ubicación en el manager) " + """\"""" + """,

                                                                                                                                                                                                                                                            "Latitud" : """ + """\"""" + str(

                                                        latitudconsulta) + """\"""" + """,

                                                                                                                                                                                                                                                            "Longitud" : """ + """\"""" + str(

                                                        longitudconsulta) + """\"""" + """

                                                                                                                                                                                                                                                            } """

                                                    print(data)

                                                    print(str(data) + " " + str(
                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n")

                                                    resp = requests.post(url, headers=headers, data=data, verify=False)
                                                    print(resp.json())
                                                    respuesta_en_str = "{}".format(dato_recibido_en_str)
                                                    self.csocket.send(bytes(respuesta_en_str, encoding='utf8'))

                        else:
                            pass

                    else:
                        pass


mydb = mysql.connector.connect(host="localhost", user="root",
                               password="testing",
                               database="telehelp")
mycursor = mydb.cursor()
mycursor.execute("SELECT * FROM servidorPython")
myresult = mycursor.fetchall()

for i in myresult:
    LOCALHOST = i[0]
    PORT = i[1]
print(LOCALHOST, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((LOCALHOST, PORT))
print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " Iniciando el Servidor")
print("Esperando por el cliente...")

socket_abierto = True
while socket_abierto:
    server.listen(1)
    clientsock, clientAddress = server.accept()
    newthread = ClientThread(clientAddress, clientsock)
    newthread.start()
