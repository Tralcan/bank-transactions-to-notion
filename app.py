import os
import pandas as pd
from flask import Flask, request, render_template, jsonify
from notion_client import Client
from dotenv import load_dotenv
from datetime import datetime

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

        # Leer el archivo .xlsx, omitiendo las primeras 3 filas
        df = pd.read_excel(file, engine='openpyxl', skiprows=3)
        
        # Imprimir columnas para depuración
        print("Columnas del archivo:", df.columns.tolist())
        
        # Verificar que la columna 'Fecha' existe
        if 'Fecha' not in df.columns:
            return jsonify({"error": f"Columna 'Fecha' no encontrada. Columnas disponibles: {df.columns.tolist()}"}), 400

        # Procesar cada fila y subir a Notion
        for _, row in df.iterrows():
            fecha = row['Fecha']
            if pd.isna(fecha) or not fecha:
                continue  # Omite filas con fechas vacías
            
            # Convertir la fecha a formato ISO 8601
            if isinstance(fecha, str):
                try:
                    fecha = datetime.strptime(fecha, '%d-%m-%Y').isoformat()
                except ValueError:
                    try:
                        fecha = datetime.strptime(fecha, '%Y-%m-%d').isoformat()  # Otro formato posible
                    except ValueError:
                        return jsonify({"error": f"Formato de fecha inválido: {fecha}"}), 400
            elif isinstance(fecha, datetime):
                fecha = fecha.isoformat()
            else:
                return jsonify({"error": f"Tipo de dato inválido para Fecha: {fecha}"}), 400

            # Preparar los datos para Notion
            properties = {
                "Fecha": {"date": {"start": fecha}},
                "Detalle": {"title": [{"text": {"content": str(row['Detalle'])}}]},
                "Monto Cargo ($)": {"number": float(row['Monto cargo ($)']) if pd.notnull(row['Monto cargo ($)']) else 0},
                "Monto Abono ($)": {"number": float(row['Monto abono ($)']) if pd.notnull(row['Monto abono ($)']) else 0},
                "Saldo ($)": {"number": float(row['Saldo ($)']) if pd.notnull(row['Saldo ($)']) else 0}
            }

            # Crear una nueva página en la base de datos de Notion
            notion.pages.create(
                parent={"database_id": NOTION_DATABASE_ID},
                properties=properties
            )

        return jsonify({"message": "Transacciones subidas exitosamente a Notion"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
