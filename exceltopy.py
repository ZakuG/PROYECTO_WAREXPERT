import difflib
import pandas as pd
import mysql.connector
import re
from mysql.connector import Error

# Configuración de la conexión a la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'admin',
    'database': 'Warexpert'
}

# Ruta del archivo Excel
excel_file = 'LISTABSALE25_actualizado.xlsx'

def parse_variant(variant, tipo):
    """
    Extrae la marca, modelo, cilindrada y años desde el texto de la variante.
    """
    # Diccionario para mapear abreviaturas a nombres completos
    abreviaturas = {
        " NS": "NISSAN",
        " TY": "TOYOTA",
        " HD": "HONDA",
        " HY": "HYUNDAI",
        " CHEV": "CHEVROLET",
        " CHV": "CHEVROLET",
        " SUZ": "SUZUKI",
        " SZ": "SUZUKI",
        " MZ": "MAZDA",
        " MIT": "MITSUBISHI",
        " M.": "MERCEDES",
        " MITS": "MITSUBISHI",
        " DH": "DAIHATSU",
        " DW": "DAEWOO"
        # Agrega más abreviaturas aquí según sea necesario
    }

     # Lista de modelos conocidos
    modelos_conocidos = [
        "YARIS", "COROLLA", "CIVIC", "ACCORD", "TUCSON", "ELANTRA", "SENTRA",
        "VERSA", "MARCH", "AVEO", "CRUZE", "FORTUNE", "LAND CRUISER"
        # Agrega más modelos según tu base de datos
    ]
    
    # Convertir a mayúsculas para comparación sin distinción de mayúsculas/minúsculas
    variant_upper = variant.upper()

    # Reemplazar abreviaturas por nombres completos
    for abbr, full_name in abreviaturas.items():
        variant_upper = variant_upper.replace(abbr, full_name)

    marcas_conocidas = [
        "HONDA", "MAZDA", "HYUNDAI", "KIA", "NISSAN", "CHEVROLET", "FORD", "TOYOTA",
        "MITSUBISHI", "VOLKSWAGEN", "CHRYSLER", "SUZUKI", "PEUGEOT", "FIAT", "RAM",
        "JEEP", "RENAULT", "ISUZU", "DODGE", "ROVER", "LAND", "SUBARU", "DAEWOO", 
        "CITROEN", "SAMSUNG", "DAIHATSU", "MERCEDES"
    ]
    
    # Buscar todas las marcas mencionadas
    marcas_encontradas = [m for m in marcas_conocidas if m in variant_upper]

    # Si se encuentran múltiples marcas, manejar adecuadamente
    if len(marcas_encontradas) > 1:
        marca_principal = marcas_encontradas[0]
        otras_marcas = marcas_encontradas[1:]
    elif marcas_encontradas:
        marca_principal = marcas_encontradas[0]
        otras_marcas = []
    else:
        marca_principal = None
        otras_marcas = []
    
    # Buscar el modelo (relacionado a la primera marca encontrada)
    modelo = None
    if tipo == "LUBRICANTE":
        aceite_match = re.search(r'\d+\s*W\s*\d+', variant_upper)
        if aceite_match:
            modelo = aceite_match.group().replace(" ", "")  # Quitar espacios en el modelo (e.g., "20 W 50" -> "20W50")f
        else:
            modelo = "ATF" if "ATF" in variant_upper else None
        return [{
                "marca": "LUBRICANTE",
                "otras_marcas": None,
                "modelo": modelo,
                "cilindrada": None,
                "año0": None,
                "año1": None
                }]

    # Si no es "ACEITE", buscar modelos regulares
    elif not modelo and marca_principal:
        modelo_match = re.search(rf'{marca_principal}\.?\s+([A-Za-z0-9\-\/]+)', variant_upper)
        if modelo_match:
            modelo_raw = modelo_match.group(1)
            # Corrección automática de modelo mal escrito
            modelo = difflib.get_close_matches(modelo_raw, modelos_conocidos, n=1, cutoff=0.8)
            modelo = modelo[0] if modelo else modelo_raw

    # Extraer cilindrada (ejemplo: "2.5", "3.0")
    cilindrada = re.search(r'\b\d+\.\d+\b', variant)
    cilindrada = float(cilindrada.group()) if cilindrada else None

    # Extraer rango de años (ejemplo: "98-04", "2000/10")
    if re.search(r'\b(W|WK)\s*\d', variant, re.IGNORECASE):
        ano0 = ano1 = None
    else:
        # Extraer rango de años (ejemplo: "98-04", "2000/10", "95/", "78-")
        anos = re.search(r'(\d{2,4})[\-/]?(\d{2,4})?', variant)
        if anos:
            ano0, ano1 = anos.groups()
            
            # Convertir años a enteros si están presentes
            ano0 = int(ano0) if ano0 else None
            ano1 = int(ano1) if ano1 else None
            
            # Ajustar los años para el siglo correcto si son de dos dígitos
            if ano0 is not None:
                if ano0 <= 50:
                    ano0 += 2000
                elif ano0 < 100:
                    ano0 += 1900
            
            if ano1 is not None:
                if ano1 <= 50:
                    ano1 += 2000
                elif ano1 < 100:
                    ano1 += 1900
            
        else:
            ano0 = ano1 = None
    return [{
        "marca": marca_principal,
        "otras_marcas": otras_marcas,
        "modelo": modelo,
        "cilindrada": cilindrada,
        "año0": ano0,
        "año1": ano1
    }]
