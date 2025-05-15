import os
import pandas as pd
import re
import time
import gc
from flask import Flask, request, render_template, jsonify
from notion_client import Client
from dotenv import load_dotenv
from datetime import datetime
import psutil

app = Flask(__name__)
load_dotenv()

# Configuración de Notion
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
notion = Client(auth=NOTION_TOKEN)

# Ruta para la página principal
@app.route('/')
def index():
    return render_template('upload.html')

# Ruta para procesar el archivo .xlsx
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if not file.filename.endswith('.xlsx'):
            return jsonify({"error": "File must be .xlsx"}), 400

        # Leer el archivo .xlsx, omitiendo las primeras 2 filas
        df = pd.read_excel(file, engine='openpyxl', skiprows=2)
        
        # Imprimir columnas para depuración
        print("Columnas del archivo:", df.columns.tolist())
        
        # Verificar que las columnas esperadas existan
        expected_columns = ['Fecha', 'Detalle', 'Monto cargo ($)', 'Monto abono ($)', 'Saldo ($)']
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            return jsonify({"error": f"Columnas faltantes: {missing_columns}. Columnas encontradas: {df.columns.tolist()}"}), 400

        # Contador para registros subidos
        uploaded_count = 0
        
        # Procesar cada fila y subir a Notion
        for index, row in df.iterrows():
            try:
                # Imprimir uso de memoria para depuración
                process = psutil.Process()
                mem_info = process.memory_info()
                print(f"Fila {index + 1}: Memoria usada: {mem_info.rss / 1024 / 1024:.2f} MB")
                
                print(f"Procesando fila {index + 1}: {row.to_dict()}")  # Imprimir fila para depuración
                
                # Validar Fecha
                fecha = row['Fecha']
                if pd.isna(fecha) or not fecha:
                    print(f"Fila {index + 1}: Fecha vacía, omitiendo")
                    continue
                
                # Convertir la fecha a formato ISO 8601
                if isinstance(fecha, str):
                    try:
                        fecha = datetime.strptime(fecha, '%d-%m-%Y').isoformat()
                    except ValueError:
                        try:
                            fecha = datetime.strptime(fecha, '%Y-%m-%d').isoformat()
                        except ValueError:
                            print(f"Fila {index + 1}: Formato de fecha inválido: {fecha}")
                            continue
                elif isinstance(fecha, datetime):
                    fecha = fecha.isoformat()
                else:
                    print(f"Fila {index + 1}: Tipo de dato inválido para Fecha: {fecha}")
                    continue

                # Validar y limpiar Detalle
                detalle = str(row['Detalle']) if pd.notnull(row['Detalle']) else "Sin detalle"
                if not detalle.strip():
                    print(f"Fila {index + 1}: Detalle vacío, usando valor por defecto")
                    detalle = "Sin detalle"
                if len(detalle) > 2000:
                    print(f"Fila {index + 1}: Detalle demasiado largo, truncando")
                    detalle = detalle[:2000]
                # Limpiar caracteres no válidos
                detalle = re.sub(r'[^\x20-\x7E]', '', detalle.strip())  # Solo caracteres ASCII imprimibles
                detalle = re.sub(r'\s+', ' ', detalle)  # Reemplazar espacios múltiples por uno
                if not detalle:
                    print(f"Fila {index + 1}: Detalle inválido después de limpieza, usando valor por defecto")
                    detalle = "Sin detalle"

                # Validar y convertir valores numéricos
                try:
                    monto_cargo = float(row['Monto cargo ($)']) if pd.notnull(row['Monto cargo ($)']) else 0
                    monto_abono = float(row['Monto abono ($)']) if pd.notnull(row['Monto abono ($)']) else 0
                    saldo = float(row['Saldo ($)']) if pd.notnull(row['Saldo ($)']) else 0
                except (ValueError, TypeError) as e:
                    print(f"Fila {index + 1}: Error en valores numéricos: {str(e)}")
                    continue

                # Preparar los datos para Notion
                properties = {
                    "Fecha": {"date": {"start": fecha}},
                    "Detalle": {"title": [{"text": {"content": detalle}}]},
                    "Monto Cargo ($)": {"number": monto_cargo},
                    "Monto Abono ($)": {"number": monto_abono},
                    "Saldo ($)": {"number": saldo}
                }

                # Imprimir datos enviados a Notion para depuración
                print(f"Fila {index + 1}: Enviando a Notion: {properties}")

                # Crear una nueva página en la base de datos de Notion
                notion.pages.create(
                    parent={"database_id": NOTION_DATABASE_ID},
                    properties=properties
                )
                print(f"Fila {index + 1}: Subida exitosamente")
                uploaded_count += 1

                # Retraso para evitar límite de tasa de la API de Notion
                time.sleep(1)

                # Liberar memoria
                del properties
                gc.collect()

            except Exception as e:
                print(f"Fila {index + 1}: Error al subir a Notion: {str(e)}")
                continue  # Continúa con la siguiente fila

        # Liberar memoria después del bucle
        del df
        gc.collect()
        
        return jsonify({"message": f"Subidas {uploaded_count} de {len(df)} transacciones exitosamente a Notion"})

    except Exception as e:
        print(f"Error general: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
