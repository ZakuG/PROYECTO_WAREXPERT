import pandas as pd

# Cargar el archivo Excel
excel_file = 'LISTABSALE25.xlsx'

try:
    # Leer el archivo Excel
    df = pd.read_excel(excel_file)
    
    # Modificar los valores de la columna 'Tipo de producto'
    df["Tipo de producto"] = df["Tipo de producto"].replace({
        "ELECTRICOS": "ELECTRICO",
        "carroceria": "CARROCERIA",
        "EMP.": "EMPAQUETADURA",
        0: "SIN TIPO",
        "Sin Tipo": "SIN TIPO",
        "RODAMIENTO": "RODAMIENTOS"
    })
    # Obtener los tipos únicos
    tipos = set(df["Tipo de producto"])
    print(tipos)

    # Guardar los cambios en un nuevo archivo si es necesario
    df.to_excel("LISTABSALE25_actualizado.xlsx", index=False)

except Exception as e:
    print(f"Se produjo un error: {e}")