try:
    # Leer el archivo Excel
    df = pd.read_excel(excel_file)

    # Establecer conexión con la base de datos
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    for index, row in df.iterrows():
        # Procesar la columna 'Variante'
        compat_list = parse_variant(row['Variante'], row["Tipo de producto"])
        for compat_data in compat_list:
            # Manejar marcas
            if compat_data["marca"]:
                cursor.execute("SELECT id_marca FROM marcas WHERE nombre = %s", (compat_data["marca"],))
                marca_result = cursor.fetchone()
                if not marca_result:
                    cursor.execute("INSERT INTO marcas (nombre) VALUES (%s)", (compat_data["marca"],))
                    marca_id = cursor.lastrowid
                else:
                    marca_id = marca_result[0]
            else:
                marca_id = None

            # Manejar modelos
            if compat_data["modelo"]:
                cursor.execute("SELECT id_modelo FROM modelo WHERE nombre = %s AND marca = %s", 
                               (compat_data["modelo"], marca_id))
                modelo_result = cursor.fetchone()
                if not modelo_result:
                    cursor.execute("INSERT INTO modelo (nombre, marca) VALUES (%s, %s)", 
                                   (compat_data["modelo"], marca_id))
                    modelo_id = cursor.lastrowid
                else:
                    modelo_id = modelo_result[0]
            else:
                modelo_id = None
            
            # Manejar categoría
            cursor.execute("SELECT id_categoria FROM CATEGORIA WHERE nombre = %s", (row["Tipo de producto"],))
            categoria_result = cursor.fetchone()
            if not categoria_result:
                cursor.execute("INSERT INTO CATEGORIA (nombre) VALUES (%s)", (row["Tipo de producto"],))
                categoria_id = cursor.lastrowid
                
            else:
                categoria_id = categoria_result[0]

            if row["Código Barras"] == "":
                print("ENTRO")
                row["Código Barras"] = "No disponible"
            # Insertar datos en Productos
            insert_product_query = """
            INSERT INTO Productos (nombre, cantidad_TOTAl, codigo_producto, categoria)
            VALUES (%s, %s, %s, %s)
            """
            
            product_data = (row['Variante'], 0, row['Código Barras'], int(categoria_id))
            cursor.execute(insert_product_query, product_data)
            product_id = cursor.lastrowid
            
            # Insertar datos en compatibilidad_producto
            insert_compat_query = """
            INSERT INTO compatibilidad_producto (año0, año1, marca, modelo, cilindrada, producto)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            compat_values = (
                compat_data["año0"],
                compat_data["año1"],
                marca_id,
                modelo_id,
                compat_data["cilindrada"],
                product_id
            )
            cursor.execute(insert_compat_query, compat_values)

            # Manejar compatibilidad con otras marcas
            if compat_data["otras_marcas"] and isinstance(compat_data["otras_marcas"], list):
                for otra_marca in compat_data["otras_marcas"]:
                    cursor.execute("SELECT id_marca FROM marcas WHERE nombre = %s", (otra_marca,))
                    otra_marca_result = cursor.fetchone()
                    if not otra_marca_result:
                        cursor.execute("INSERT INTO marcas (nombre) VALUES (%s)", (otra_marca,))
                        otra_marca_id = cursor.lastrowid
                    else:
                        otra_marca_id = otra_marca_result[0]

                    insert_other_compat_query = """
                    INSERT INTO compatibilidad_producto (año0, año1, marca, modelo, cilindrada, producto)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    other_compat_values = (
                        compat_data["año0"],
                        compat_data["año1"],
                        otra_marca_id,
                        modelo_id,
                        compat_data["cilindrada"],
                        product_id
                    )
                    cursor.execute(insert_other_compat_query, other_compat_values)

            # Insertar datos en Precios
            insert_price_query = """
            INSERT INTO Precios (precio_cliente, costo_empresa, id_producto)
            VALUES (%s, %s, %s)
            """
            price_data = (row['Precio Venta'], 0, product_id)
            cursor.execute(insert_price_query, price_data)

    # Confirmar los cambios
    connection.commit()
    print("Datos importados con éxito.")

except Error as e:
    print(f"Error en la base de datos: {e}")
    if connection.is_connected():
        connection.rollback()
except Exception as ex:
    print(f"Error inesperado: {ex}")
finally:
    if 'cursor' in locals() and not cursor.close:
        cursor.close()
    if 'connection' in locals() and connection.is_connected():
        connection.close()
