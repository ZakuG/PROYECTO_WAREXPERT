from tkinter import Toplevel, Label, Frame, PhotoImage, filedialog, messagebox
from tkinter import ttk
from tkinter import *
import os
from PIL import Image, ImageTk  # Para manejar las imágenes correctamente
import mysql.connector
from io import BytesIO

# Modelo: Interacción con la base de datos
class ProductoModelo:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",  # Cambiar según configuración local
            database="Warexpert"
        )
        
        self.cursor = self.conn.cursor()

    def agregar_compatibilidad_producto(self, producto_id, año0, año1, marca, modelo, cilindrada):
        try:
            self.cursor.execute(
                "INSERT INTO compatibilidad_producto (año0, año1, marca, modelo, cilindrada, producto) VALUES (%s, %s, %s, %s, %s, %s)",
                (año0, año1, marca, modelo, cilindrada, producto_id)
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def agregar_producto(self, nombre, descripcion, codigo, precio, costo, largo, ancho, altura, imagenes):

        try:
            
            self.cursor.execute("INSERT INTO Productos (nombre, descripcion, codigo_producto) VALUES (%s, %s, %s)", (nombre, descripcion, codigo))
            producto_id = self.cursor.lastrowid
            
            self.cursor.execute("INSERT INTO Precios (precio_cliente, costo_empresa, id_producto) VALUES (%s, %s, %s)", (precio, costo, producto_id))
            self.cursor.execute("INSERT INTO Dimensiones (largo, ancho, altura, id_producto) VALUES (%s, %s, %s, %s)", (largo, ancho, altura, producto_id))
            
            for imagen_path in imagenes:
                with open(imagen_path, "rb") as imagen_file:
                    imagen_binaria = imagen_file.read()
                self.cursor.execute("INSERT INTO Imagenes (url_imagen, id_producto) VALUES (%s, %s)", (imagen_binaria, producto_id))

            self.conn.commit()
            return(producto_id)
        except Exception as e:
            self.conn.rollback()
            raise e
    def actualizar_producto(self, id_producto, producto, descripcion, codigo, precio, costo, largo, ancho, altura):
        try:
            self.cursor.execute("Update productos set nombre=%s, descripcion=%s, codigo_producto=%s where id_producto = %s", (producto, descripcion, codigo, id_producto))
            self.cursor.execute("update precios set precio_cliente=%s, costo_empresa=%s where id_producto=%s", (precio, costo, id_producto))
            self.cursor.execute("update dimensiones set largo=%s, ancho=%s, altura=%s where id_producto=%s", (largo, ancho, altura, id_producto))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        
    def actualizar_compatibilidad(self, cilindrada, año0, año1, id):
        try:
            self.cursor.execute("Update compatibilidad_producto set cilindrada=%s ,año0=%s, año1=%s where id_compatibilidad_producto = %s", (cilindrada, año0, año1, id))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def agregar_marca(self, nombre, imagenes):
        try:
            if not imagenes:
                imagenes = None
                self.cursor.execute("INSERT INTO Marcas (nombre, imagen) VALUES (%s, %s)", (nombre, imagenes))
                self.conn.commit()
            else:
                self.cursor.execute("INSERT INTO Marcas (nombre, imagen) VALUES (%s, %s)", (nombre, imagenes[0]))
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        
    def agregar_modelo(self, nombre, marca, imagen):
        try:
            # Verifica si se proporciona una imagen
            imagen_dato = imagen[0] if imagen else None

            # Ejecuta la consulta con la imagen o None
            self.cursor.execute(
                "INSERT INTO Modelo (nombre, marca, imagen) VALUES (%s, %s, %s)", 
                (nombre, marca, imagen_dato)
            )
            self.conn.commit()

        except Exception as e:
            # En caso de error, revierte la transacción y lanza la excepción
            self.conn.rollback()
            raise e
    def buscar_marca(self):
        self.cursor.execute("SELECT id_marca, nombre FROM marcas")
        return self.cursor.fetchall()
    
    def buscar_modelo(self, id):
        self.cursor.execute(f"SELECT id_modelo, nombre FROM modelo where marca={id}")
        return self.cursor.fetchall()

    def buscar_producto(self, nombre):
        # Divide el texto en palabras clave
        try:
            palabras_clave = nombre.split()

            # Construye las condiciones dinámicamente
            condiciones = []
            parametros = []

            for palabra in palabras_clave:
                if palabra.isdigit():  # Si la palabra es un año (entero)
                    condiciones.append("(cp.año0 <= %s and cp.año1 >= %s)")
                    parametros.extend([int(palabra), int(palabra)])
                elif self.es_float(palabra):  # Si la palabra es una cilindrada (flotante)
                    condiciones.append("ABS(cp.cilindrada - %s) < 0.01")  # Margen de error para flotantes
                    parametros.append(float(palabra))
                else:
                    like_pattern = f"%{palabra}%"
                    condiciones.append("(m.nombre LIKE %s OR mo.nombre LIKE %s OR p.nombre LIKE %s OR p.descripcion LIKE %s)")
                    parametros.extend([like_pattern, like_pattern, like_pattern, like_pattern])

            

            # Combina las condiciones con AND para que todas las palabras coincidan
            where_clause = " AND ".join(condiciones)

            # Consulta final
            consulta = f"""
                            SELECT 
                                p.codigo_producto, m.nombre, mo.nombre, 
                                p.nombre, p.descripcion, cp.cilindrada, 
                                cp.año0, cp.año1, p.Cantidad_Total, 
                                pr.precio_cliente, pr.costo_empresa, p.id_producto, cp.id_compatibilidad_producto
                                FROM 
                                    Productos as p 
                                left join 
                                    compatibilidad_producto as cp 
                                on 
                                    cp.producto=p.id_producto 
                                left join 
                                    Marcas as m 
                                on 
                                    cp.marca=m.id_marca 
                                left join 
                                    modelo as mo 
                                on 
                                    cp.modelo=mo.id_modelo 
                                left join 
                                    Precios as pr 
                                on 
                                    pr.id_producto=p.id_producto
                                
                                WHERE 
                                    p.cantidad_total>0 and {where_clause}
                        """
            # Ejecuta la consulta
            self.cursor.execute(consulta, tuple(parametros))

            return self.cursor.fetchall()
        except Exception as e:
            return(None)

    def es_float(self, valor):
        try:
            float(valor)
            return True
        except ValueError:
            return False

    def buscar_producto_marca(self, id_marca=None, id_modelo=None, año=None, cilindrada=None):
        try:
            # Construye las condiciones dinámicamente
            condiciones = []
            parametros = []

            if id_marca:
                condiciones.append("m.id_marca = %s")
                parametros.append(id_marca)

            if id_modelo:
                condiciones.append("mo.id_modelo = %s")
                parametros.append(id_modelo)

            if año:
                condiciones.append("(cp.año0 <= %s AND cp.año1 >= %s)")
                parametros.extend([int(año), int(año)])

            if cilindrada:
                condiciones.append("ABS(cp.cilindrada - %s) < 0.01")  # Margen de error para flotantes
                parametros.append(float(cilindrada))

            # Si no hay condiciones, evita ejecutar una consulta sin filtro
            if not condiciones:
                raise ValueError("Se debe proporcionar al menos un criterio de búsqueda.")

            # Combina las condiciones con AND
            where_clause = " AND ".join(condiciones)

            # Consulta final
            consulta = f"""
                            SELECT 
                                p.codigo_producto, m.nombre, mo.nombre, 
                                p.nombre, p.descripcion, cp.cilindrada, 
                                cp.año0, cp.año1, p.Cantidad_Total, 
                                pr.precio_cliente, pr.costo_empresa, p.id_producto, cp.id_compatibilidad_producto
                                FROM 
                                    Productos as p
                                left join 
                                    compatibilidad_producto as cp 
                                on 
                                    cp.producto=p.id_producto 
                                left join 
                                    Marcas as m 
                                on 
                                    cp.marca=m.id_marca 
                                left join 
                                    modelo as mo 
                                on 
                                    cp.modelo=mo.id_modelo 
                                left join 
                                    Precios as pr 
                                on 
                                    pr.id_producto=p.id_producto 
                                WHERE 
                                    p.cantidad_total>0 and {where_clause}
                        """

            # Ejecuta la consulta
            self.cursor.execute(consulta, tuple(parametros))
            return self.cursor.fetchall()
        except Exception as e:
            return None


    def buscar_product(self, nombre):
        # Divide el texto en palabras clave
        try:
            palabras_clave = nombre.split()

            # Construye las condiciones dinámicamente
            condiciones = []
            parametros = []

            for palabra in palabras_clave:
                if palabra.isdigit():  # Si la palabra es un año (entero)
                    condiciones.append("(cp.año0 <= %s and cp.año1 >= %s)")
                    parametros.extend([int(palabra), int(palabra)])
                elif self.es_float(palabra):  # Si la palabra es una cilindrada (flotante)
                    condiciones.append("ABS(cp.cilindrada - %s) < 0.01")  # Margen de error para flotantes
                    parametros.append(float(palabra))
                else:
                    palabra = str(palabra)
                    like_pattern = f"%{palabra}%"
                    condiciones.append("(m.nombre LIKE %s OR mo.nombre LIKE %s OR p.nombre LIKE %s OR p.descripcion LIKE %s)")
                    parametros.extend([like_pattern, like_pattern, like_pattern, like_pattern])

            # Combina las condiciones con AND para que todas las palabras coincidan
            where_clause = " AND ".join(condiciones)

            # Consulta final
            consulta = f"""
                SELECT 
                    p.codigo_producto, m.nombre, mo.nombre, p.nombre, 
                    p.descripcion, cp.cilindrada, cp.año0, cp.año1, 
                    p.Cantidad_Total, p.id_producto, pr.precio_cliente, 
                    pr.costo_empresa, d.largo, d.ancho, d.altura, 
                    m.id_marca, mo.id_modelo
                FROM 
                    Productos as p 
                left join 
                    compatibilidad_producto as cp 
                on 
                    cp.producto=p.id_producto 
                LEFT JOIN 
                    Marcas as m 
                ON 
                    cp.marca=m.id_marca 
                LEFT JOIN 
                    modelo as mo 
                ON 
                    cp.modelo=mo.id_modelo 
                LEFT JOIN
                    precios as pr
                ON
                    pr.id_producto=p.id_producto
                LEFT JOIN
                    dimensiones as d
                ON
                    d.id_producto=p.id_producto
                WHERE 
                    {where_clause}
            """

            # Ejecuta la consulta
            self.cursor.execute(consulta, tuple(parametros))
            return self.cursor.fetchall()
        except Exception as e:
            return(None)
    def buscar_detalles_producto(self, id_producto, id_compatibilidad):
        if id_compatibilidad != "No disponible":

            consulta = """
                SELECT 
                    p.nombre, p.descripcion, p.codigo_producto,
                    u.pasillo, u.seccion, u.piso, u.cantidad,
                    pr.precio_cliente, pr.costo_empresa,
                    d.largo, d.ancho, d.altura,
                    m.nombre, mo.nombre, cp.cilindrada, cp.año0, cp.año1, u.id_ubicacion, p.id_producto
                FROM Productos p
                left join compatibilidad_producto as cp on cp.producto = p.id_producto 
                LEFT JOIN Ubicaciones u ON p.id_producto = u.id_producto
                LEFT JOIN Precios pr ON p.id_producto = pr.id_producto
                LEFT JOIN Dimensiones d ON p.id_producto = d.id_producto
                LEFT JOIN MARCAS AS M ON M.ID_MARCA = cP.MARCA
                LEFT JOIN MODELO AS MO ON MO.ID_MODELO = cP.MODELO
                WHERE p.id_producto = %s and cp.id_compatibilidad_producto = %s
            """
            self.cursor.execute(consulta, (id_producto, id_compatibilidad, ))
            return self.cursor.fetchall()
        else:

            consulta = """
                SELECT 
                    p.nombre, p.descripcion, p.codigo_producto,
                    u.pasillo, u.seccion, u.piso, u.cantidad,
                    pr.precio_cliente, pr.costo_empresa,
                    d.largo, d.ancho, d.altura,
                    m.nombre, mo.nombre, cp.cilindrada, cp.año0, cp.año1, u.id_ubicacion, p.id_producto
                FROM Productos p
                left join compatibilidad_producto as cp on cp.producto = p.id_producto 
                LEFT JOIN Ubicaciones u ON p.id_producto = u.id_producto
                LEFT JOIN Precios pr ON p.id_producto = pr.id_producto
                LEFT JOIN Dimensiones d ON p.id_producto = d.id_producto
                LEFT JOIN MARCAS AS M ON M.ID_MARCA = cP.MARCA
                LEFT JOIN MODELO AS MO ON MO.ID_MODELO = cP.MODELO
                WHERE p.id_producto = %s
            """
            self.cursor.execute(consulta, (id_producto,))
            return self.cursor.fetchall()

    def obtener_compatibilidad(self, id_producto, id_compatibilidad):
        consulta = """
            SELECT 
                m.nombre, mo.nombre, cp.cilindrada, cp.año0, cp.año1
            FROM compatibilidad_producto as cp
            LEFT JOIN MARCAS AS M ON M.ID_MARCA = cP.MARCA
            LEFT JOIN MODELO AS MO ON MO.ID_MODELO = cP.MODELO
            WHERE cp.producto = %s and cp.id_compatibilidad_producto != %s
        """
        self.cursor.execute(consulta, (id_producto, id_compatibilidad, ))
        return self.cursor.fetchall()
    def obtener_compatibilidad_actualizar(self, id_producto):
        consulta = """
            SELECT 
                m.id_marca, m.nombre, mo.id_modelo, mo.nombre, cp.cilindrada, cp.año0, cp.año1, cp.id_compatibilidad_producto
            FROM compatibilidad_producto as cp
            LEFT JOIN MARCAS AS M ON M.ID_MARCA = cP.MARCA
            LEFT JOIN MODELO AS MO ON MO.ID_MODELO = cP.MODELO
            WHERE cp.producto = %s 
        """
        self.cursor.execute(consulta, (id_producto, ))
        return self.cursor.fetchall()
    def buscar_imagenes_producto(self, id_producto):
        
        consulta = """
            SELECT 
                url_imagen
            FROM Imagenes
            WHERE id_producto = %s
        """
        self.cursor.execute(consulta, (id_producto,))
        # Extraemos solo las rutas de las imágenes de la consulta


        return [imagen[0] for imagen in self.cursor.fetchall()]

    def eliminar_compatibilidad(self, id):
        try:
            
            self.cursor.execute(f"delete from compatibilidad_producto where id_compatibilidad_producto={id}")
            self.conn.commit()

        except Exception as e:

            self.conn.rollback()
            raise e
        
    def eliminar(self, id):
        try:
            
            self.cursor.execute(f"delete from productos where id_producto={id}")
            self.conn.commit()

        except Exception as e:

            self.conn.rollback()
            raise e

    def buscar_product_carro(self, id_producto, compatibilidad):
        if compatibilidad != "No disponible":
            query = """
            SELECT p.codigo_producto, p.nombre, m.nombre AS marca, mo.nombre AS modelo, 
                pr.precio_cliente
            FROM Productos p
            left JOIN compatibilidad_producto as cp ON cp.producto = p.id_producto
            left JOIN marcas m ON cp.marca = m.id_marca
            left JOIN modelo mo ON cp.modelo = mo.id_modelo
            JOIN Precios pr ON p.id_producto = pr.id_producto
            WHERE p.id_producto = %s and cp.id_compatibilidad_producto = %s
            """
            self.cursor.execute(query, (id_producto, compatibilidad[0],))
            result = self.cursor.fetchone()
            
            if result:
                # Si la marca o el modelo son None, los cambiamos a "No disponible"
                marca = result[2] if result[2] is not None else "No disponible"
                modelo = result[3] if result[3] is not None else "No disponible"
                
                # Regresamos los resultados con la marca y el modelo actualizados
                return (result[0], result[1], marca, modelo, result[4])
        else:
            query = """
            SELECT p.codigo_producto, p.nombre, m.nombre AS marca, mo.nombre AS modelo, 
                pr.precio_cliente
            FROM Productos p
            left JOIN compatibilidad_producto as cp ON cp.producto = p.id_producto
            left JOIN marcas m ON cp.marca = m.id_marca
            left JOIN modelo mo ON cp.modelo = mo.id_modelo
            JOIN Precios pr ON p.id_producto = pr.id_producto
            WHERE p.id_producto = %s
            """
            self.cursor.execute(query, (id_producto,))
            result = self.cursor.fetchone()
            
            if result:
                # Si la marca o el modelo son None, los cambiamos a "No disponible"
                marca = result[2] if result[2] is not None else "No disponible"
                modelo = result[3] if result[3] is not None else "No disponible"
                
                # Regresamos los resultados con la marca y el modelo actualizados
                return (result[0], result[1], marca, modelo, result[4])
        return None
    
    def update_ubi(self, id_ubi, cantidad, id_producto):
        # Consulta para obtener la cantidad actual en la ubicación
        query1 = """
        SELECT cantidad FROM ubicaciones WHERE id_ubicacion = %s
        """
        self.cursor.execute(query1, (id_ubi,))
        resultado = self.cursor.fetchone()
        
        if resultado is None:
            raise ValueError(f"No se encontró una ubicación con ID {id_ubi}")
        
        cantidad_actual = int(resultado[0])
        nueva_cantidad = cantidad_actual - int(cantidad)

        if nueva_cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa.")

        if nueva_cantidad == 0:
            # Eliminar la ubicación si la cantidad llega a cero
            query2 = """
            DELETE FROM ubicaciones WHERE id_ubicacion = %s
            """
            self.cursor.execute(query2, (id_ubi,))
        else:
            # Actualizar la cantidad si no llega a cero
            query2 = """
            UPDATE ubicaciones SET cantidad = %s WHERE id_ubicacion = %s
            """
            self.cursor.execute(query2, (nueva_cantidad, id_ubi))
        
        # Actualizar la cantidad total en la tabla Productos
        query3 = """
        UPDATE Productos
        SET cantidad_total = (
            SELECT COALESCE(SUM(cantidad), 0)
            FROM ubicaciones
            WHERE id_producto = %s
        )
        WHERE id_producto = %s
        """
        self.cursor.execute(query3, (id_producto, id_producto))
        
        self.conn.commit()


    def guardar_carro_modelo(self, carrito, id_medio_pago, total):
        try:
            # Insertar en la tabla `carro`

            query_carro = "INSERT INTO carro (medio_pago, monto) VALUES (%s, %s)"
            self.cursor.execute(query_carro, (int(id_medio_pago), float(total),))
            id_carro = self.cursor.lastrowid

            # Insertar en la tabla `detalle_carro`
            query_detalle = """
            INSERT INTO detalle_carro (producto, cantidad, total_producto, carro)
            VALUES (%s, %s, %s, %s)
            """
            for producto in carrito:
                self.cursor.execute(query_detalle, (
                    int(producto['id_producto']), int(producto['cantidad']),
                    float(producto['precio_total']), id_carro,
                ))

            self.conn.commit()
            return None
        except Exception as e:
            self.conn.rollback()
            return None

    def revertir_stock(self, id_ubi, cantidad, id_producto, pasillo=None, seccion=None, piso=None):
        try:
            # Validar que la cantidad sea un número entero válido
            if cantidad is None or not isinstance(cantidad, int):
                raise ValueError("La cantidad debe ser un número entero.")

            # Verificar si la ubicación existe
            query1 = """
            SELECT cantidad FROM ubicaciones WHERE id_ubicacion = %s
            """
            self.cursor.execute(query1, (id_ubi,))
            resultado = self.cursor.fetchone()

            if resultado is None:
                # Si la ubicación no existe, crearla
                if pasillo is None or seccion is None or piso is None:
                    raise ValueError("Pasillo, sección y piso son necesarios para crear una nueva ubicación.")
                
                if cantidad <= 0:
                    raise ValueError("No se puede crear una ubicación con cantidad 0 o negativa.")
                
                query2 = """
                INSERT INTO ubicaciones (pasillo, seccion, piso, id_producto, cantidad)
                VALUES (%s, %s, %s, %s, %s)
                """
                self.cursor.execute(query2, (pasillo, seccion, piso, id_producto, cantidad))
            else:
                # Si la ubicación existe, actualizar la cantidad
                cantidad_actual = int(resultado[0])
                nueva_cantidad = cantidad_actual + cantidad

                if nueva_cantidad < 0:
                    raise ValueError("La cantidad no puede ser negativa.")

                query2 = """
                UPDATE ubicaciones SET cantidad = %s WHERE id_ubicacion = %s
                """
                self.cursor.execute(query2, (nueva_cantidad, id_ubi))

            # Actualizar la cantidad total en la tabla Productos
            query3 = """
            UPDATE Productos
            SET cantidad_total = (
                SELECT COALESCE(SUM(cantidad), 0)
                FROM ubicaciones
                WHERE id_producto = %s
            )
            WHERE id_producto = %s
            """
            self.cursor.execute(query3, (id_producto, id_producto))
            
            # Confirmar los cambios
            self.conn.commit()

        except Exception as e:
            self.conn.rollback()  # Revertir transacciones en caso de error
            raise Exception(f"No se pudo revertir el stock: {e}")


    def cerrar_conexion(self):
        self.cursor.close()
        self.conn.close()
# Vista: Interfaz gráfica
class ProductoVista:
    def __init__(self, root, controlador):
        self.root = root
        self.controlador = controlador
        
        # Pestañas
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        # Pestaña de registro
        self.tab_registro = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_registro, text="Registrar Producto")
        self.crear_pestaña_registro()

        # Pestaña asignar ubicacion
        self.tab_ubicacion = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_ubicacion, text="Asignar Ubicacion")
        self.crear_pestaña_ubicacion()

        # Pestaña de búsqueda
        self.tab_busqueda = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_busqueda, text="Buscar Producto")
        self.crear_pestaña_busqueda()
    	
        # Pestaña de búsqueda por marca
        self.tab_busqueda_marca = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_busqueda_marca, text="Buscar Producto por Modelo")
        self.crear_pestaña_busqueda_marca()

        # Pestaña de marca
        self.tab_marca = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_marca, text="Registrar Marca")
        self.crear_pestaña_marca()

        # Pestaña Modelo
        self.tab_modelo = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_modelo, text="Registrar Modelo")
        self.crear_pestaña_modelo()

        #pestaña carro
        self.tab_carro = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_carro, text="Carro")
        self.crear_pestaña_carro()
        self.carrito = []  
        self.total_final = 0.0

        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 10, "bold"))
        style.configure("TEntry", font=("Arial", 10, "bold"))
        style.configure("TCombobox", font=("Arial", 10, "bold"))
        style.configure("TButton", font=("Arial", 10, "bold"))


    def crear_pestaña_registro(self):
        self.id=[]
        datos_frame = Frame(self.tab_registro)
        datos_frame.pack(fill="x", padx=10, pady=10)
        # Campos de entrada
        ttk.Label(datos_frame, text="Nombre:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.nombre_entry = ttk.Entry(datos_frame, width=75)
        self.nombre_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(datos_frame, text="Descripción:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.descripcion_entry = ttk.Entry(datos_frame, width=75)
        self.descripcion_entry.grid(row=1, column=1, padx=5, pady=5)


        ttk.Label(datos_frame, text="Código Producto:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.codigo_entry = ttk.Entry(datos_frame, width=75)
        self.codigo_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(datos_frame, text="Precio Cliente:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.precio_entry = ttk.Entry(datos_frame)
        self.precio_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(datos_frame, text="Costo Empresa:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.costo_entry = ttk.Entry(datos_frame)
        self.costo_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(datos_frame, text="Largo (cm):").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.largo_entry = ttk.Entry(datos_frame)
        self.largo_entry.grid(row=5, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(datos_frame, text="Ancho (cm):").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.ancho_entry = ttk.Entry(datos_frame)
        self.ancho_entry.grid(row=6, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(datos_frame, text="Altura (cm):").grid(row=7, column=0, padx=5, pady=5, sticky="w")
        self.altura_entry = ttk.Entry(datos_frame)
        self.altura_entry.grid(row=7, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(datos_frame, text="Imágenes:").grid(row=8, column=0, padx=5, pady=5, sticky="w")
        self.imagenes_list = []
        self.imagenes_button = ttk.Button(datos_frame, text="Cargar Imágenes", command=self.cargar_imagenes)
        self.imagenes_button.grid(row=8, column=1, padx=5, pady=5, sticky="w")

        # Botón para guardar
        self.guardar_button = ttk.Button(datos_frame, text="Guardar", command=self.guardar_producto)
        self.guardar_button.grid(row=9, column=0, columnspan=2, pady=10)

        self.compatibilidad_frame = Frame(self.tab_registro)
        self.compatibilidad_frame.pack(fill="x", padx=10, pady=10)

    def cargar_marca_compatibilicad_combobox(self):
        # Obtener marcas desde la base de datos
        modelos = self.controlador.obtener_marcas()  # Este método debe devolver una lista de tuplas (id_marca, nombre)
        if modelos:
            self.compatibilidad_marcas_combobox["values"] = [f"{id_marca} - {nombre_marca}" for id_marca, nombre_marca in modelos]
        else:
            self.compatibilidad_marcas_combobox["values"] = []
            messagebox.showwarning("Advertencia", "No se encontraron modelos registrados.")

    def actualizar_modelos_compatibilidad(self, event=None):
        """Actualiza los modelos según la marca seleccionada para compatibilidad."""
        marca_seleccionada = self.compatibilidad_marcas_combobox.get()
        if not marca_seleccionada:
            return
        id_marca = int(marca_seleccionada.split(" - ")[0])
        modelos = self.controlador.obtener_modelos(id_marca)
        if modelos:
            self.compatibilidad_modelo_combobox["values"] = [
                f"{id_modelo} - {nombre_modelo}" for id_modelo, nombre_modelo in modelos
            ]
            self.compatibilidad_modelo_combobox.state(["!disabled"])
        else:
            self.compatibilidad_modelo_combobox["values"] = []
            self.compatibilidad_modelo_combobox.state(["disabled"])
            messagebox.showwarning("Advertencia", "No se encontraron modelos asociados.")

        self.compatibilidad_modelo_combobox.set("")

    def agregar_compatibilidad(self):
        """Agregar una compatibilidad a la tabla correspondiente."""
        try:
            marca_seleccionada = self.compatibilidad_marcas_combobox.get()
            modelo_seleccionado = self.compatibilidad_modelo_combobox.get()
            if not marca_seleccionada:
                return messagebox.showwarning("Advertencia", "Seleccione marca.")
            else:
                id_marca = int(marca_seleccionada.split(" - ")[0])
            if modelo_seleccionado:
                id_modelo = int(modelo_seleccionado.split(" - ")[0])
            else:
                id_modelo = None
            

            año1 = self.compatibilidad_año1_entry.get()
            año2 = self.compatibilidad_año2_entry.get()
            cilindrada = float(self.compatibilidad_cilindrada_entry.get()) if self.compatibilidad_cilindrada_entry.get() else None

            
            if not año1 and not año2:
                año1, año2 = None, None  # Ningún valor ingresado
            elif not año1:
                año2 = int(año2)
                año1 = año2  # Si año1 está vacío, se iguala a año2
            elif not año2:
                año1 = int(año1)
                año2 = año1
            elif año1 > año2:
                return messagebox.showwarning("Advertencia", "El año 1 debe ser menor al año 2.")
            else:
                año1 = int(año1)
                año2 = int(año2)

            producto_id = self.id[0]  # Variable almacenada del producto recién creado
            self.controlador.agregar_compatibilidad_producto(producto_id, año1, año2, id_marca, id_modelo, cilindrada)
            messagebox.showinfo("Éxito", "Compatibilidad agregada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo agregar compatibilidad: {e}")

    def cargar_imagenes(self):
        files = filedialog.askopenfilenames(filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")])
        if files:
            self.imagenes_list = files
            messagebox.showinfo("Imágenes cargadas", f"Se cargaron {len(files)} imágenes.")
        else:
            messagebox.showwarning("Advertencia", "No se seleccionaron imágenes.")

    def guardar_producto(self):
        self.id=[]
        
        if not self.nombre_entry.get():
             return messagebox.showwarning("Advertencia", "Debe agregar un nombre al producto.")
        if not self.codigo_entry.get():
             return messagebox.showwarning("Advertencia", "Debe agregar un codigo del producto.")
        if not self.precio_entry.get():
            return messagebox.showwarning("Advertencia", "Debe agregar un precio al producto.")
        if not self.costo_entry.get():
            return messagebox.showwarning("Advertencia", "Debe agregar un costo al producto.")   

        

        ttk.Label(self.compatibilidad_frame, text=f"Agregar Compatibilidad al Producto: {self.nombre_entry.get()} - {self.codigo_entry.get()}").grid(row=10, column=0, columnspan=4, pady=10)
    
        ttk.Label(self.compatibilidad_frame, text="Marca:").grid(row=11, column=0, padx=5, pady=5, sticky="w")
        self.compatibilidad_marcas_combobox = ttk.Combobox(self.compatibilidad_frame, state="readonly")
        self.compatibilidad_marcas_combobox.grid(row=11, column=1, padx=5, pady=5, sticky="w")
        self.cargar_marca_compatibilicad_combobox()

        self.compatibilidad_marcas_combobox.bind("<<ComboboxSelected>>", self.actualizar_modelos_compatibilidad)

        ttk.Label(self.compatibilidad_frame, text="Modelo:").grid(row=11, column=2, padx=5, pady=5, sticky="w")
        self.compatibilidad_modelo_combobox = ttk.Combobox(self.compatibilidad_frame, state="readonly")
        self.compatibilidad_modelo_combobox.grid(row=11, column=3, padx=5, pady=5, sticky="w")
        self.compatibilidad_modelo_combobox.state(["disabled"])

        ttk.Label(self.compatibilidad_frame, text="Año Inicio:").grid(row=12, column=0, padx=5, pady=5, sticky="w")
        self.compatibilidad_año1_entry = ttk.Entry(self.compatibilidad_frame)
        self.compatibilidad_año1_entry.grid(row=12, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.compatibilidad_frame, text="Año Fin:").grid(row=12, column=2, padx=5, pady=5, sticky="w")
        self.compatibilidad_año2_entry = ttk.Entry(self.compatibilidad_frame)
        self.compatibilidad_año2_entry.grid(row=12, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(self.compatibilidad_frame, text="Cilindrada:").grid(row=13, column=0, padx=5, pady=5, sticky="w")
        self.compatibilidad_cilindrada_entry = ttk.Entry(self.compatibilidad_frame)
        self.compatibilidad_cilindrada_entry.grid(row=13, column=1, padx=5, pady=5, sticky="w")

        self.agregar_compatibilidad_button = ttk.Button(
            self.compatibilidad_frame, 
            text="Agregar Compatibilidad", 
            command=self.agregar_compatibilidad
        )
        self.agregar_compatibilidad_button.grid(row=14, column=0, columnspan=4, pady=10, sticky="w")


        datos = {
            "nombre": self.nombre_entry.get(),
            "descripcion": self.descripcion_entry.get() or None,
            "codigo": self.codigo_entry.get(),
            "precio": self.precio_entry.get(),
            "costo": self.costo_entry.get(),
            "largo": float(self.largo_entry.get()) if self.largo_entry.get() else None,
            "ancho": float(self.ancho_entry.get()) if self.ancho_entry.get() else None,
            "altura": float(self.altura_entry.get()) if self.altura_entry.get() else None, 
            "imagenes": self.imagenes_list
        }
        
        id = self.controlador.guardar_producto(datos)
        self.id.append(id)
        try:
            self.buscar_producto()
        except Exception:
            None
        try:
            self.buscar_producto_marca()
        except Exception:
            None

        try:
            self.buscar_product()
        except Exception:
            None

    def crear_pestaña_ubicacion(self):
        # Campo de búsqueda
        ttk.Label(self.tab_ubicacion, text="Buscar Producto:").pack(padx=5, pady=5)
        self.busqueda_entry_ubicacion = ttk.Entry(self.tab_ubicacion, width=65)
        self.busqueda_entry_ubicacion.pack(padx=5, pady=5)

        self.buscar_button = ttk.Button(self.tab_ubicacion, text="Buscar", command=self.buscar_product)
        self.buscar_button.pack(pady=5)

        # Frame para Treeview y Scrollbars
        tree_frame_ubicacion = ttk.Frame(self.tab_ubicacion)
        tree_frame_ubicacion.pack(fill="both", expand=True, padx=5, pady=5)

        # Scrollbars
        x_scroll = ttk.Scrollbar(tree_frame_ubicacion, orient="horizontal")
        x_scroll.pack(side="bottom", fill="x")

        y_scroll = ttk.Scrollbar(tree_frame_ubicacion, orient="vertical")
        y_scroll.pack(side="right", fill="y")

        # Treeview
        self.resultados_tree_ubicacion = ttk.Treeview(
            tree_frame_ubicacion,
            columns=("Código", "Marca", "Modelo", "Nombre", "Descripción", "Cilindrada", "Año 1", "Año 2", "Cantidad Total"),
            show="headings",
            xscrollcommand=x_scroll.set,
            yscrollcommand=y_scroll.set
        )
        self.resultados_tree_ubicacion.pack(fill="both", expand=True)

        # Configurar encabezados
        encabezados = [
            "Código Producto", "Marca", "Modelo", "Nombre", "Descripción", 
            "Cilindrada", "Año 1", "Año 2", "Cantidad Total"
        ]
        for col, texto in zip(self.resultados_tree_ubicacion["columns"], encabezados):
            self.resultados_tree_ubicacion.heading(col, text=texto)
            self.resultados_tree_ubicacion.column(col, minwidth=100, width=120, stretch=True)

        # Configurar scrollbars
        x_scroll.config(command=self.resultados_tree_ubicacion.xview)
        y_scroll.config(command=self.resultados_tree_ubicacion.yview)

        # Ajustar tamaño dinámico de columnas
        self.tab_ubicacion.pack_propagate(False)

        # Doble clic en un producto para ver detalles
        self.resultados_tree_ubicacion.bind("<Double-1>", self.agregar_ubicacion_producto)



    def buscar_product(self):
        nombre = self.busqueda_entry_ubicacion.get()
        resultados = self.controlador.buscar_product(nombre)
        for item in self.resultados_tree_ubicacion.get_children():
            self.resultados_tree_ubicacion.delete(item)
        for row in resultados:
    # Reemplaza valores nulos con 'No disponible'
            row = [value if value is not None else "No disponible" for value in row]
            self.resultados_tree_ubicacion.insert("", "end", values=row)


    def agregar_ubicacion_producto(self, event):
        item = self.resultados_tree_ubicacion.selection()
        if not item:
            messagebox.showwarning("Advertencia", "Seleccione un producto.")
            return

        producto = self.resultados_tree_ubicacion.item(item[0], "values")
        id_producto = producto[9]
        
        ubicacion_window = Toplevel(self.root)
        ubicacion_window.title(f"Asignar Ubicación - {producto[1]} {producto[2]} {producto[3]}")
        ubicacion_window.geometry("400x300")

        ubicacion_window.resizable(False, False)
        ubicacion_window.attributes("-fullscreen", False)

        # Campos para asignar ubicación
        ttk.Label(ubicacion_window, text="Pasillo:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        pasillo_entry = ttk.Entry(ubicacion_window)
        pasillo_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(ubicacion_window, text="Sección:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        seccion_entry = ttk.Entry(ubicacion_window)
        seccion_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(ubicacion_window, text="Piso:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        piso_entry = ttk.Entry(ubicacion_window)
        piso_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(ubicacion_window, text="Cantidad:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        cantidad_entry = ttk.Entry(ubicacion_window)
        cantidad_entry.grid(row=3, column=1, padx=5, pady=5)

        def guardar_ubicacion():
            pasillo = pasillo_entry.get()
            seccion = seccion_entry.get()
            piso = piso_entry.get()
            cantidad = cantidad_entry.get()

            if not (pasillo and seccion and piso and cantidad):
                messagebox.showerror("Error", "Todos los campos son obligatorios.")
                return

            try:
                cantidad = int(cantidad)
                self.controlador.asignar_ubicacion(id_producto, pasillo, seccion, piso, cantidad)
                messagebox.showinfo("Éxito", "Ubicación asignada correctamente.")
                ubicacion_window.destroy()
            except ValueError:
                messagebox.showerror("Error", "La cantidad debe ser un número entero.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
            try:
                self.buscar_producto()
            except Exception:
                None
            try:
                self.buscar_producto_marca()
            except Exception:
                None

            try:
                self.buscar_product()
            except Exception:
                None

        def actualizar_producto():
            compatibilidad = self.controlador.obtener_compatibilidad(id_producto)
            cilindrada_entry_list = []
            año_1_entry_list = []
            año_2_entry_list = []
            id_compatibilidad_list = []

            editar_window = Toplevel(self.root)
            editar_window.title(f"Editar Producto - {producto[1]} {producto[2]} {producto[3]}")
            editar_window.geometry("800x600")
            editar_window.resizable(False, False)
            editar_window.attributes("-fullscreen", False)

            editar_window.resizable(False, False)
            editar_window.attributes("-fullscreen", False)

            # Canvas para scroll
            canvas = Canvas(editar_window)
            canvas.pack(side="left", fill="both", expand=True)

            # Scrollbar
            scrollbar = Scrollbar(editar_window, orient="vertical", command=canvas.yview)
            scrollbar.pack(side="right", fill="y")
            canvas.configure(yscrollcommand=scrollbar.set)

            # Frame interno para contenido
            contenidoa_frame = Frame(canvas)

            # Configuración del canvas para el frame interno
            canvas.create_window((0, 0), window=contenidoa_frame, anchor="nw")

            # Actualizar el scroll region
            def actualizar_scroll_region1(event):
                canvas.configure(scrollregion=canvas.bbox("all"))

            contenidoa_frame.bind("<Configure>", actualizar_scroll_region1)

            # Vincular la rueda del mouse al canvas
            def on_mousewheel1(event):
                canvas.yview_scroll(-1 * (event.delta // 120), "units")

            editar_window.bind_all("<MouseWheel>", on_mousewheel1)

            producto_frame = Frame(contenidoa_frame)
            producto_frame.pack(fill="x", padx=10, pady=10)

            ttk.Label(producto_frame, text="Producto:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
            producto1_entry = ttk.Entry(producto_frame)
            producto1_entry.insert(0, producto[3])
            producto1_entry.grid(row=0, column=1, padx=5, pady=5)

            ttk.Label(producto_frame, text="Descripción:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="w")
            descripcion1_entry = ttk.Entry(producto_frame)
            descripcion1_entry.insert(0, producto[4])
            descripcion1_entry.grid(row=1, column=1, padx=5, pady=5)

            ttk.Label(producto_frame, text="Código Producto:", font=("Arial", 10, "bold")).grid(row=2, column=0, padx=5, pady=5, sticky="w")
            codigo1_entry = ttk.Entry(producto_frame)
            codigo1_entry.insert(0, producto[0])
            codigo1_entry.grid(row=2, column=1, padx=5, pady=5)

            precios_frame = Frame(contenidoa_frame)
            precios_frame.pack(fill="x", padx=10, pady=10)

            ttk.Label(precios_frame, text="Precio Cliente:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
            precio1_entry = ttk.Entry(precios_frame)
            precio1_entry.insert(0, producto[10])
            precio1_entry.grid(row=0, column=1, padx=5, pady=5)

            ttk.Label(precios_frame, text="Costo Empresa:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="w")
            costo1_entry = ttk.Entry(precios_frame)
            costo1_entry.insert(0, producto[11])
            costo1_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

            dimensiones_frame = Frame(contenidoa_frame)
            dimensiones_frame.pack(fill="x", padx=10, pady=10)

            ttk.Label(dimensiones_frame, text="Largo (cm):", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
            largo1_entry = ttk.Entry(dimensiones_frame)
            largo1_entry.insert(0, producto[12])
            largo1_entry.grid(row=0, column=1, padx=5, pady=5)

            ttk.Label(dimensiones_frame, text="Ancho (cm):", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="w")
            ancho1_entry = ttk.Entry(dimensiones_frame)
            ancho1_entry.insert(0, producto[13])
            ancho1_entry.grid(row=1, column=1, padx=5, pady=5)

            ttk.Label(dimensiones_frame, text="Altura (cm):", font=("Arial", 10, "bold")).grid(row=2, column=0, padx=5, pady=5, sticky="w")
            altura1_entry = ttk.Entry(dimensiones_frame)
            altura1_entry.insert(0, producto[14])
            altura1_entry.grid(row=2, column=1, padx=5, pady=5)

            
            
            if compatibilidad:

                marcas_frame = Frame(contenidoa_frame)
                marcas_frame.pack(fill="x", padx=10, pady=10)
                Label(marcas_frame, text="Compatible con:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
                print("AAA")
                i = 0
                for compatible in compatibilidad:

                    compa_frame = Frame(contenidoa_frame)
                    compa_frame.pack(fill="x", padx=10, pady=10)

                    # Crear variables independientes para cada iteración
                    id_compatibilidad_list.append(compatible[7])
                    Label(compa_frame, text=f"{compatible[1]} - {compatible[3]}"  if compatible[3] else compatible[1], font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
                    ttk.Button(compa_frame, text="Eliminar Compatibilidad", command=lambda id=compatible[7]: eliminar_compatibilidad(id)).grid(row=0, column=1)
                    # Campos adicionales
                    ttk.Label(compa_frame, text="Cilindrada:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="w")
                    cilindrada1_entry = ttk.Entry(compa_frame)
                    cilindrada1_entry.insert(0, compatible[4] if compatible[4] is not None else "")
                    cilindrada1_entry.grid(row=1, column=1, padx=5, pady=5)
                    cilindrada_entry_list.append(cilindrada1_entry)

                    ttk.Label(compa_frame, text="Año 1:", font=("Arial", 10, "bold")).grid(row=1, column=2, padx=5, pady=5, sticky="w")
                    año11_entry = ttk.Entry(compa_frame)
                    año11_entry.insert(0, compatible[5] if compatible[5] is not None else "")
                    año11_entry.grid(row=1, column=3, padx=5, pady=5)
                    año_1_entry_list.append(año11_entry)

                    ttk.Label(compa_frame, text="Año 2:", font=("Arial", 10, "bold")).grid(row=1, column=4, padx=5, pady=5, sticky="w")
                    año21_entry = ttk.Entry(compa_frame)
                    año21_entry.insert(0, compatible[6] if compatible[6] is not None else "")
                    año21_entry.grid(row=1, column=5, padx=5, pady=5)
                    año_2_entry_list.append(año21_entry)
                    
                    i += 1


            def agregar_compatibilidad_vista():

                def cargar_marca_add_compatibilicad_combobox():
                    # Obtener marcas desde la base de datos
                    modelos = self.controlador.obtener_marcas()  # Este método debe devolver una lista de tuplas (id_marca, nombre)
                    if modelos:
                        compatibilidad_add_marcas_combobox["values"] = [f"{id_marca} - {nombre_marca}" for id_marca, nombre_marca in modelos]
                    else:
                        compatibilidad_add_marcas_combobox["values"] = []
                        messagebox.showwarning("Advertencia", "No se encontraron modelos registrados.")

                def actualizar_modelos_add_compatibilidad(event=None):
                    """Actualiza los modelos según la marca seleccionada para compatibilidad."""
                    marca_seleccionada = compatibilidad_add_marcas_combobox.get()
                    if not marca_seleccionada:
                        return
                    id_marca = int(marca_seleccionada.split(" - ")[0])
                    modelos = self.controlador.obtener_modelos(id_marca)
                    if modelos:
                        compatibilidad_add_modelo_combobox["values"] = [
                            f"{id_modelo} - {nombre_modelo}" for id_modelo, nombre_modelo in modelos
                        ]
                        compatibilidad_add_modelo_combobox.state(["!disabled"])
                    else:
                        compatibilidad_add_modelo_combobox["values"] = []
                        compatibilidad_add_modelo_combobox.state(["disabled"])
                        messagebox.showwarning("Advertencia", "No se encontraron modelos asociados.")

                    compatibilidad_add_modelo_combobox.set("")

                def agregar_compatibilidad_funcion():
                
                    marca_seleccionada = compatibilidad_add_marcas_combobox.get()
                    modelo_seleccionado = compatibilidad_add_modelo_combobox.get()
                    if not marca_seleccionada:
                        return messagebox.showwarning("Advertencia", "Seleccione marca.")
                    else:
                        id_marca = int(marca_seleccionada.split(" - ")[0])
                    if modelo_seleccionado:
                        id_modelo = int(modelo_seleccionado.split(" - ")[0])
                    else:
                        id_modelo = None
                    

                    año1 = compatibilidad_add_año1_entry.get()
                    año2 = compatibilidad_add_año2_entry.get()
                    cilindrada = float(compatibilidad_add_cilindrada_entry.get()) if compatibilidad_add_cilindrada_entry.get() else None

                    
                    if not año1 and not año2:
                        año1, año2 = None, None  # Ningún valor ingresado
                    elif not año1:
                        año2 = int(año2)
                        año1 = año2  # Si año1 está vacío, se iguala a año2
                    elif not año2:
                        año1 = int(año1)
                        año2 = año1
                    elif año1 > año2:
                        return messagebox.showwarning("Advertencia", "El año 1 debe ser menor al año 2.")
                    else:
                        año1 = int(año1)
                        año2 = int(año2)

                    self.controlador.agregar_compatibilidad_producto(id_producto, año1, año2, id_marca, id_modelo, cilindrada)
                    try:
                        self.buscar_producto()
                    except Exception:
                        None
                    try:
                        self.buscar_producto_marca()
                    except Exception:
                        None
                    try:
                        self.buscar_product()
                    except Exception:
                        None
                    try:
                        editar_window.destroy()
                        add_compatibilidad.destroy()
                        actualizar_producto()  # Vuelve a cargar la vista con las compatibilidades actualizadas
                    except Exception as e:
                        None
            
                
                add_compatibilidad = Toplevel(self.root)
                add_compatibilidad.title(f"Agregar Compatibilidad - {producto1_entry.get()}")
                add_compatibilidad.geometry("520x210")

                add_compatibilidad.resizable(False, False)
                add_compatibilidad.attributes("-fullscreen", False)

                add_compatibilidad_frame = Frame(add_compatibilidad)
                add_compatibilidad_frame.pack(fill="x", padx=10, pady=10)

                ttk.Label(add_compatibilidad_frame, text=f"Agregar Compatibilidad al Producto: {producto1_entry.get()} - {codigo1_entry.get()}").grid(row=0, column=0, columnspan=4, pady=10)
            
                ttk.Label(add_compatibilidad_frame, text="Marca:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
                compatibilidad_add_marcas_combobox = ttk.Combobox(add_compatibilidad_frame, state="readonly")
                compatibilidad_add_marcas_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="w")
                cargar_marca_add_compatibilicad_combobox()

                compatibilidad_add_marcas_combobox.bind("<<ComboboxSelected>>", actualizar_modelos_add_compatibilidad)

                ttk.Label(add_compatibilidad_frame, text="Modelo:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
                compatibilidad_add_modelo_combobox = ttk.Combobox(add_compatibilidad_frame, state="readonly")
                compatibilidad_add_modelo_combobox.grid(row=1, column=3, padx=5, pady=5, sticky="w")
                compatibilidad_add_modelo_combobox.state(["disabled"])

                ttk.Label(add_compatibilidad_frame, text="Año 1:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
                compatibilidad_add_año1_entry = ttk.Entry(add_compatibilidad_frame)
                compatibilidad_add_año1_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

                ttk.Label(add_compatibilidad_frame, text="Año 2:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
                compatibilidad_add_año2_entry = ttk.Entry(add_compatibilidad_frame)
                compatibilidad_add_año2_entry.grid(row=2, column=3, padx=5, pady=5, sticky="w")

                ttk.Label(add_compatibilidad_frame, text="Cilindrada:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
                compatibilidad_add_cilindrada_entry = ttk.Entry(add_compatibilidad_frame)
                compatibilidad_add_cilindrada_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")

                agregar_compatibilidad_add_button = ttk.Button(
                    add_compatibilidad_frame, 
                    text="Agregar Compatibilidad", 
                    command=agregar_compatibilidad_funcion
                )
                agregar_compatibilidad_add_button.grid(row=4, column=0, columnspan=4, pady=10, sticky="w")


            def eliminar_compatibilidad(id):

                self.controlador.eliminar_compatibilidad(id)

                try:
                    self.buscar_producto()
                except Exception:
                    None
                try:
                    self.buscar_producto_marca()
                except Exception:
                    None

                try:
                    self.buscar_product()
                except Exception:
                    None
                try:
                    editar_window.destroy()
                    actualizar_producto()  # Vuelve a cargar la vista con las compatibilidades actualizadas
                except Exception as e:
                    None
                
            def actualizar_producto_en_base():
                try:
                    # Obtener los valores del formulario
                    i = 0
                    id_producto = producto[9]
                    for compat in id_compatibilidad_list:
                        
                        # Manejo de la cilindrada
                        cilindrada = cilindrada_entry_list[i].get()
                        cilindrada = float(cilindrada) if cilindrada and cilindrada not in ["", None] else None

                        # Manejo de los años
                        try:
                            año1 = int(año_1_entry_list[i].get()) if año_1_entry_list[i].get() not in ["", "No disponible"] else None
                        except ValueError:
                            año1 = None

                        try:
                            año2 = int(año_2_entry_list[i].get()) if año_2_entry_list[i].get() not in ["", "No disponible"] else None
                        except ValueError:
                            año2 = None

                        # Si ambos años están vacíos, asignarles None
                        if año1 == "" and año2 == "":
                            año1, año2 = None, None  # Ambos vacíos
                        elif año1 is None and año2 is not None:
                            año1 = año2  # Si falta año1, usar año2
                        elif año2 is None and año1 is not None:
                            año2 = año1  # Si falta año2, usar año1
                        elif año1 is not None and año2 is not None and año1 > año2:
                            return messagebox.showwarning("Advertencia", "El año 1 debe ser menor al año 2.")
                        

                        # Actualización de compatibilidad
                        self.controlador.actualizar_compatibilidad(
                            cilindrada if cilindrada else None,
                            año1 if año1 else None,
                            año2 if año2 else None,
                            id_compatibilidad_list[i]
                        )
                        i += 1

                    if not producto1_entry.get():
                        messagebox.showwarning("Advertencia", "Debe agregar un nombre al producto.")
                        return
                    if not codigo1_entry.get():
                        messagebox.showwarning("Advertencia", "Debe agregar un código del producto.")
                        return
                    if not precio1_entry.get():
                        messagebox.showwarning("Advertencia", "Debe agregar un precio al producto.")
                        return
                    if not costo1_entry.get():
                        messagebox.showwarning("Advertencia", "Debe agregar un costo al producto.")
                        return
                    producto_nombre = producto1_entry.get()
                    descripcion = descripcion1_entry.get()
                    codigo = codigo1_entry.get()
                    precio = precio1_entry.get()
                    costo = costo1_entry.get()
                    largo = largo1_entry.get()
                    if largo == "No disponible":
                        largo = None
                    else:
                        largo = float(largo)
                    ancho = ancho1_entry.get()
                    if ancho == "No disponible":
                        ancho = None
                    else:
                        ancho = float(ancho)
                    altura = altura1_entry.get()
                    if altura == "No disponible":
                        altura = None
                    else:
                        altura = float(altura)

                    # Intentar actualizar el producto
                    datos_actualizados = {
                        "id_producto": id_producto,
                        "producto": producto_nombre,
                        "descripcion": descripcion if descripcion else None,
                        "codigo": codigo,
                        "precio": float(precio),
                        "costo": float(costo),
                        "largo": largo if largo else None,
                        "ancho": ancho if ancho else None,
                        "altura": altura if altura else None
                    }

                    # Llamar al método del controlador
                    self.controlador.actualizar_producto(datos_actualizados)
                    ubicacion_window.destroy()
                    editar_window.destroy()  # Cerrar la ventana de edición
                    try:
                        self.buscar_producto()
                    except Exception:
                        None
                    try:
                        self.buscar_producto_marca()
                    except Exception:
                        None
                    try:
                        self.buscar_product()
                    except Exception:
                        None
                except Exception as e:
                    return messagebox.showerror("Error", f"No se pudo actualizar el producto: {e}")
            # Llamar a las funciones de inicialización
            
            boton_frame = Frame(contenidoa_frame)
            boton_frame.pack(fill="x", padx=3, pady=10)
            ttk.Button(boton_frame, text="Editar Producto", command=actualizar_producto_en_base).grid(row=0, column=0)
            ttk.Button(boton_frame, text="Agregar Compatibilidad", command=agregar_compatibilidad_vista).grid(row=0, column=1)
            

        def eliminar_producto():
            id_producto = producto[9]

            def eliminar_producto_en_base():
                self.controlador.eliminar_producto(int(id_producto))
                ubicacion_window.destroy()
                eliminar_window.destroy()  # Cerrar la ventana de edición
                try:
                    self.buscar_producto()
                except Exception:
                    None
                try:
                    self.buscar_producto_marca()
                except Exception:
                    None

                try:
                    self.buscar_product()
                except Exception:
                    None

            def cancelar_producto_en_base():
                ubicacion_window.destroy()
                eliminar_window.destroy()  # Cerrar la ventana de edición
                try:
                    self.buscar_producto()
                except Exception:
                    None
                try:
                    self.buscar_producto_marca()
                except Exception:
                    None

                try:
                    self.buscar_product()
                except Exception:
                    None


            eliminar_window = Toplevel(self.root)
            eliminar_window.title(f"Eliminar producto - {producto[1]} {producto[2]} {producto[3]}")
            eliminar_window.geometry("640x90")  # Ajustar tamaño de la ventana
            eliminar_window.resizable(False, False)
            eliminar_window.attributes("-fullscreen", False)
            eliminar_frame = Frame(eliminar_window)
            eliminar_frame.pack(fill="both", padx=4, pady=4)

            ttk.Label(eliminar_frame, text="¿Estás seguro? Esto borrará toda la información del producto, incluyendo dónde está guardado.", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=10)

            button_frame = Frame(eliminar_frame)
            button_frame.grid(row=1, column=0, pady=10, padx=10)

            ttk.Button(button_frame, text="Eliminar", command=eliminar_producto_en_base, width=15).grid(row=0, column=0, padx=10)
            ttk.Button(button_frame, text="Cancelar", command=cancelar_producto_en_base, width=15).grid(row=0, column=1, padx=10)
            
            button_frame.columnconfigure(0, weight=1)
            button_frame.columnconfigure(1, weight=1)

        ttk.Button(ubicacion_window, text="Guardar Ubicación", command=guardar_ubicacion).grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(ubicacion_window, text="Editar Producto", command=actualizar_producto).grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(ubicacion_window, text="Eliminar Producto", command=eliminar_producto).grid(row=6, column=0, columnspan=2, pady=10)
        
    def crear_pestaña_busqueda(self):
        # Campo de búsqueda
        ttk.Label(self.tab_busqueda, text="Buscar Producto:").pack(padx=5, pady=5)
        self.busqueda_entry = ttk.Entry(self.tab_busqueda, width=65)
        self.busqueda_entry.pack(padx=5, pady=5)

        self.buscar_button = ttk.Button(self.tab_busqueda, text="Buscar", command=self.buscar_producto)
        self.buscar_button.pack(pady=5)

        # Frame para Treeview y Scrollbars
        tree_frame = ttk.Frame(self.tab_busqueda)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Scrollbars
        x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal")
        x_scroll.pack(side="bottom", fill="x")

        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        y_scroll.pack(side="right", fill="y")

        # Treeview
        self.resultados_tree = ttk.Treeview(
            tree_frame,
            columns=("Código", "Marca", "Modelo", "Nombre", "Descripción", "Cilindrada", "Año 1", "Año 2", "Cantidad Total", "Precio", "Costo"),
            show="headings",
            xscrollcommand=x_scroll.set,
            yscrollcommand=y_scroll.set
        )

        # Encabezados
        encabezados = [
            "Código Producto", "Marca", "Modelo", "Nombre", "Descripción",
            "Cilindrada", "Año 1", "Año 2", "Cantidad Total", "Precio", "Costo"
        ]
        for col, texto in zip(self.resultados_tree["columns"], encabezados):
            self.resultados_tree.heading(col, text=texto)

        self.resultados_tree.pack(fill="both", expand=True)

        # Configurar scrollbars
        x_scroll.config(command=self.resultados_tree.xview)
        y_scroll.config(command=self.resultados_tree.yview)

        # Ajustar tamaño dinámico de columnas
        tree_frame.bind("<Configure>", lambda event: self.ajustar_columnas())

        # Doble clic en un producto para ver detalles
        self.resultados_tree.bind("<Double-1>", self.ver_detalles_producto)

    def ajustar_columnas(self):
        # Ajusta el ancho de las columnas proporcionalmente al tamaño del Treeview
        total_width = self.resultados_tree.winfo_width()
        num_columns = len(self.resultados_tree["columns"])

        if num_columns > 0:
            width_per_column = total_width // num_columns
            for col in self.resultados_tree["columns"]:
                self.resultados_tree.column(col, width=width_per_column)

    def buscar_producto(self):
        nombre = self.busqueda_entry.get()
        resultados = self.controlador.buscar_producto(nombre)
        for item in self.resultados_tree.get_children():
            self.resultados_tree.delete(item)
        for row in resultados:
        # Reemplaza valores nulos con 'No disponible'
            row = [value if value is not None else "No disponible" for value in row]
            self.resultados_tree.insert("", "end", values=row)

    def ver_detalles_producto(self, event):
        item = self.resultados_tree.selection()[0]
        id_producto = self.resultados_tree.item(item, "values")[11]
        id_compatibilidad = self.resultados_tree.item(item, "values")[12]
        self.controlador.mostrar_detalles_producto(id_producto, id_compatibilidad)

    def crear_pestaña_busqueda_marca(self):
        # Campo de búsqueda
        ttk.Label(self.tab_busqueda_marca, text="Buscar Producto:").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Combobox de marcas
        ttk.Label(self.tab_busqueda_marca, text="Marca:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.marcas2_combobox = ttk.Combobox(self.tab_busqueda_marca, state="readonly")
        self.marcas2_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.cargar_marca_combobox2()

        # Combobox de modelos
        ttk.Label(self.tab_busqueda_marca, text="Modelo:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.modelo2_combobox = ttk.Combobox(self.tab_busqueda_marca, state="readonly")
        self.modelo2_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.modelo2_combobox.state(["disabled"])
        self.marcas2_combobox.bind("<<ComboboxSelected>>", self.actualizar_modelos2)

        # Campo de entrada para año
        ttk.Label(self.tab_busqueda_marca, text="Año:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.año_marca_entry = ttk.Entry(self.tab_busqueda_marca)
        self.año_marca_entry.grid(row=3, column=1, padx=5, pady=5)

        # Campo de entrada para cilindrada
        ttk.Label(self.tab_busqueda_marca, text="Cilindrada:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.cilindrada_marca_entry = ttk.Entry(self.tab_busqueda_marca)
        self.cilindrada_marca_entry.grid(row=4, column=1, padx=5, pady=5)

        # Botón de búsqueda
        self.buscar_marca_button = ttk.Button(self.tab_busqueda_marca, text="Buscar", command=self.buscar_producto_marca)
        self.buscar_marca_button.grid(row=5, column=1, padx=5, pady=10)

        # Frame para Treeview y Scrollbars
        tree_frame_marca = ttk.Frame(self.tab_busqueda_marca)
        tree_frame_marca.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # Scrollbars
        x_scroll = ttk.Scrollbar(tree_frame_marca, orient="horizontal")
        x_scroll.grid(row=1, column=0, sticky="ew")

        y_scroll = ttk.Scrollbar(tree_frame_marca, orient="vertical")
        y_scroll.grid(row=0, column=1, sticky="ns")

        # Treeview
        self.resultados_marca1_tree = ttk.Treeview(
            tree_frame_marca,
            columns=("Código", "Marca", "Modelo", "Nombre", "Descripción", "Cilindrada", "Año 1", "Año 2", "Cantidad Total", "Precio", "Costo"),
            show="headings",
            xscrollcommand=x_scroll.set,
            yscrollcommand=y_scroll.set
        )
        self.resultados_marca1_tree.grid(row=0, column=0, sticky="nsew")

        # Configurar encabezados
        encabezados = [
            "Código Producto", "Marca", "Modelo", "Nombre", "Descripción",
            "Cilindrada", "Año 1", "Año 2", "Cantidad Total", "Precio", "Costo"
        ]
        for col, texto in zip(self.resultados_marca1_tree["columns"], encabezados):
            self.resultados_marca1_tree.heading(col, text=texto)
            self.resultados_marca1_tree.column(col, minwidth=100, width=120, stretch=True)

        # Configurar scrollbars
        x_scroll.config(command=self.resultados_marca1_tree.xview)
        y_scroll.config(command=self.resultados_marca1_tree.yview)

        # Ajustar tamaño dinámico de columnas
        self.tab_busqueda_marca.grid_rowconfigure(6, weight=1)
        self.tab_busqueda_marca.grid_columnconfigure(1, weight=1)
        tree_frame_marca.grid_rowconfigure(0, weight=1)
        tree_frame_marca.grid_columnconfigure(0, weight=1)

        # Doble clic en un producto para ver detalles
        self.resultados_marca1_tree.bind("<Double-1>", self.ver_detalles_producto_marca)

    def buscar_producto_marca(self):
        # Obtener valores de los campos
        marca_seleccionada = self.marcas2_combobox.get()
        modelo_seleccionado = self.modelo2_combobox.get()
        año = self.año_marca_entry.get()
        cilindrada = self.cilindrada_marca_entry.get()

        # Convertir marca y modelo a IDs (si están seleccionados)
        id_marca = int(marca_seleccionada.split(" - ")[0]) if marca_seleccionada else None
        id_modelo = int(modelo_seleccionado.split(" - ")[0]) if modelo_seleccionado else None

        # Realizar búsqueda con filtros
        resultados = self.controlador.buscar_producto_marca(id_marca, id_modelo, año, cilindrada)

        # Limpiar resultados anteriores
        for item in self.resultados_marca1_tree.get_children():
            self.resultados_marca1_tree.delete(item)

        # Mostrar resultados
        for row in resultados:
            row = [value if value is not None else "No disponible" for value in row]
            self.resultados_marca1_tree.insert("", "end", values=row)

    def cargar_marca_combobox2(self):
        # Obtener marcas desde la base de datos
        modelos = self.controlador.obtener_marcas()  # Este método debe devolver una lista de tuplas (id_marca, nombre)
        if modelos:
            self.marcas2_combobox["values"] = [f"{id_marca} - {nombre_marca}" for id_marca, nombre_marca in modelos]
        else:
            self.marcas2_combobox["values"] = []
            messagebox.showwarning("Advertencia", "No se encontraron modelos registrados.")

    def actualizar_modelos2(self, event=None):
        """Actualiza el combobox de modelos basado en la marca seleccionada y limpia la selección del modelo."""
        marca_seleccionada = self.marcas2_combobox.get()
        if not marca_seleccionada:
            return

        # Obtener el ID de la marca seleccionada
        id_marca = int(marca_seleccionada.split(" - ")[0])

        # Obtener los modelos asociados a la marca
        modelos = self.controlador.obtener_modelos(id_marca)  # Devuelve lista de tuplas (id_modelo, nombre)
        if modelos:
            self.modelo2_combobox["values"] = [f"{id_modelo} - {nombre_modelo}" for id_modelo, nombre_modelo in modelos]
            self.modelo2_combobox.state(["!disabled"])
        else:
            self.modelo2_combobox["values"] = []
            self.modelo2_combobox.state(["disabled"])
            messagebox.showwarning("Advertencia", "No se encontraron modelos asociados a esta marca.")

        # Limpiar la selección actual del combobox de modelos
        self.modelo2_combobox.set("")  # Borra la selección actual
        self.año_marca_entry.delete(0, "end")
        self.cilindrada_marca_entry.delete(0, "end")
    def ver_detalles_producto_marca(self, event):
        item = self.resultados_marca1_tree.selection()[0]
        id_producto = self.resultados_marca1_tree.item(item, "values")[11]
        id_compatibilidad = self.resultados_marca1_tree.item(item, "values")[12]
        self.controlador.mostrar_detalles_producto(id_producto, id_compatibilidad)

    def mostrar_detalles_producto(self, detalles, id_producto, compatibilidad, id_compatibilidad):
        detalles_window = Toplevel(self.root)
        detalles_window.title("Detalles del Producto")
        detalles_window.geometry("800x600")

        # Canvas para scroll
        canvas = Canvas(detalles_window)
        canvas.pack(side="left", fill="both", expand=True)

        # Scrollbar
        scrollbar = Scrollbar(detalles_window, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Frame interno para contenido
        contenedor = Frame(canvas)

        # Configuración del canvas para el frame interno
        canvas.create_window((0, 0), window=contenedor, anchor="nw")

        # Actualizar el scroll region
        def actualizar_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        contenedor.bind("<Configure>", actualizar_scroll_region)

        # Vincular la rueda del mouse al canvas
        def on_mousewheel(event):
            canvas.yview_scroll(-1 * (event.delta // 120), "units")

        detalles_window.bind_all("<MouseWheel>", on_mousewheel)

        # Información básica
        marca_frame = Frame(contenedor)
        marca_frame.pack(fill="x", padx=10, pady=10)
        Label(marca_frame, text="Marca:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        Label(marca_frame, text=detalles[0][12], font=("Arial", 10)).grid(row=0, column=1, sticky="w")

        Label(marca_frame, text="Modelo:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w")
        Label(marca_frame, text=detalles[0][13], font=("Arial", 10)).grid(row=1, column=1, sticky="w")

        Label(marca_frame, text="Cilindrada:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w")
        Label(marca_frame, text=detalles[0][14], font=("Arial", 10)).grid(row=2, column=1, sticky="w")

        Label(marca_frame, text="Año:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w")
        Label(marca_frame, text=f"{detalles[0][15]} - {detalles[0][16]}", font=("Arial", 10)).grid(row=3, column=1, sticky="w")
        
        info_frame = Frame(contenedor)
        info_frame.pack(fill="x", padx=10, pady=10)

        Label(info_frame, text="Nombre:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w")
        Label(info_frame, text=detalles[0][0], font=("Arial", 10)).grid(row=1, column=1, sticky="w")

        Label(info_frame, text="Descripción:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w")
        descripcion_texto = Text(info_frame, wrap="word", height=3, width=50, font=("Arial", 10))
        descripcion_texto.grid(row=2, column=1, sticky="w")
        scroll = Scrollbar(info_frame, command=descripcion_texto.yview)
        scroll.grid(row=2, column=2, sticky="ns")
        descripcion_texto.config(yscrollcommand=scroll.set)
        descripcion_texto.insert(END, detalles[0][1] if detalles[0][1] else "No disponible")
        descripcion_texto.config(state="disabled")

        Label(info_frame, text="Código:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        Label(info_frame, text=detalles[0][2], font=("Arial", 10)).grid(row=0, column=1, sticky="w")

        # Precios
        precios_frame = Frame(contenedor)
        precios_frame.pack(fill="x", padx=10, pady=10)
        Label(precios_frame, text="Precio Cliente:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        Label(precios_frame, text=f"${detalles[0][7]:.2f}", font=("Arial", 10)).grid(row=0, column=1, sticky="w")

        Label(precios_frame, text="Costo Empresa:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w")
        Label(precios_frame, text=f"${detalles[0][8]:.2f}", font=("Arial", 10)).grid(row=1, column=1, sticky="w")

        # Dimensiones
        dimensiones_frame = Frame(contenedor)
        dimensiones_frame.pack(fill="x", padx=10, pady=10)

        Label(dimensiones_frame, text="Dimensiones:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        Label(dimensiones_frame, text=f"{detalles[0][9]} cm x {detalles[0][10]} cm x {detalles[0][11]} cm", font=("Arial", 10)).grid(row=0, column=1, sticky="w")

        if compatibilidad:
            compatible_frame = Frame(contenedor)
            compatible_frame.pack(fill="x", padx=10, pady=10)
            Label(compatible_frame, text=f"Compatible con:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
            i=1
            for compatible in compatibilidad:
                Label(compatible_frame, text=f"- {compatible[0]} {compatible[1]}, Cilindrada: {compatible[2]}, Año: {compatible[3]} - {compatible[4]}", font=("Arial", 10, "bold")).grid(row=i, column=0, sticky="w")
                i += 1

        i = 1
        lista = []
        cantidades = []
        id_ubicaciones = []
        ubicacion = []
        for detalle in detalles:
            # Ubicación y cantidad
            ubicacion_frame = Frame(contenedor)
            ubicacion_frame.pack(fill="x", padx=10, pady=10)

            Label(ubicacion_frame, text=f"Ubicación {i}:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
            Label(ubicacion_frame, text=f"Pasillo {detalle[3]}, Sección {detalle[4]}, Piso {detalle[5]}", font=("Arial", 10)).grid(row=0, column=1, sticky="w")

            Label(ubicacion_frame, text="Cantidad:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w")
            Label(ubicacion_frame, text=detalle[6], font=("Arial", 10)).grid(row=1, column=1, sticky="w")
            lista.append(f"Ubicación {i}")
            ubicacion.append({"pasillo":detalle[3], "seccion":detalle[4], "piso":detalle[5]})
            cantidades.append(detalle[6])
            id_ubicaciones.append(detalle[17])
            i += 1

        ttk.Label(marca_frame, text="").grid(row=0, column=2, padx=140)  
        
        ttk.Label(marca_frame, text="Seleccione Ubicación:").grid(row=0, column=3, sticky="w")
        ubicaciones_combobox = ttk.Combobox(marca_frame, state="readonly")
        ubicaciones_combobox.grid(row=0, column=4)

        if len(lista)>0:
            ubicaciones_combobox["values"] = [element for element in lista]
        else:
            ubicaciones_combobox["values"] = []
            messagebox.showwarning("Advertencia", "No se encontraron ubicaciones registradas.")

        def actualizar_cantidad(event=None):
            """Actualiza el combobox de modelos basado en la marca seleccionada y limpia la selección del modelo."""
            ubi_seleccionada = ubicaciones_combobox.get()
            if not ubi_seleccionada:
                return
            try:
                # Obtener el ID de la marca seleccionada
                id_ubi = int(ubi_seleccionada.split(" ")[1]) - 1

                cantidad=cantidades[id_ubi]
                if cantidad > 0:
                    cantidad_combobox["values"] = [num for num in range(1, cantidad + 1)]
                    cantidad_combobox.set("")  # Limpiar la selección actual
                    cantidad_combobox.state(["!disabled"])
                else:
                    cantidad_combobox["values"] = []
                    cantidad_combobox.set("")  # Limpiar cualquier selección
                    cantidad_combobox.state(["disabled"])
                    messagebox.showwarning("Advertencia", "No se encontraron cantidades asociadas a esta ubicación.")

                # Limpiar la selección actual del combobox de modelos
                cantidad_combobox.set("")  # Borra la selección actual
            except ValueError:
                messagebox.showerror("Error", "No se pudo encontrar la ubicación seleccionada.")

        ubicaciones_combobox.bind("<<ComboboxSelected>>", actualizar_cantidad)

        ttk.Label(marca_frame, text="").grid(row=1, column=2, padx=140)  
        ttk.Label(marca_frame, text="Seleccione una Cantidad:").grid(row=1, column=3, sticky="w")
        cantidad_combobox = ttk.Combobox(marca_frame, state="readonly")
        cantidad_combobox.grid(row=1, column=4)
        cantidad_combobox.state(["disabled"])

        def agregar_al_carrito():
            id_ubi = ubicaciones_combobox.get()
            if not id_ubi:
                return
            # Obtener el ID de la marca seleccionada
            id_ubi = int(id_ubi.split(" ")[1]) - 1
            ubicacion1 = ubicacion[id_ubi]
            id_ubi = id_ubicaciones[id_ubi]
            cantidad = int(cantidad_combobox.get())
            self.añadir_al_carro(detalles[0][18], id_ubi, cantidad, ubicacion1, id_compatibilidad)
            detalles_window.destroy()
            try:
                self.buscar_producto()
            except Exception:
                None
            try:
                self.buscar_producto_marca()
            except Exception:
                None

            try:
                self.buscar_product()
            except Exception:
                None
            
                
           
        ttk.Label(marca_frame, text="").grid(row=2, column=2, padx=140)
        ttk.Button(marca_frame, text="Agregar al carrito", command=agregar_al_carrito).grid(row=2, column=3, columnspan=2)

        # Imagen del producto
        self.modelo = ProductoModelo()
        imagenes = self.modelo.buscar_imagenes_producto(id_producto)  # Obtener las imágenes desde la base de datos
        imagen_frame = Frame(contenedor)
        imagen_frame.pack(fill="x", padx=10, pady=10)

        imagen_actual = [0]  # Usamos una lista para que sea mutable y accesible dentro de las funciones locales

        
        def mostrar_imagen(indice):
            try:
                # Convierte los datos binarios en una imagen
                imagen_data = BytesIO(imagenes[indice])
                imagen = Image.open(imagen_data)
                imagen = imagen.resize((300, 300), Image.LANCZOS)
                imagen_tk = ImageTk.PhotoImage(imagen)

                # Actualiza la etiqueta de la imagen
                imagen_label.config(image=imagen_tk)
                imagen_label.image = imagen_tk  # Mantén la referencia para evitar que se elimine
                imagen_label.pack()

                # Actualiza la etiqueta del contador
                contador_label.config(text=f"Imagen {indice + 1} de {len(imagenes)}")
            except Exception as e:
                Label(imagen_frame, text=f"Error al cargar la imagen: {e}", font=("Arial", 10, "italic"), fg="red").pack()

        def imagen_anterior():
            if imagen_actual[0] > 0:
                imagen_actual[0] -= 1
                mostrar_imagen(imagen_actual[0])

        def imagen_siguiente():
            if imagen_actual[0] < len(imagenes) - 1:
                imagen_actual[0] += 1
                mostrar_imagen(imagen_actual[0])

        # Botones para navegar entre imágenes
        boton_anterior = Button(imagen_frame, text="Anterior", command=imagen_anterior)
        boton_anterior.pack(side="left", padx=5)

        boton_siguiente = Button(imagen_frame, text="Siguiente", command=imagen_siguiente)
        boton_siguiente.pack(side="right", padx=5)

        # Etiqueta para mostrar imágenes
        imagen_label = Label(imagen_frame)
        imagen_label.pack()

        # Etiqueta para el contador
        contador_label = Label(imagen_frame, text="")
        contador_label.pack()

        # Muestra la primera imagen
        mostrar_imagen(imagen_actual[0])

        detalles_window.mainloop()

    def crear_pestaña_marca(self):
        # Campos de entrada
        ttk.Label(self.tab_marca, text="Nombre:").grid(row=0, column=0, padx=5, pady=5)
        self.nombre_marca_entry = ttk.Entry(self.tab_marca)
        self.nombre_marca_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.tab_marca, text="Logo:").grid(row=1, column=0, padx=5, pady=5)
        self.imagenes_marcas_Entry = []
        self.imagenes_button = ttk.Button(self.tab_marca, text="Cargar Logo", command=self.cargar_imagenes_marca)
        self.imagenes_button.grid(row=1, column=1, padx=5, pady=5)

        # Botón para guardar
        self.guardar_button = ttk.Button(self.tab_marca, text="Guardar", command=self.guardar_marcas)
        self.guardar_button.grid(row=2, column=0, columnspan=2, pady=10)

    def cargar_imagenes_marca(self):
        files = filedialog.askopenfilenames(filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")])
        self.imagenes_marcas_Entry = files
        messagebox.showinfo("Imágenes cargadas", f"Se cargo {len(files)} imágen.")

    def guardar_marcas(self):
        datos = {
            "nombre": self.nombre_marca_entry.get(),
            "imagenes": self.imagenes_marcas_Entry
        }
        self.controlador.guardar_marcas(datos)
        self.nombre_marca_entry.delete(0, END)  # Limpia el campo de texto
        self.imagen_marca_entry = []
        try:
            self.cargar_marca_combobox2()
            self.actualizar_modelos2()
        except Exception:
            None 
        self.cargar_marcas_combobox()
        try:
            self.cargar_marca_compatibilicad_combobox()
            self.actualizar_modelos_compatibilidad()
        except Exception:
            None
        
  
    def crear_pestaña_modelo(self):
        # Campos de entrada
        ttk.Label(self.tab_modelo, text="Nombre:").grid(row=1, column=0, padx=5, pady=5)
        self.nombre_modelo_entry = ttk.Entry(self.tab_modelo)
        self.nombre_modelo_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self.tab_modelo, text="Marca:").grid(row=0, column=0, padx=5, pady=5)
        self.marca_combobox = ttk.Combobox(self.tab_modelo, state="readonly")
        self.marca_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.cargar_marcas_combobox()
        
        ttk.Label(self.tab_modelo, text="Imagen:").grid(row=2, column=0, padx=5, pady=5)
        self.imagen_modelo_entry = []
        self.imagenes_button = ttk.Button(self.tab_modelo, text="Cargar Imagen", command=self.cargar_imagenes_modelo)
        self.imagenes_button.grid(row=2, column=1, padx=5, pady=5)

        # Botón para guardar
        self.guardar_button = ttk.Button(self.tab_modelo, text="Guardar", command=self.guardar_modelo)
        self.guardar_button.grid(row=3, column=0, columnspan=2, pady=10)
    
    def cargar_marcas_combobox(self):
        # Obtener marcas desde la base de datos
        marcas = self.controlador.obtener_marcas()  # Este método debe devolver una lista de tuplas (id_marca, nombre)
        if marcas:
            self.marca_combobox["values"] = [f"{id_marca} - {nombre}" for id_marca, nombre in marcas]
        else:
            self.marca_combobox["values"] = []
            messagebox.showwarning("Advertencia", "No se encontraron marcas registradas.")

    def cargar_imagenes_modelo(self):
        files = filedialog.askopenfilenames(filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")])
        self.imagen_modelo_entry = files
        messagebox.showinfo("Imágenes cargadas", f"Se cargo {len(files)} imágen.")

    def guardar_modelo(self):
        if not self.nombre_modelo_entry.get():
            messagebox.showerror("Error", "El campo 'Nombre' es obligatorio.")
            return
        if not self.marca_combobox.get():
            messagebox.showerror("Error", "Debe seleccionar una marca.")
            return

        # Obtener id de la marca seleccionada
        marca_seleccionada = self.marca_combobox.get()
        id_marca = int(marca_seleccionada.split(" - ")[0])

        datos = {
            "nombre": self.nombre_modelo_entry.get(),
            "marca": id_marca,
            "imagenes": self.imagen_modelo_entry
        }
        self.controlador.guardar_modelo(datos)
        self.nombre_modelo_entry.delete(0, END)  # Limpia el campo de texto
        self.marca_combobox.set('')  # Restablece el combobox
        self.imagen_modelo_entry = []
        try:
            self.cargar_marca_combobox2()
            self.actualizar_modelos2()
        except Exception:
            None 
        self.cargar_marcas_combobox()
        try:
            self.cargar_marca_compatibilicad_combobox()
            self.actualizar_modelos_compatibilidad()
        except Exception:
            None
        
    
    def crear_pestaña_carro(self):
        columnas = ("codigo", "marca", "modelo", "nombre", "cantidad", "precio_unitario", "precio_total")
        self.carro_treeview = ttk.Treeview(
            self.tab_carro, columns=columnas, show="headings", height=15
        )
        self.carro_treeview.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        self.carro_treeview.heading("codigo", text="Código")
        self.carro_treeview.heading("marca", text="Marca")
        self.carro_treeview.heading("modelo", text="Modelo")
        self.carro_treeview.heading("nombre", text="Producto")
        self.carro_treeview.heading("cantidad", text="Cantidad")
        self.carro_treeview.heading("precio_unitario", text="Precio Unitario")
        self.carro_treeview.heading("precio_total", text="Total Producto")

        # Entrada para seleccionar medio de pago
        ttk.Label(self.tab_carro, text="Medio de Pago:").grid(row=1, column=0, padx=5, pady=5)
        self.medio_pago_combobox = ttk.Combobox(self.tab_carro, state="readonly")
        self.medio_pago_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.cargar_medios_pago()

        # Etiqueta para mostrar el total final
        self.total_label = ttk.Label(self.tab_carro, text="Total Final: $0.00", font=("Arial", 12, "bold"))
        self.total_label.grid(row=1, column=2, padx=5, pady=5, sticky="w")

        # Botón para guardar el carrito
        self.guardar_carro_button = ttk.Button(self.tab_carro, text="Guardar Carro", command=self.guardar_carro)
        self.guardar_carro_button.grid(row=1, column=3, padx=5, pady=5)
        # Nuevo botón: Eliminar producto seleccionado
        self.eliminar_producto_button = ttk.Button(self.tab_carro, text="Eliminar Producto", command=self.eliminar_producto_carro)
        self.eliminar_producto_button.grid(row=2, column=0, padx=5, pady=5)

        # Nuevo botón: Vaciar carrito completo
        self.vaciar_carro_button = ttk.Button(self.tab_carro, text="Vaciar Carrito", command=self.vaciar_carro)
        self.vaciar_carro_button.grid(row=2, column=1, padx=5, pady=5)

    def cargar_medios_pago(self):
        """Carga los medios de pago desde la base de datos."""
        medios_pago = self.controlador.obtener_medios_pago()
        self.medio_pago_combobox["values"] = [f"{id} - {nombre}" for id, nombre in medios_pago]

    def añadir_al_carro(self, id_producto, id_ubi, cantidad, ubicacion, compatibilidad):
        """Añade un producto al carrito."""
        
        producto = self.controlador.obtener_producto_carro(id_producto, id_ubi, cantidad, compatibilidad)
        if not producto:
            return messagebox.showerror("Error", "No se pudo encontrar el producto.")
        else:
            messagebox.showinfo("Éxito", "Producto agregado correctamente")

        # Calcular precio total por cantidad
        precio_total = producto[4] * cantidad
        # Agregar al carrito
        self.carrito.append({
            "codigo": producto[0],
            "marca": producto[2],
            "modelo": producto[3],
            "nombre": producto[1],
            "cantidad": cantidad,
            "precio_unitario": producto[4],
            "precio_total": precio_total,
            "id_producto": id_producto,
            "id_ubi": id_ubi,
            "pasillo": ubicacion["pasillo"],
            "seccion": ubicacion["seccion"],
            "piso": ubicacion["piso"]
        })

        # Actualizar total final
        self.total_final += precio_total
        self.actualizar_tabla_carro()

    def actualizar_tabla_carro(self):
        """Actualiza la tabla con los productos del carrito."""
        # Limpiar tabla
        for item in self.carro_treeview.get_children():
            self.carro_treeview.delete(item)

        # Insertar productos en la tabla
        for producto in self.carrito:
            self.carro_treeview.insert(
                "", "end",
                values=(
                    producto["codigo"], producto["marca"], producto["modelo"],
                    producto["nombre"], producto["cantidad"],
                    f"${producto['precio_unitario']:.2f}", f"${producto['precio_total']:.2f}"
                )
            )

        # Actualizar total final
        self.total_label.config(text=f"Total Final: ${self.total_final:.2f}")
    def guardar_carro(self):
        """Guarda el carrito en la base de datos."""
        medio_pago_seleccionado = self.medio_pago_combobox.get()
        if not medio_pago_seleccionado:
            return messagebox.showerror("Error", "Debe seleccionar un medio de pago.")

        id_medio_pago = int(medio_pago_seleccionado.split(" - ")[0])

        if not self.carrito:
            return messagebox.showwarning("Advertencia", "El carrito está vacío.")

        # Guardar en la base de datos

        exito = self.controlador.guardar_carro(self.carrito, id_medio_pago, self.total_final)
        if exito:
            self.carrito = []
            self.total_final = 0.0
            self.actualizar_tabla_carro()

    def eliminar_producto_carro(self):
        """Elimina el producto seleccionado del carrito."""
        # Obtener el elemento seleccionado del Treeview
        selected_item = self.carro_treeview.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Debe seleccionar un producto para eliminar.")
            return

        # Extraer datos del producto seleccionado
        try:
            producto = self.carro_treeview.item(selected_item, "values")
            codigo_producto = str(producto[0])  # Asegurar que sea cadena
            cantidad = int(producto[4])         # Convertir cantidad a entero
            precio_total = float(str(producto[6]).replace("$", "").replace(",", ""))  # Limpiar y convertir precio a flotante
        except (IndexError, ValueError):
            messagebox.showerror("Error", "Los datos del producto seleccionado son inválidos.")
            return

        # Buscar el producto en el carrito
        producto_a_eliminar = next(
            (
                p for p in self.carrito
                if p["codigo"] == codigo_producto
                and p["cantidad"] == cantidad
                and abs(p["precio_total"] - precio_total) < 0.01  # Comparación tolerante para flotantes
            ),
            None
        )

        if not producto_a_eliminar:
            messagebox.showerror("Error", "No se pudo encontrar el producto seleccionado en el carrito.")
            return
        # Revertir stock
        id_ubi = producto_a_eliminar["id_ubi"]
        id_producto = producto_a_eliminar["id_producto"]
        pasillo = producto_a_eliminar["pasillo"]
        seccion = producto_a_eliminar["seccion"]
        piso = producto_a_eliminar["piso"]

        self.controlador.revertir_stock(id_ubi, cantidad, id_producto, pasillo, seccion, piso)

        # Eliminar producto del carrito
        self.carrito.remove(producto_a_eliminar)
        self.total_final -= precio_total

        # Actualizar tabla del carrito y buscar productos si corresponde
        self.actualizar_tabla_carro()
        try:
            self.buscar_producto()
        except Exception:
            None
        try:
            self.buscar_producto_marca()
        except Exception:
            None

        try:
            self.buscar_product()
        except Exception:
            None

    def vaciar_carro(self):
        """Vacía todo el carrito."""
        if not self.carrito:
            return messagebox.showwarning("Advertencia", "El carrito ya está vacío.")

        # Revertir el stock de todos los productos
        for producto in self.carrito:
            self.controlador.revertir_stock(producto["id_ubi"], producto["cantidad"], producto["id_producto"], producto["pasillo"], producto["seccion"], producto["piso"])

        self.carrito = []
        self.total_final = 0.0
        self.actualizar_tabla_carro()
        try:
            self.buscar_producto()
        except Exception:
            None
        try:
            self.buscar_producto_marca()
        except Exception:
            None

        try:
            self.buscar_product()
        except Exception:
            None

# Controlador: Lógica para manejar interacciones
class ProductoControlador:
    def __init__(self, vista):
        self.modelo = ProductoModelo()
        self.vista = vista
        self.carro_activo = None  

    def revertir_stock(self, id_ubi, cantidad, id_producto, pasillo, seccion, piso):
        try:
            self.modelo.revertir_stock(id_ubi, cantidad, id_producto, pasillo, seccion, piso)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo revertir el stock: {e}")

    def agregar_compatibilidad_producto(self, producto_id, año1, año2, marca, modelo, cilindrada):
        try:
            self.modelo.agregar_compatibilidad_producto(producto_id, año1, año2, marca, modelo, cilindrada)
        except Exception as e:
            raise e

    def guardar_producto(self, datos):
        
        try:
            id = self.modelo.agregar_producto(
                datos["nombre"], datos["descripcion"], datos["codigo"],
                datos["precio"], datos["costo"], datos["largo"],
                datos["ancho"], datos["altura"], datos["imagenes"]
            )
            messagebox.showinfo("Éxito", "Producto registrado correctamente.")
            return(id)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar el producto: {e}")

    def eliminar_producto(self, id):
        try:
            self.modelo.eliminar(id)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el producto: {e}")

    def actualizar_producto(self, datos):
        try:
            self.modelo.actualizar_producto(
                datos["id_producto"],
                datos["producto"], datos["descripcion"], datos["codigo"],
                datos["precio"], datos["costo"],
                datos["largo"], datos["ancho"], datos["altura"]
            )
            messagebox.showinfo("Éxito", "Producto actualizado correctamente.")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el producto: {e}")

    def eliminar_compatibilidad(self, id):
        try:
            self.modelo.eliminar_compatibilidad(
                id
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar el producto: {e}")

    def actualizar_compatibilidad(self, cilindrada, año0, año1, id):
        try:
            self.modelo.actualizar_compatibilidad(
                cilindrada, año0, año1, id
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el producto: {e}")

    def guardar_marcas(self, datos):
        try:
            self.modelo.agregar_marca(
                datos["nombre"], datos["imagenes"]
            )
            messagebox.showinfo("Éxito", "Marca registrada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar la marca: {e}")

    def guardar_modelo(self, datos):
        try:
            self.modelo.agregar_modelo(
                datos["nombre"], datos["marca"], datos["imagenes"]
            )
            messagebox.showinfo("Éxito", "Modelo registrado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar el modelo: {e}")

    def buscar_producto(self, nombre):
        try:
            return self.modelo.buscar_producto(nombre)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo buscar el producto: {e}")
            return []

    def buscar_product(self, nombre):
        try:
            return self.modelo.buscar_product(nombre)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo buscar el producto: {e}")
            return []

    def buscar_producto_marca(self, id_marca, id_modelo, año, cilindrada):
        try:
            return self.modelo.buscar_producto_marca(id_marca, id_modelo, año, cilindrada)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo buscar el producto: {e}")
            return []

    def mostrar_detalles_producto(self, id_producto, id_compatibilidad):
        try:
            detalles = self.modelo.buscar_detalles_producto(id_producto, id_compatibilidad)
            compatibilidad = self.modelo.obtener_compatibilidad(id_producto, id_compatibilidad)
            self.vista.mostrar_detalles_producto(detalles, id_producto, compatibilidad, id_compatibilidad)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener los detalles del producto: {e}")

    def obtener_compatibilidad(self, id_producto):
        try:
            return self.modelo.obtener_compatibilidad_actualizar(id_producto)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo encontrar la compatibilidad: {e}")
            return []

    def asignar_ubicacion(self, id_producto, pasillo, seccion, piso, cantidad):
        try:
            # Verificar si la ubicación ya existe
            self.modelo.cursor.execute("""
                SELECT cantidad
                FROM Ubicaciones
                WHERE pasillo = %s AND seccion = %s AND piso = %s AND id_producto = %s
            """, (pasillo, seccion, piso, id_producto))
            
            resultado = self.modelo.cursor.fetchone()
            
            if resultado:  # Si existe, actualizar la cantidad
                nueva_cantidad = resultado[0] + cantidad
                self.modelo.cursor.execute("""
                    UPDATE Ubicaciones
                    SET cantidad = %s
                    WHERE pasillo = %s AND seccion = %s AND piso = %s AND id_producto = %s
                """, (nueva_cantidad, pasillo, seccion, piso, id_producto))
            else:  # Si no existe, insertar una nueva ubicación
                self.modelo.cursor.execute("""
                    INSERT INTO Ubicaciones (pasillo, seccion, piso, id_producto, cantidad)
                    VALUES (%s, %s, %s, %s, %s)
                """, (pasillo, seccion, piso, id_producto, cantidad))
            
            # Actualizar el total en la tabla Productos
            self.modelo.cursor.execute(f"""
                UPDATE Productos
                SET cantidad_total = (
                    SELECT SUM(cantidad)
                    FROM Ubicaciones
                    WHERE id_producto = {id_producto}
                )
                WHERE id_producto = {id_producto}
            """)
            
            self.modelo.conn.commit()
        except Exception as e:
            self.modelo.conn.rollback()
            raise e
    def obtener_marcas(self):
        try:
            return self.modelo.buscar_marca()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo buscar la marca: {e}")
            return []
        
    def obtener_modelos(self, id):
        try:
            return self.modelo.buscar_modelo(id)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo buscar el modelo: {e}")
            return []

    def obtener_medios_pago(self):
        query = "SELECT id_medio_pago, nombre FROM medio_pago"
        self.modelo.cursor.execute(query)
        return self.modelo.cursor.fetchall()
        
    def guardar_carro(self, carrito, id_medio_pago, total):
        
        try:
            self.modelo.guardar_carro_modelo(carrito, id_medio_pago, total)
            messagebox.showinfo("Éxito", "Carrito agregado correctamente")
            return True

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo agregar el carro: {e}")
            return False

    def obtener_producto_carro(self, id_producto, id_ubi, cantidad, compatibilidad):
        try:
            
            self.modelo.update_ubi(id_ubi, cantidad, id_producto)
            
            return self.modelo.buscar_product_carro(id_producto, compatibilidad)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener el producto: {e}")


    
# Inicialización
if __name__ == "__main__":
    root = Tk()
    root.title("Gestión de Productos")
    root.state('zoomed')
    root.resizable(True, True)
    root.attributes("-fullscreen", False)

    # Crea la vista y luego el controlador, pasando la vista al controlador
    controlador = ProductoControlador(None)  # Inicializa el controlador sin la vista aún

    # Crea la vista y luego asigna el controlador
    vista = ProductoVista(root, controlador)  # Pasa el controlador al inicializar la vista

    # Vincula el controlador a la vista
    controlador.vista = vista   # Vincula el controlador a la vista

    
    root.mainloop()
