from tkinter import Toplevel, Label, Frame, PhotoImage, filedialog, messagebox
from tkinter import ttk
from tkinter import *
import tkinter as tk 
import os
from PIL import Image, ImageTk  # Para manejar las imágenes correctamente
import mysql.connector
from io import BytesIO
from configparser import ConfigParser
from datetime import date

# Modelo: Interacción con la base de datos
class ProductoModelo:
    def __init__(self):
        if getattr(os.sys, 'frozen', False):  
            base_path = os.sys._MEIPASS  # Ruta temporal donde PyInstaller coloca los archivos
        else:
            base_path = os.path.dirname(__file__)  # Ruta del script actual

        config_path = os.path.join(base_path, "db_config.txt")
        print(f"Ruta de configuración: {config_path}") 
        # Verifica si el archivo existe
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"No se encontró el archivo de configuración: {config_path}")

        config = ConfigParser()
        config.read(config_path)  # Usar config_path en lugar de "db_config.txt"

        # Extraer valores
        host = config.get("mysql", "host")
        user = config.get("mysql", "user")
        password = config.get("mysql", "password")
        database = config.get("mysql", "database")

        # Establecer conexión con MySQL
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
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
    def cargar_imagenes_new(self, imagenes, id):
        try:
            for imagen_path in imagenes:
                with open(imagen_path, "rb") as imagen_file:
                    imagen_binaria = imagen_file.read()
                self.cursor.execute("INSERT INTO Imagenes (url_imagen, id_producto) VALUES (%s, %s)", (imagen_binaria, id))

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

    def agregar_marca(self, nombre):
        try:
            self.cursor.execute("INSERT INTO Marcas (nombre) VALUES (%s)", (nombre,))
            self.conn.commit()
            """else:
                with open(imagenes[0], "rb") as imagen_file:
                    imagen_binaria = imagen_file.read()
                self.cursor.execute("INSERT INTO Marcas (nombre, imagen) VALUES (%s, %s)", (nombre, imagen_binaria))
                self.conn.commit()"""
        except Exception as e:
            self.conn.rollback()
            raise e
        
    def agregar_modelo(self, nombre, marca):
        try:
    

            self.cursor.execute(
            "INSERT INTO Modelo (nombre, marca) VALUES (%s, %s)", 
            (nombre, marca))
            self.conn.commit()
            """else:
                with open(imagen[0], "rb") as imagen_file:
                        imagen_binaria = imagen_file.read()
                # Ejecuta la consulta con la imagen o None
                self.cursor.execute(
                    "INSERT INTO Modelo (nombre, marca, imagen) VALUES (%s, %s, %s)", 
                    (nombre, marca, imagen_binaria)
                )
                self.conn.commit()"""
        except Exception as e:
            # En caso de error, revierte la transacción y lanza la excepción
            self.conn.rollback()
            raise e
    def buscar_marca(self):
        self.cursor.execute("SELECT id_marca, nombre FROM marcas order by nombre")
        return self.cursor.fetchall()
    
    def buscar_modelo(self, id):
        self.cursor.execute(f"SELECT id_modelo, nombre FROM modelo where marca={id} order by nombre")
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
                    condiciones.append("(m.nombre LIKE %s OR mo.nombre LIKE %s OR p.nombre LIKE %s OR p.descripcion LIKE %s OR p.codigo_producto LIKE %s)")
                    parametros.extend([like_pattern, like_pattern, like_pattern, like_pattern, like_pattern])

            

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
                                    p.cantidad_total>0 and {where_clause} ORDER BY 
                                m.nombre, mo.nombre, p.nombre;
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
                                ORDER BY 
                                    m.nombre, mo.nombre, p.nombre;
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
                    like_pattern = f"%{palabra}%"
                    condiciones.append("(m.nombre LIKE %s OR mo.nombre LIKE %s OR p.nombre LIKE %s OR p.descripcion LIKE %s OR p.codigo_producto LIKE %s)")
                    parametros.extend([like_pattern, like_pattern, like_pattern, like_pattern, like_pattern])

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
                ORDER BY 
                    m.nombre, mo.nombre, p.nombre;
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
            ORDER BY 
                m.nombre, mo.nombre;
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
            ORDER BY 
                m.nombre, mo.nombre
        """
        self.cursor.execute(consulta, (id_producto, ))
        return self.cursor.fetchall()
    
    def buscar_logo(self, id_compatibilidad):

        consulta = """
            SELECT 
                m.imagen
            FROM marcas as m
            inner join compatibilidad_producto as cp
            on cp.marca = m.id_marca
            WHERE cp.id_compatibilidad_producto = %s
        """

        self.cursor.execute(consulta, (id_compatibilidad,))
        # Extraemos solo las rutas de las imágenes de la consulta


        return self.cursor.fetchone()

    def buscar_logo_marca(self, id):

        consulta = """
            SELECT 
                imagen
            FROM marcas
            where id_marca = %s
        """

        self.cursor.execute(consulta, (id,))
        # Extraemos solo las rutas de las imágenes de la consulta


        return self.cursor.fetchone()

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

    def buscar_imagenes_producto_id(self, id_producto):
        
        consulta = """
            SELECT 
                url_imagen, id_imagen
            FROM Imagenes
            WHERE id_producto = %s
        """
        self.cursor.execute(consulta, (id_producto,))
        # Extraemos solo las rutas de las imágenes de la consulta


        return self.cursor.fetchall()

    def eliminar_imagen_producto(self, id_producto, id_imagen):
        try:
            self.cursor.execute(f"delete from imagenes where id_imagen={id_imagen} and id_producto={id_producto}")
            self.conn.commit()

        except Exception as e:

            self.conn.rollback()
            raise e
        
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
            self.cursor.execute(query, (id_producto, compatibilidad,))
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


    def guardar_carro_modelo(self, carrito, id_medio_pago, total, id_usuario):
        try:
            # Insertar en la tabla `carro`

            query_carro = "INSERT INTO carro (medio_pago, monto, usuario) VALUES (%s, %s, %s)"
            self.cursor.execute(query_carro, (int(id_medio_pago), float(total), int(id_usuario),))
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

    def obtener_ventas_diarias(self):
        try:
            consulta = """
                SELECT 
                    u.nombre AS usuario,
                    SUM(dc.cantidad) AS productos_vendidos,
                    COUNT(DISTINCT c.id_carro) AS cantidad_ventas,
                    SUM(c.monto) AS monto_total
                FROM 
                    usuario u
                JOIN 
                    carro c ON u.id_usuario = c.usuario
                JOIN 
                    detalle_carro dc ON c.id_carro = dc.carro
                WHERE 
                    DATE(c.fecha) = CURDATE()
                GROUP BY 
                    u.id_usuario
                UNION ALL
                SELECT 
                    CASE mp.nombre
                        WHEN 'Efectivo' THEN 'Total Efectivo'
                        WHEN 'Tarjeta de Debito' THEN 'Total Débito'
                        WHEN 'Tarjeta de Credito' THEN 'Total Crédito'
                        WHEN 'Transferencia' THEN 'Total Transferencia'
                    END AS usuario,
                    NULL AS productos_vendidos,
                    NULL AS cantidad_ventas,
                    SUM(c.monto) AS monto_total_vendedor
                FROM 
                    medio_pago mp
                JOIN 
                    carro c ON mp.id_medio_pago = c.medio_pago
                WHERE 
                    DATE(c.fecha) = CURDATE()
                GROUP BY 
                    mp.nombre
                UNION ALL
                SELECT 
                    'Total General' AS usuario,
                    NULL AS productos_vendidos,
                    NULL AS cantidad_ventas,
                    SUM(c.monto) AS monto_total
                FROM 
                    carro c
                WHERE 
                    DATE(c.fecha) = CURDATE();
            """
            # Ejecuta la consulta
            self.cursor.execute(consulta)
            return self.cursor.fetchall()
        except Exception as e:
            return None

    """def guardar_cierre_caja(self, total_dia, total_efectivo, total_debito, total_credito, total_transferencia, cantidad_ventas, cantidad_articulos, ventas_por_usuario):
        try:
            # Insertar en la tabla `carro`
            query_cierre = 
                            INSERT INTO detalle_diario (
                                total_dia, total_efectivo,
                                total_debito, total_credito, total_tranfe, cantidad_ventas_total, cantidad_articulos_total, activa
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        
            self.cursor.execute(query_cierre, (total_dia, total_efectivo, total_debito, total_credito, total_transferencia, cantidad_ventas, cantidad_articulos, False,))
            id_cierre = self.cursor.lastrowid
            
            for usuario_data in ventas_por_usuario:
                cantidad_ventas_usuario = usuario_data['cantidad_ventas']
                cantidad_articulos_usuario = usuario_data['cantidad_productos']
                total_ventas_usuario = usuario_data['total_ventas']
                query_user= select id_usuario from usuario where nombre = %s
                self.cursor.execute(query_user, (usuario_data['usuario'],))  # Obtener el ID del usuario desde tu base de datos
                usuario_id= self.cursor.fetchall()
                # Insertar en la tabla `detalle_carro`

                query_detalle = 
                INSERT INTO detalle_diario_usuario  (detalle_diario, cantidad_ventas, cantidad_articulos, total_usuario, usuario)
                VALUES (%s, %s, %s, %s, %s)
                

                self.cursor.execute(query_detalle, (
                    int(id_cierre), int(cantidad_ventas_usuario),
                    int(cantidad_articulos_usuario), float(total_ventas_usuario), int(usuario_id[0]),))

            self.conn.commit()
            return None
        except Exception as e:

            self.conn.rollback()
            return None"""

    def cerrar_conexion(self):
        self.cursor.close()
        self.conn.close()
# Vista: Interfaz gráfica
class ProductoVista:
    def __init__(self, root, controlador):
        self.root = root
        self.controlador = controlador
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="yellow", foreground="black")
        style.map("Treeview.Heading", background=[("active", "yellow2")], foreground=[("active", "black")])
        style.configure("Treeview", 
                rowheight=25,  # Ajusta la altura de las filas
                bordercolor="black",  # Color del borde
                borderwidth=1,  # Ancho del borde
                background="white",  # Fondo de las filas
                fieldbackground="white")
        style.map("Treeview", 
          background=[("selected", "lightblue")],  # Fondo cuando la fila está seleccionada
          foreground=[("selected", "black")])
        style.layout("Custom.Treeview",
            [('Treeview.treearea', {'sticky': 'nswe'})])
        style.configure("Custom.TFrame", background="#F5F5DC")
        style.configure("TLabel", font=("Arial", 10, "bold"), background="beige")
        style.configure("TEntry", font=("Arial", 10, "bold"), bg="beige")
        style.configure("TCombobox", font=("Arial", 10, "bold"), bg="beige")
        style.configure("TButton", font=("Arial", 10, "bold"), bg="beige")
        style.configure("TNotebook", background="beige", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Arial", 10, "bold"), background="tan1", foreground="black")
        style.map("TNotebook.Tab", 
              background=[("selected", "tan4")],  # Café claro cuando está seleccionada
              foreground=[("selected", "black")])


        # Pestañas
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        self.notebook.bind("<<NotebookTabChanged>>", self.actualizar_pestaña)

        # Pestaña de registro
        self.tab_registro = ttk.Frame(self.notebook, style="Custom.TFrame")
        self.notebook.add(self.tab_registro, text="Registrar Producto")
        self.crear_pestaña_registro()

         # Pestaña de marca
        self.tab_marca = ttk.Frame(self.notebook, style="Custom.TFrame")
        self.notebook.add(self.tab_marca, text="Registrar Marca")
        self.crear_pestaña_marca()

        # Pestaña Modelo
        self.tab_modelo = ttk.Frame(self.notebook, style="Custom.TFrame")
        self.notebook.add(self.tab_modelo, text="Registrar Modelo")
        self.crear_pestaña_modelo()

        # Pestaña asignar ubicacion
        self.tab_ubicacion = ttk.Frame(self.notebook, style="Custom.TFrame")
        self.notebook.add(self.tab_ubicacion, text="Asignar Ubicacion")
        self.crear_pestaña_ubicacion()

        # Pestaña de búsqueda
        self.tab_busqueda = ttk.Frame(self.notebook, style="Custom.TFrame")
        self.notebook.add(self.tab_busqueda, text="Buscar Producto")
        self.crear_pestaña_busqueda()
    	
        # Pestaña de búsqueda por marca
        self.tab_busqueda_marca = ttk.Frame(self.notebook, style="Custom.TFrame")
        self.notebook.add(self.tab_busqueda_marca, text="Buscar Producto por Modelo")
        self.crear_pestaña_busqueda_marca()

       

        #pestaña carro
        self.tab_carro = ttk.Frame(self.notebook, style="Custom.TFrame")
        self.notebook.add(self.tab_carro, text="Carrito")
        self.crear_pestaña_carro()
        self.carrito = []  
        self.total_final = 0.0

        self.tab_detalle = ttk.Frame(self.notebook, style="Custom.TFrame")
        self.notebook.add(self.tab_detalle, text="Detalle Ventas")
        self.tab_detalle_venta()
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_programa)

    def crear_pestaña_registro(self):
        self.id=[]
        datos_frame = Frame(self.tab_registro, bg="beige")
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
        self.imagenes_button = tk.Button(datos_frame, text="Cargar Imágenes", bg="salmon4", fg="beige", bd=3, activebackground="coral4",  # Fondo al presionar
                                        activeforeground="beige", font=("Arial", 10, "bold"), command=self.cargar_imagenes)
        self.imagenes_button.grid(row=8, column=1, padx=5, pady=5, sticky="w")

        buttona_frame = Frame(self.tab_registro, bg="beige")
        buttona_frame.pack(fill="x")

        # Botón para guardar
        self.guardar_button = tk.Button(buttona_frame, text="Guardar", bg="green", fg="white", bd=3, width=15, activebackground="darkgreen",  # Fondo al presionar
                                        activeforeground="white",  font=("Arial", 10, "bold"), command=self.guardar_producto)
        self.guardar_button.grid(row=0, column=0, columnspan=2, padx=80, pady=10)

        self.compatibilidad_frame = Frame(self.tab_registro, bg="beige")
        self.compatibilidad_frame.pack(fill="x", padx=10)

    def cargar_marca_compatibilicad_combobox(self):
        # Obtener marcas desde la base de datos
        modelos = self.controlador.obtener_marcas()  # Este método debe devolver una lista de tuplas (id_marca, nombre)
        if modelos:
            self.marcas_diccionario = {nombre_marca: id_marca for id_marca, nombre_marca in modelos}
            self.compatibilidad_marcas_combobox["values"] = list(self.marcas_diccionario.keys())
        else:
            self.compatibilidad_marcas_combobox["values"] = []


    def actualizar_modelos_compatibilidad(self, event=None):
        """Actualiza los modelos según la marca seleccionada para compatibilidad."""
        marca_seleccionada = self.compatibilidad_marcas_combobox.get()
        if not marca_seleccionada:
            return
        id_marca = self.marcas_diccionario.get(marca_seleccionada)
        if id_marca is None:
            messagebox.showerror("Error", "La marca seleccionada no es válida.")
            return
        modelos = self.controlador.obtener_modelos(id_marca)
        if modelos:
            self.modelos_diccionario = {"-- Ninguno --": None}  # Agregar opción "Ninguno" con ID None
            self.modelos_diccionario.update({nombre_marca: id_marca for id_marca, nombre_marca in modelos})
            # Configurar los valores del combobox con solo los nombres
            self.compatibilidad_modelo_combobox["values"] = list(self.modelos_diccionario.keys())
            self.compatibilidad_modelo_combobox.state(["!disabled"])
        else:
            self.compatibilidad_modelo_combobox["values"] = []
            self.compatibilidad_modelo_combobox.state(["disabled"])


        self.compatibilidad_modelo_combobox.set("")

    def agregar_compatibilidad(self):
        """Agregar una compatibilidad a la tabla correspondiente."""
        try:
            marca_seleccionada = self.compatibilidad_marcas_combobox.get()
            modelo_seleccionado = self.compatibilidad_modelo_combobox.get()
            if not marca_seleccionada:
                return messagebox.showwarning("Advertencia", "Seleccione marca.")
            else:
                id_marca = self.marcas_diccionario.get(marca_seleccionada)
            if modelo_seleccionado:
                id_modelo = self.modelos_diccionario.get(modelo_seleccionado)
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
            elif int(año1) > int(año2):
                return messagebox.showwarning("Advertencia", "El año 1 debe ser menor al año 2.")
            else:
                año1 = int(año1)
                año2 = int(año2)

            producto_id = self.id[0]  # Variable almacenada del producto recién creado
            boolean = self.controlador.agregar_compatibilidad_producto(producto_id, año1, año2, id_marca, id_modelo, cilindrada)
            if boolean:
                messagebox.showinfo("Éxito", "Compatibilidad agregada correctamente.")

                self.compatibilidad_año1_entry.delete(0, END)
                self.compatibilidad_año2_entry.delete(0, END)
                self.compatibilidad_cilindrada_entry.delete(0, END)
                self.compatibilidad_modelo_combobox.set("")
                self.compatibilidad_marcas_combobox.set("")
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
        
        id, boolean = self.controlador.guardar_producto(datos)
        if boolean:
            self.id.append(id)

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

            self.agregar_compatibilidad_button = tk.Button(self.compatibilidad_frame, text="Agregar Compatibilidad",
                                                            bg="green", fg="white", bd=3, activebackground="darkgreen",  # Fondo al presionar
                                                            activeforeground="white",  font=("Arial", 10, "bold"),
                                                            command=self.agregar_compatibilidad
                                                            )
            self.agregar_compatibilidad_button.grid(row=14, column=0, columnspan=4, pady=10, sticky="w")



            self.nombre_entry.delete(0, END)
            self.codigo_entry.delete(0, END)
            self.descripcion_entry.delete(0, END)
            self.altura_entry.delete(0, END)
            self.ancho_entry.delete(0, END)
            self.largo_entry.delete(0, END)
            self.precio_entry.delete(0, END)
            self.costo_entry.delete(0, END)
            self.imagenes_list = []
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

        self.buscar_button = tk.Button(self.tab_ubicacion, text="Buscar", bg="green", fg="white", bd=3, activebackground="darkgreen",  # Fondo al presionar
                                        activeforeground="white",  font=("Arial", 10, "bold"), command=self.buscar_product, width=15)
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
        
        ubicacion_window = Toplevel(self.root, bg="beige")
        ubicacion_window.title(f"Asignar Ubicación - {producto[3]}")
        ubicacion_window.geometry("400x300")

        ubicacion_window.resizable(False, False)
        ubicacion_window.attributes("-fullscreen", False)

        ubi_frame = Frame(ubicacion_window, bg="beige")
        ubi_frame.pack(side="top")

        # Campos para asignar ubicación
        ttk.Label(ubi_frame, text="Pasillo:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        pasillo_entry = ttk.Entry(ubi_frame)
        pasillo_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(ubi_frame, text="Sección:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        seccion_entry = ttk.Entry(ubi_frame)
        seccion_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(ubi_frame, text="Piso:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        piso_entry = ttk.Entry(ubi_frame)
        piso_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(ubi_frame, text="Cantidad:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        cantidad_entry = ttk.Entry(ubi_frame)
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

            editar_window = Toplevel(self.root, bg="beige")
            editar_window.title(f"Editar Producto - {producto[3]}")
            editar_window.geometry("800x600")
            editar_window.resizable(False, False)
            editar_window.attributes("-fullscreen", False)

            editar_window.resizable(False, False)
            editar_window.attributes("-fullscreen", False)

            # Canvas para scroll
            canvas = Canvas(editar_window, bg="beige")
            canvas.pack(side="left", fill="both", expand=True)

            # Scrollbar
            scrollbar = Scrollbar(editar_window, orient="vertical", command=canvas.yview, bg="white")
            scrollbar.pack(side="right", fill="y")
            canvas.configure(yscrollcommand=scrollbar.set)

            # Frame interno para contenido
            contenidoa_frame = Frame(canvas, bg="beige")

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

            producto_frame = Frame(contenidoa_frame, bg="beige")
            producto_frame.pack(fill="x", padx=10, pady=10)

            ttk.Label(producto_frame, text="Producto:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
            producto1_entry = ttk.Entry(producto_frame, width=75)
            producto1_entry.insert(0, producto[3])
            producto1_entry.grid(row=0, column=1, padx=5, pady=5)

            ttk.Label(producto_frame, text="Descripción:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="w")
            descripcion1_entry = ttk.Entry(producto_frame, width=75)
            descripcion1_entry.insert(0, producto[4])
            descripcion1_entry.grid(row=1, column=1, padx=5, pady=5)

            ttk.Label(producto_frame, text="Código Producto:", font=("Arial", 10, "bold")).grid(row=2, column=0, padx=5, pady=5, sticky="w")
            codigo1_entry = ttk.Entry(producto_frame, width=75)
            codigo1_entry.insert(0, producto[0])
            codigo1_entry.grid(row=2, column=1, padx=5, pady=5)

            precios_frame = Frame(contenidoa_frame, bg="beige")
            precios_frame.pack(fill="x", padx=10, pady=10)

            ttk.Label(precios_frame, text="Precio Cliente:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
            precio1_entry = ttk.Entry(precios_frame)
            precio1_entry.insert(0, producto[10])
            precio1_entry.grid(row=0, column=1, padx=5, pady=5)

            ttk.Label(precios_frame, text="Costo Empresa:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="w")
            costo1_entry = ttk.Entry(precios_frame)
            costo1_entry.insert(0, producto[11])
            costo1_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

            dimensiones_frame = Frame(contenidoa_frame, bg="beige")
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

                marcas_frame = Frame(contenidoa_frame, bg="beige")
                marcas_frame.pack(fill="x", padx=10, pady=10)
                Label(marcas_frame, text="Compatible con:", font=("Arial", 10, "bold"), bg="beige").grid(row=0, column=0, sticky="w")
                i = 0
                for compatible in compatibilidad:

                    compa_frame = Frame(contenidoa_frame, bg="beige")
                    compa_frame.pack(fill="x", padx=10, pady=10)

                    # Crear variables independientes para cada iteración
                    id_compatibilidad_list.append(compatible[7])
                    Label(compa_frame, text=f"{compatible[1]} - {compatible[3]}"  if compatible[3] else compatible[1], font=("Arial", 10, "bold"), bg="beige").grid(row=0, column=0, sticky="w", padx=5)
                    tk.Button(compa_frame, text="Eliminar Compatibilidad", bg="red", fg="white", bd=3, activebackground="red3",  # Fondo al presionar
                      activeforeground="white",  font=("Arial", 10, "bold"), command=lambda id=compatible[7]: eliminar_compatibilidad(id)).grid(row=0, column=1, padx=5)
                    # Campos adicionales
                    tk.Label(compa_frame, text="Cilindrada:", font=("Arial", 10, "bold"), bg="beige").grid(row=1, column=0, pady=5, sticky="w")
                    cilindrada1_entry = ttk.Entry(compa_frame)
                    cilindrada1_entry.insert(0, compatible[4] if compatible[4] is not None else "")
                    cilindrada1_entry.grid(row=1, column=1, pady=5)
                    cilindrada_entry_list.append(cilindrada1_entry)

                    tk.Label(compa_frame, text="Año 1:", font=("Arial", 10, "bold"), bg="beige").grid(row=1, column=2, padx=5, pady=5, sticky="w")
                    año11_entry = ttk.Entry(compa_frame)
                    año11_entry.insert(0, compatible[5] if compatible[5] is not None else "")
                    año11_entry.grid(row=1, column=3, padx=5, pady=5)
                    año_1_entry_list.append(año11_entry)

                    tk.Label(compa_frame, text="Año 2:", font=("Arial", 10, "bold"), bg="beige").grid(row=1, column=4, padx=5, pady=5, sticky="w")
                    año21_entry = ttk.Entry(compa_frame)
                    año21_entry.insert(0, compatible[6] if compatible[6] is not None else "")
                    año21_entry.grid(row=1, column=5, padx=5, pady=5)
                    año_2_entry_list.append(año21_entry)
                    
                    i += 1

            def ver_imagenes_vista():
                add_Imagenes = Toplevel(self.root, bg="beige")
                add_Imagenes.title(f"Imagenes - {producto1_entry.get()}")
                add_Imagenes.geometry("520x520")

                add_Imagenes.resizable(False, False)
                add_Imagenes.attributes("-fullscreen", False)

                add_Imagenes_frame = Frame(add_Imagenes, bg="beige")
                add_Imagenes_frame.pack(fill="x", padx=10, pady=10)

                ttk.Label(add_Imagenes_frame, text=f"Imagenes del Producto: {producto1_entry.get()} - {codigo1_entry.get()}").pack(side="top")
                Imagenes_frame = Frame(add_Imagenes, bg="beige")
                Imagenes_frame.pack(fill="x", padx=10, pady=10)
                self.modelo = ProductoModelo()
                
                imagenes = self.modelo.buscar_imagenes_producto_id(id_producto)  # Obtener las imágenes desde la base de datos
                imagen_frame = Frame(Imagenes_frame, bg="beige")
                imagen_frame.pack(fill="x", padx=10, pady=10)
                if imagenes:
                    
                    

                    imagen_actual = [0]  # Usamos una lista para que sea mutable y accesible dentro de las funciones locales

                    
                    def mostrar_imagen(indice):
                        try:
                            # Convierte los datos binarios en una imagen
                            imagen_data = BytesIO(imagenes[indice][0])
                            imagen = Image.open(imagen_data)
                            imagen = imagen.resize((300, 300), Image.LANCZOS)
                            imagen_tk = ImageTk.PhotoImage(imagen)

                            # Actualiza la etiqueta de la imagen
                            imagen_label.config(image=imagen_tk)
                            imagen_label.image = imagen_tk  # Mantén la referencia para evitar que se elimine
                            imagen_label.pack()

                            # Actualiza la etiqueta del contador
                            contador_label.config(text=f"Imagen {indice + 1} de {len(imagenes)}", font=("Arial", 10, "bold"))
                        except Exception as e:
                            imagen_label.config(text="Error al cargar la imagen", image="", font=("Arial", 10, "bold"))
                            contador_label.config(text=f"Imagen {indice + 1} de {len(imagenes)} (Corrupta)", font=("Arial", 10, "bold"))
                    
                    def imagen_anterior():
                        if imagen_actual[0] > 0:
                            imagen_actual[0] -= 1

                            mostrar_imagen(imagen_actual[0])

                    def imagen_siguiente():
                        if imagen_actual[0] < len(imagenes) - 1:
                            imagen_actual[0] += 1
                            mostrar_imagen(imagen_actual[0])

                    def eliminar_imagen():
                        indice = imagen_actual[0]
                        id_imagen = imagenes[indice][1]
                        if messagebox.askyesno("Confirmar eliminación", "¿Seguro que deseas eliminar esta imagen?"):
                            # Eliminar imagen de la base de datos
                            self.modelo.eliminar_imagen_producto(id_producto, id_imagen)
                            del imagenes[indice]

                            # Ajustar el índice y actualizar la vista
                            if indice >= len(imagenes):
                                imagen_actual[0] = len(imagenes) - 1
                            if len(imagenes) > 0:
                                mostrar_imagen(imagen_actual[0])
                            else:
                                imagen_label.config(image="", text="No hay imágenes disponibles", font=("Arial", 10, "bold"))
                                contador_label.config(text="")
                            add_Imagenes.destroy()
                            ver_imagenes_vista()

                    # Botones para navegar entre imágenes
                    boton_anterior = Button(imagen_frame, text="Anterior", command=imagen_anterior, bg="salmon4", fg="beige", bd=3, activebackground="coral4",  # Fondo al presionar
                                                    activeforeground="beige", font=("Arial", 10, "bold"))
                    boton_anterior.pack(side="left", padx=5)

                    boton_siguiente = Button(imagen_frame, text="Siguiente", command=imagen_siguiente, bg="salmon4", fg="beige", bd=3, activebackground="coral4",  # Fondo al presionar
                                                    activeforeground="beige", font=("Arial", 10, "bold"))
                    boton_siguiente.pack(side="right", padx=5)

                    boton_eliminar = Button(imagen_frame, text="Eliminar Imagen", command=eliminar_imagen, bg="red", fg="white", bd=3, activebackground="red3",
                                activeforeground="white", font=("Arial", 10, "bold"))
                    boton_eliminar.pack(side="bottom", pady=5)
                    
                    

                    # Etiqueta para mostrar imágenes
                    imagen_label = Label(imagen_frame, bg="beige")
                    imagen_label.pack()

                    # Etiqueta para el contador
                    contador_label = Label(imagen_frame, text="", bg="beige")
                    contador_label.pack()

                    # Muestra la primera imagen
                    mostrar_imagen(imagen_actual[0])
                else:
                    ttk.Label(imagen_frame, text=f"No hay imagenes disponibles").pack(side="top")

                def cargar_imagenes():
                        imagen_list = []
                        files = filedialog.askopenfilenames(filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")])
                        if files:
                            imagen_list = files
                            self.modelo.cargar_imagenes_new(imagen_list, id_producto)
                            messagebox.showinfo("Imágenes cargadas", f"Se cargaron {len(files)} imágenes.")
                            add_Imagenes.destroy()
                            print("aaa")
                            ver_imagenes_vista()
                        else:
                            messagebox.showwarning("Advertencia", "No se seleccionaron imágenes.")

                imagenes_button = tk.Button(imagen_frame, text="Cargar Imágenes", bg="green", fg="white", bd=3, activebackground="darkgreen",  # Fondo al presionar
                                            activeforeground="white", font=("Arial", 10, "bold"), command=cargar_imagenes)
                imagenes_button.pack(side="bottom", pady=5)
            def agregar_compatibilidad_vista():

                def cargar_marca_add_compatibilicad_combobox():
                    # Obtener marcas desde la base de datos
                    modelos = self.controlador.obtener_marcas()  # Este método debe devolver una lista de tuplas (id_marca, nombre)
                    if modelos:
                        # Agregar opción "Ninguno" con ID None
                        self.marcas_diccionario={nombre_marca: id_marca for id_marca, nombre_marca in modelos}
                        compatibilidad_add_marcas_combobox["values"] = list(self.marcas_diccionario.keys())
                    else:
                        compatibilidad_add_marcas_combobox["values"] = []


                def actualizar_modelos_add_compatibilidad(event=None):
                    """Actualiza los modelos según la marca seleccionada para compatibilidad."""
                    marca_seleccionada = compatibilidad_add_marcas_combobox.get()
                    if not marca_seleccionada:
                        return
                    id_marca = self.marcas_diccionario.get(marca_seleccionada)
                    modelos = self.controlador.obtener_modelos(id_marca)
                    if modelos:
                        self.modelos_diccionario = {"-- Ninguno --": None}  # Agregar opción "Ninguno" con ID None
                        self.modelos_diccionario.update({nombre_marca: id_marca for id_marca, nombre_marca in modelos})
                        compatibilidad_add_modelo_combobox["values"] = list(self.modelos_diccionario.keys())
                        compatibilidad_add_modelo_combobox.state(["!disabled"])

                    else:
                        compatibilidad_add_modelo_combobox["values"] = []
                        compatibilidad_add_modelo_combobox.state(["disabled"])

                    compatibilidad_add_modelo_combobox.set("")

                def agregar_compatibilidad_funcion():
                
                    marca_seleccionada = compatibilidad_add_marcas_combobox.get()
                    modelo_seleccionado = compatibilidad_add_modelo_combobox.get()
                    if not marca_seleccionada:
                        return messagebox.showwarning("Advertencia", "Seleccione marca.")
                    else:
                        id_marca = self.marcas_diccionario.get(marca_seleccionada)
                    if modelo_seleccionado:
                        id_modelo = self.modelos_diccionario.get(modelo_seleccionado)
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
            
                
                add_compatibilidad = Toplevel(self.root, bg="beige")
                add_compatibilidad.title(f"Agregar Compatibilidad - {producto1_entry.get()}")
                add_compatibilidad.geometry("520x230")

                add_compatibilidad.resizable(False, False)
                add_compatibilidad.attributes("-fullscreen", False)

                add_title_compatibilidad_frame = Frame(add_compatibilidad, bg="beige")
                add_title_compatibilidad_frame.pack(fill="x", padx=10, pady=10)

                ttk.Label(add_title_compatibilidad_frame, text=f"Agregar Compatibilidad al Producto: {producto1_entry.get()} - {codigo1_entry.get()}").grid(row=0, column=0, columnspan=4, pady=10)
                
                add_compatibilidad_frame = Frame(add_compatibilidad, bg="beige")
                add_compatibilidad_frame.pack(fill="x", padx=10, pady=10)

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

                agregar_compatibilidad_add_button = tk.Button(
                    add_compatibilidad_frame, 
                    text="Agregar Compatibilidad", 
                    bg="green", fg="white", bd=3, activebackground="darkgreen",  # Fondo al presionar
                    activeforeground="white",  font=("Arial", 10, "bold"), 
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
            
            boton_frame = Frame(contenidoa_frame, bg="beige")
            boton_frame.pack(fill="x", padx=3, pady=10)
            tk.Button(boton_frame, text="Editar Producto", bg="green", fg="white", bd=3, activebackground="darkgreen",  # Fondo al presionar
                                                        activeforeground="white",  font=("Arial", 10, "bold"), 
                                                        command=actualizar_producto_en_base).grid(row=0, column=0, padx=5)
            tk.Button(boton_frame, text="Agregar Compatibilidad", bg="salmon4", fg="beige", bd=3, activebackground="coral4",  # Fondo al presionar
                                        activeforeground="beige", font=("Arial", 10, "bold"), 
                                        command=agregar_compatibilidad_vista).grid(row=0, column=1, padx=5)
            tk.Button(boton_frame, text="Ver Imagenes", bg="Blue", fg="beige", bd=3, activebackground="darkblue",  # Fondo al presionar
                                        activeforeground="beige", font=("Arial", 10, "bold"), command=ver_imagenes_vista).grid(row=0, column=2, padx=5)
            

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


            eliminar_window = Toplevel(self.root, bg="beige")
            eliminar_window.title(f"Eliminar producto - {producto[3]}")
            eliminar_window.geometry("640x90")  # Ajustar tamaño de la ventana
            eliminar_window.resizable(False, False)
            eliminar_window.attributes("-fullscreen", False)
            eliminar_frame = Frame(eliminar_window, bg="beige")
            eliminar_frame.pack(fill="both", padx=4, pady=4)

            ttk.Label(eliminar_frame, text="¿Estás seguro? Esto borrará toda la información del producto, incluyendo dónde está guardado.", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=10)

            button_frame = Frame(eliminar_frame, bg="beige")
            button_frame.grid(row=1, column=0, pady=10, padx=10)

            tk.Button(button_frame, text="Eliminar", 
                      bg="red", fg="white", bd=3, activebackground="red3",  # Fondo al presionar
                      activeforeground="white",  font=("Arial", 10, "bold"),
                      command=eliminar_producto_en_base, width=15).grid(row=0, column=0, padx=10)
            tk.Button(button_frame, text="Cancelar", 
                      bg="green", fg="white", bd=3, activebackground="darkgreen",  # Fondo al presionar
                      activeforeground="white",  font=("Arial", 10, "bold"),
                      command=cancelar_producto_en_base, width=15).grid(row=0, column=1, padx=10)
            
            button_frame.columnconfigure(0, weight=1)
            button_frame.columnconfigure(1, weight=1)

        ubi_button_frame = Frame(ubicacion_window, bg="beige")
        ubi_button_frame.pack(side="bottom")

        tk.Button(ubi_button_frame, text="Guardar Ubicación", bg="green", fg="white", bd=3, activebackground="darkgreen",  # Fondo al presionar
                  activeforeground="white",  font=("Arial", 10, "bold"), 
                  command=guardar_ubicacion, width=20).grid(row=4, column=0, columnspan=2, pady=10)
        tk.Button(ubi_button_frame, text="Editar Producto", bg="salmon4", fg="beige", bd=3, activebackground="coral4",  # Fondo al presionar
                  activeforeground="beige", font=("Arial", 10, "bold"), 
                  command=actualizar_producto, width=20).grid(row=5, column=0, columnspan=2, pady=10)
        tk.Button(ubi_button_frame, text="Eliminar Producto", command=eliminar_producto, bg="red", 
                  fg="white", bd=3, width=20, activebackground="red3",  # Fondo al presionar
                  activeforeground="white",  font=("Arial", 10, "bold")).grid(row=6, column=0, columnspan=2, pady=10)
        
    def crear_pestaña_busqueda(self):
        tree_frame_busca_titulo = tk.Frame(self.tab_busqueda, bg="beige")
        tree_frame_busca_titulo.pack(fill="x", padx=5, pady=5)
        ttk.Label(tree_frame_busca_titulo, text="Buscar Producto:", font=("Arial", 10, "bold")).pack(padx=5, pady=5)

        tree_frame_buscar = tk.Frame(self.tab_busqueda, bg="beige")
        tree_frame_buscar.pack(fill="x", padx=5, pady=5)

        self.busqueda_entry = ttk.Entry(tree_frame_buscar, width=65)
        self.busqueda_entry.pack(padx=5, pady=5)

        self.buscar_button = tk.Button(tree_frame_buscar, text="Buscar", command=self.buscar_producto, bg="green", fg="white", bd=3, width=15, 
                                        activebackground="darkgreen", activeforeground="white", font=("Arial", 10, "bold"))
        self.buscar_button.pack(padx=5, pady=5)

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

        # Configurar encabezados
        encabezados = [
            "Código Producto", "Marca", "Modelo", "Nombre", "Descripción",
            "Cilindrada", "Año 1", "Año 2", "Cantidad Total", "Precio", "Costo"
        ]
        for col, texto in zip(self.resultados_tree["columns"], encabezados):
            self.resultados_tree.heading(col, text=texto)
            self.resultados_tree.column(col, minwidth=100, width=120, stretch=True)

        self.resultados_tree.pack(fill="both", expand=True)

        # Configurar scrollbars
        x_scroll.config(command=self.resultados_tree.xview)
        y_scroll.config(command=self.resultados_tree.yview)

        # Doble clic en un producto para ver detalles
        self.resultados_tree.bind("<Double-1>", self.ver_detalles_producto)


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
        self.tree_frame_busca_titulo = tk.Frame(self.tab_busqueda_marca, bg="beige")
        self.tree_frame_busca_titulo.grid(row=0, column=0, columnspan=2)
        ttk.Label(self.tree_frame_busca_titulo, text="Buscar Producto:").grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        tree_frame_buscar = tk.Frame(self.tab_busqueda_marca, bg="beige")
        tree_frame_buscar.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        # Combobox de marcas
        ttk.Label(tree_frame_buscar, text="Marca:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.marcas2_combobox = ttk.Combobox(tree_frame_buscar, state="readonly")
        self.marcas2_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.cargar_marca_combobox2()

        # Combobox de modelos
        ttk.Label(tree_frame_buscar, text="Modelo:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.modelo2_combobox = ttk.Combobox(tree_frame_buscar, state="readonly")
        self.modelo2_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.modelo2_combobox.state(["disabled"])
        self.marcas2_combobox.bind("<<ComboboxSelected>>", self.actualizar_modelos2)

        # Campo de entrada para año
        ttk.Label(tree_frame_buscar, text="Año:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.año_marca_entry = ttk.Entry(tree_frame_buscar)
        self.año_marca_entry.grid(row=3, column=1, padx=5, pady=5)

        # Campo de entrada para cilindrada
        ttk.Label(tree_frame_buscar, text="Cilindrada:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.cilindrada_marca_entry = ttk.Entry(tree_frame_buscar)
        self.cilindrada_marca_entry.grid(row=4, column=1, padx=5, pady=5)

        tree_frame_busca_bot = tk.Frame(self.tab_busqueda_marca, bg="beige")
        tree_frame_busca_bot.grid(row=2, column=0, columnspan=2)

        # Botón de búsqueda
        self.buscar_marca_button = tk.Button(tree_frame_busca_bot, text="Buscar", command=self.buscar_producto_marca, bg="green", fg="white", bd=3, width=15, activebackground="darkgreen",  # Fondo al presionar
                                        activeforeground="white",  font=("Arial", 10, "bold"))
        self.buscar_marca_button.grid(row=0, column=0, padx=5, pady=10)

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
        id_marca = self.marcas_diccionario.get(marca_seleccionada)
        try:
            id_modelo = self.modelos_diccionario.get(modelo_seleccionado)
        except Exception:
            id_modelo=None
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

            self.marcas_diccionario = {nombre_marca: id_marca for id_marca, nombre_marca in modelos}
            self.marcas2_combobox["values"] = list(self.marcas_diccionario.keys())
        else:
            self.marcas2_combobox["values"] = []

    def actualizar_modelos2(self, event=None):
        """Actualiza el combobox de modelos basado en la marca seleccionada y limpia la selección del modelo."""
        
        marca_seleccionada = self.marcas2_combobox.get()
        if not marca_seleccionada:
            return
        
        # Obtener el ID de la marca seleccionada
        id_marca = self.marcas_diccionario.get(marca_seleccionada)
        """self.modelo = ProductoModelo()
        logo = self.modelo.buscar_logo_marca(id_marca)
        if logo[0]:
            try:
                # Convertir los datos binarios en una imagen
                logo_data = BytesIO(logo[0])
                logo_img = Image.open(logo_data)
                logo_img = logo_img.resize((100, 75), Image.LANCZOS)
                logo_tk = ImageTk.PhotoImage(logo_img)
                
                # Crear etiqueta para el logo y agregarla al `marca_frame`
                logo_label = Label(self.tree_frame_busca_titulo, image=logo_tk, bg="beige")
                logo_label.image = logo_tk  # Mantener referencia
                logo_label.grid(row=0, column=2, padx=10, sticky="w")
            except Exception as e:
                if hasattr(self, "logo_label") and self.logo_label:
                    self.logo_label.destroy()
                    self.logo_label = None
        else:
            if hasattr(self, "logo_label") and self.logo_label:
                self.logo_label.destroy()
                self.logo_label = None"""

        # Obtener los modelos asociados a la marca
        modelos = self.controlador.obtener_modelos(id_marca)  # Devuelve lista de tuplas (id_modelo, nombre)
        if modelos:
            self.modelos_diccionario = {"-- Ninguno --": None}  # Agregar opción "Ninguno" con ID None
            self.modelos_diccionario.update({nombre_marca: id_marca for id_marca, nombre_marca in modelos})
            self.modelo2_combobox["values"] = list(self.modelos_diccionario.keys())
            self.modelo2_combobox.state(["!disabled"])
        else:
            self.modelo2_combobox["values"] = []
            self.modelo2_combobox.state(["disabled"])

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

        detalles_window.resizable(False, False)
        detalles_window.attributes("-fullscreen", False)

        # Canvas para scroll
        canvas = Canvas(detalles_window, bg="beige")
        canvas.pack(side="left", fill="both", expand=True)

        # Scrollbar
        scrollbar = Scrollbar(detalles_window, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Frame interno para contenido
        contenedor = Frame(canvas, bg="beige")

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
        marca_frame = Frame(contenedor, bg="beige")
        marca_frame.pack(fill="x", padx=10, pady=10)
        Label(marca_frame, text="Marca:", font=("Arial", 10, "bold"), bg="beige").grid(row=0, column=0, sticky="w")
        Label(marca_frame, text=detalles[0][12] if detalles[0][12] else "No agregado", font=("Arial", 10), bg="beige").grid(row=0, column=1, sticky="w")

        Label(marca_frame, text="Modelo:", font=("Arial", 10, "bold"), bg="beige").grid(row=1, column=0, sticky="w")
        Label(marca_frame, text=detalles[0][13] if detalles[0][13] else "No agregado", font=("Arial", 10), bg="beige").grid(row=1, column=1, sticky="w")

        Label(marca_frame, text="Cilindrada:", font=("Arial", 10, "bold"), bg="beige").grid(row=2, column=0, sticky="w")
        Label(marca_frame, text=detalles[0][14] if detalles[0][14] else "No agregado", font=("Arial", 10), bg="beige").grid(row=2, column=1, sticky="w")

        Label(marca_frame, text="Año:", font=("Arial", 10, "bold"), bg="beige").grid(row=3, column=0, sticky="w")
        Label(marca_frame, text=f"{detalles[0][15]} - {detalles[0][16]}" if detalles[0][15] else "No agregado", font=("Arial", 10), bg="beige").grid(row=3, column=1, sticky="w")
        
        info_frame = Frame(contenedor, bg="beige")
        info_frame.pack(fill="x", padx=10, pady=10)

        Label(info_frame, text="Nombre:", font=("Arial", 10, "bold"), bg="beige").grid(row=1, column=0, sticky="w")
        Label(info_frame, text=detalles[0][0], font=("Arial", 10), bg="beige").grid(row=1, column=1, sticky="w")

        Label(info_frame, text="Descripción:", font=("Arial", 10, "bold"), bg="beige").grid(row=2, column=0, sticky="w")
        descripcion_texto = Text(info_frame, wrap="word", height=3, width=50, font=("Arial", 10))
        descripcion_texto.grid(row=2, column=1, sticky="w")
        scroll = Scrollbar(info_frame, command=descripcion_texto.yview)
        scroll.grid(row=2, column=2, sticky="ns")
        descripcion_texto.config(yscrollcommand=scroll.set)
        descripcion_texto.insert(END, detalles[0][1] if detalles[0][1] else "No disponible")
        descripcion_texto.config(state="disabled")

        Label(info_frame, text="Código:", font=("Arial", 10, "bold"), bg="beige").grid(row=0, column=0, sticky="w")
        Label(info_frame, text=detalles[0][2], font=("Arial", 10), bg="beige").grid(row=0, column=1, sticky="w")

        # Precios
        precios_frame = Frame(contenedor, bg="beige")
        precios_frame.pack(fill="x", padx=10, pady=10)
        Label(precios_frame, text="Precio Cliente:", font=("Arial", 10, "bold"), bg="beige").grid(row=0, column=0, sticky="w")
        Label(precios_frame, text=f"${detalles[0][7]:.2f}", font=("Arial", 10), bg="beige").grid(row=0, column=1, sticky="w")

        Label(precios_frame, text="Costo Empresa:", font=("Arial", 10, "bold"), bg="beige").grid(row=1, column=0, sticky="w")
        Label(precios_frame, text=f"${detalles[0][8]:.2f}", font=("Arial", 10), bg="beige").grid(row=1, column=1, sticky="w")

        # Dimensiones
        
        dimensiones_frame = Frame(contenedor, bg="beige")
        dimensiones_frame.pack(fill="x", padx=10, pady=10)
        if detalles[0][9] != None:
            if detalles[0][10] and detalles[0][11]:
                dimension=f"{detalles[0][9]} cm x {detalles[0][10]} cm x {detalles[0][11]} cm (Largo x Ancho x Altura)"
            elif detalles[0][10]:
                dimension=f"{detalles[0][9]} cm x {detalles[0][10]} cm (Largo x Ancho)"
            elif detalles[0][11]:
                dimension=f"{detalles[0][9]} cm x {detalles[0][11]} cm (Largo x Altura)"
            else:
                dimension=f"{detalles[0][9]} cm (Largo)"
        elif detalles[0][9] == None:

            if detalles[0][10] and detalles[0][11]:
                dimension=f"{detalles[0][10]} cm x {detalles[0][11]} cm (Ancho x Altura)"
            elif detalles[0][10]:
                dimension=f"{detalles[0][10]} cm (Ancho)"
            elif detalles[0][11]:
                dimension=f"{detalles[0][11]} cm (Altura)"
        try:
            Label(dimensiones_frame, text="Dimensiones:", font=("Arial", 10, "bold"), bg="beige").grid(row=0, column=0, sticky="w")
            Label(dimensiones_frame, text=dimension, font=("Arial", 10), bg="beige").grid(row=0, column=1, sticky="w")
        except Exception:
            Label(dimensiones_frame, text="No agregado", font=("Arial", 10), bg="beige").grid(row=0, column=1, sticky="w")
        if compatibilidad:
            compatible_frame = Frame(contenedor, bg="beige")
            compatible_frame.pack(fill="x", padx=10, pady=10)
            Label(compatible_frame, text=f"Compatible con:", font=("Arial", 10, "bold"), bg="beige").grid(row=0, column=0, sticky="w")
            i=1
            for compatible in compatibilidad:
                if compatible[1]:
                    if compatible[2] and compatible[3]:
                        texto = f"- {compatible[0]} {compatible[1]}, Cilindrada: {compatible[2]}, Año: {compatible[3]} - {compatible[4]}"
                    elif compatible[3]:
                        texto = f"- {compatible[0]} {compatible[1]}, Año: {compatible[3]} - {compatible[4]}"
                    elif compatible[2]:
                        texto = f"- {compatible[0]} {compatible[1]}, Cilindrada: {compatible[2]}"
                    else:
                        texto = f"- {compatible[0]} {compatible[1]}"
                else:
                    if compatible[2] and compatible[3]:
                        texto = f"- {compatible[0]}, Cilindrada: {compatible[2]}, Año: {compatible[3]} - {compatible[4]}"
                    elif compatible[3]:
                        texto = f"- {compatible[0]}, Año: {compatible[3]} - {compatible[4]}"
                    elif compatible[2]:
                        texto = f"- {compatible[0]}, Cilindrada: {compatible[2]}"
                    else:
                        texto = f"- {compatible[0]}"
                Label(compatible_frame, text=texto, font=("Arial", 10, "bold"), bg="beige").grid(row=i, column=0, sticky="w")
                i += 1

        i = 1
        lista = []
        cantidades = []
        id_ubicaciones = []
        ubicacion = []
        for detalle in detalles:
            # Ubicación y cantidad
            ubicacion_frame = Frame(contenedor, bg="beige")
            ubicacion_frame.pack(fill="x", padx=10, pady=10)

            Label(ubicacion_frame, text=f"Ubicación {i}:", font=("Arial", 10, "bold"), bg="beige").grid(row=0, column=0, sticky="w")
            Label(ubicacion_frame, text=f"Pasillo {detalle[3]}, Sección {detalle[4]}, Piso {detalle[5]}", font=("Arial", 10), bg="beige").grid(row=0, column=1, sticky="w")

            Label(ubicacion_frame, text="Cantidad:", font=("Arial", 10, "bold"), bg="beige").grid(row=1, column=0, sticky="w")
            Label(ubicacion_frame, text=detalle[6], font=("Arial", 10), bg="beige").grid(row=1, column=1, sticky="w")
            lista.append(f"Ubicación {i}")
            ubicacion.append({"pasillo":detalle[3], "seccion":detalle[4], "piso":detalle[5]})
            cantidades.append(detalle[6])
            id_ubicaciones.append(detalle[17])
            i += 1

        ttk.Label(marca_frame, text="").grid(row=0, column=2, padx=40)  
        
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
        
        ttk.Label(marca_frame, text="").grid(row=1, column=2, padx=40)  
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
            
                
           
        ttk.Label(marca_frame, text="").grid(row=2, column=2, padx=40)
        tk.Button(marca_frame, text="Agregar al carrito", command=agregar_al_carrito, bg="green", fg="white", bd=3, width=15, activebackground="darkgreen",  # Fondo al presionar
                                        activeforeground="white",  font=("Arial", 10, "bold")).grid(row=2, column=3, columnspan=2)

        # Imagen del producto
        self.modelo = ProductoModelo()
        
        imagenes = self.modelo.buscar_imagenes_producto(id_producto)  # Obtener las imágenes desde la base de datos
        if imagenes:
            imagen_frame = Frame(contenedor, bg="beige")
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
                    contador_label.config(text=f"Imagen {indice + 1} de {len(imagenes)}", font=("Arial", 10, "bold"))
                except Exception as e:
                    imagen_label.config(text="Error al cargar la imagen", image="", font=("Arial", 10, "bold"))
                    contador_label.config(text=f"Imagen {indice + 1} de {len(imagenes)} (Corrupta)", font=("Arial", 10, "bold"))


            def imagen_anterior():
                if imagen_actual[0] > 0:
                    imagen_actual[0] -= 1
                    mostrar_imagen(imagen_actual[0])

            def imagen_siguiente():
                if imagen_actual[0] < len(imagenes) - 1:
                    imagen_actual[0] += 1
                    mostrar_imagen(imagen_actual[0])

            # Botones para navegar entre imágenes
            boton_anterior = Button(imagen_frame, text="Anterior", command=imagen_anterior, bg="salmon4", fg="beige", bd=3, activebackground="coral4",  # Fondo al presionar
                                            activeforeground="beige", font=("Arial", 10, "bold"))
            boton_anterior.pack(side="left", padx=5)

            boton_siguiente = Button(imagen_frame, text="Siguiente", command=imagen_siguiente, bg="salmon4", fg="beige", bd=3, activebackground="coral4",  # Fondo al presionar
                                            activeforeground="beige", font=("Arial", 10, "bold"))
            boton_siguiente.pack(side="right", padx=5)

            # Etiqueta para mostrar imágenes
            imagen_label = Label(imagen_frame, bg="beige")
            imagen_label.pack()

            # Etiqueta para el contador
            contador_label = Label(imagen_frame, text="", bg="beige")
            contador_label.pack()

            # Muestra la primera imagen
            mostrar_imagen(imagen_actual[0])
        
        """try:
            logo = self.modelo.buscar_logo(id_compatibilidad)
            if logo[0]:
                try:
                    # Convertir los datos binarios en una imagen
                    logo_data = BytesIO(logo[0])
                    logo_img = Image.open(logo_data)
                    logo_img = logo_img.resize((75, 50), Image.LANCZOS)
                    logo_tk = ImageTk.PhotoImage(logo_img)
                    
                    # Crear etiqueta para el logo y agregarla al `marca_frame`
                    logo_label = Label(marca_frame, image=logo_tk, bg="beige")
                    logo_label.image = logo_tk  # Mantener referencia
                    logo_label.grid(row=0, column=2, padx=10, sticky="w")
                except Exception as e:
                    Label(marca_frame, text="Logo no disponible", font=("Arial", 10, "italic", "bold"), bg="beige", fg="red").grid(row=0, column=2, padx=10, sticky="w")
        except Exception:
            None"""
        detalles_window.mainloop()

    def crear_pestaña_marca(self):
        # Campos de entrada
        ttk.Label(self.tab_marca, text="Nombre:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.nombre_marca_entry = ttk.Entry(self.tab_marca)
        self.nombre_marca_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        """ttk.Label(self.tab_marca, text="Logo:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.imagenes_marcas_Entry = []
        self.imagenes_button = tk.Button(self.tab_marca, text="Cargar Logo", command=self.cargar_imagenes_marca, bg="salmon4", fg="beige", bd=3, activebackground="coral4",  # Fondo al presionar
                                        activeforeground="beige", font=("Arial", 10, "bold"))
        self.imagenes_button.grid(row=1, column=1, padx=5, pady=5, sticky="w")"""

        # Botón para guardar
        self.guardar_button = tk.Button(self.tab_marca, text="Guardar", command=self.guardar_marcas, bg="green", fg="white", bd=3, width=15, activebackground="darkgreen",  # Fondo al presionar
                                        activeforeground="white",  font=("Arial", 10, "bold"))
        self.guardar_button.grid(row=2, column=0, columnspan=2, pady=10)


    """def cargar_imagenes_marca(self):
        files = filedialog.askopenfilenames(filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")])
        self.imagenes_marcas_Entry = files
        messagebox.showinfo("Imágenes cargadas", f"Se cargo {len(files)} imágen.")"""

   
    def guardar_marcas(self):
        datos = {"nombre" : self.nombre_marca_entry.get()}
        if not self.nombre_marca_entry.get():
            messagebox.showerror("Error", "El campo 'Nombre' es obligatorio.")
            return
        self.controlador.guardar_marcas(datos)
        self.nombre_marca_entry.delete(0, END)  # Limpia el campo de texto
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
        ttk.Label(self.tab_modelo, text="Nombre:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.nombre_modelo_entry = ttk.Entry(self.tab_modelo)
        self.nombre_modelo_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.tab_modelo, text="Marca:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.marca_combobox = ttk.Combobox(self.tab_modelo, state="readonly")
        self.marca_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.cargar_marcas_combobox()
        
        """ttk.Label(self.tab_modelo, text="Imagen:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.imagen_modelo_entry = []
        self.imagenes_button = tk.Button(self.tab_modelo, text="Cargar Imagen", command=self.cargar_imagenes_modelo, bg="salmon4", fg="beige", bd=3, activebackground="coral4",  # Fondo al presionar
                                        activeforeground="beige", font=("Arial", 10, "bold"))
        self.imagenes_button.grid(row=2, column=1, padx=5, pady=5, sticky="w")"""

        # Botón para guardar
        self.guardar_button = tk.Button(self.tab_modelo, text="Guardar", command=self.guardar_modelo, bg="green", fg="white", bd=3, width=15, activebackground="darkgreen",  # Fondo al presionar
                                        activeforeground="white",  font=("Arial", 10, "bold"))
        self.guardar_button.grid(row=3, column=0, columnspan=2, pady=10)
    
    def cargar_marcas_combobox(self):
        # Obtener marcas desde la base de datos
        marcas = self.controlador.obtener_marcas()  # Este método debe devolver una lista de tuplas (id_marca, nombre)
        if marcas:

            self.marcas_diccionario = {nombre_marca: id_marca for id_marca, nombre_marca in marcas}
            self.marca_combobox["values"] = list(self.marcas_diccionario.keys())

        else:
            self.marca_combobox["values"] = []


    """def cargar_imagenes_modelo(self):
        files = filedialog.askopenfilenames(filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")])
        self.imagen_modelo_entry = files
        messagebox.showinfo("Imágenes cargadas", f"Se cargo {len(files)} imágen.")"""

    def guardar_modelo(self):
        if not self.nombre_modelo_entry.get():
            messagebox.showerror("Error", "El campo 'Nombre' es obligatorio.")
            return
        if not self.marca_combobox.get():
            messagebox.showerror("Error", "Debe seleccionar una marca.")
            return

        # Obtener id de la marca seleccionada
        marca_seleccionada = self.marca_combobox.get()
        id_marca = self.marcas_diccionario.get(marca_seleccionada)

        datos = {
            "nombre": self.nombre_modelo_entry.get(),
            "marca": id_marca,
            #"imagenes": self.imagen_modelo_entry
        }
        self.controlador.guardar_modelo(datos)
        self.nombre_modelo_entry.delete(0, END)  # Limpia el campo de texto
        self.marca_combobox.set('')  # Restablece el combobox
        #self.imagen_modelo_entry = []
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
        self.guardar_carro_button = tk.Button(self.tab_carro, text="Guardar Carrito", command=self.guardar_carro, bg="green", fg="white", bd=3, width=15, activebackground="darkgreen",  # Fondo al presionar
                                        activeforeground="white",  font=("Arial", 10, "bold"))
        self.guardar_carro_button.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(self.tab_carro, text="Vendedor:").grid(row=2, column=0, padx=5, pady=5)
        self.vendedor_combobox = ttk.Combobox(self.tab_carro, state="readonly")
        self.vendedor_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.cargar_vendedor()

        # Nuevo botón: Eliminar producto seleccionado
        self.eliminar_producto_button = tk.Button(self.tab_carro, text="Eliminar Producto", command=self.eliminar_producto_carro, bg="red", fg="white", bd=3, width=15, activebackground="red3",  # Fondo al presionar
                                        activeforeground="white",  font=("Arial", 10, "bold"))
        self.eliminar_producto_button.grid(row=3, column=0, padx=5, pady=5)

        # Nuevo botón: Vaciar carrito completo
        self.vaciar_carro_button = tk.Button(self.tab_carro, text="Vaciar Carrito", command=self.vaciar_carro, bg="red", fg="white", bd=3, width=15, activebackground="red3",  # Fondo al presionar
                                        activeforeground="white",  font=("Arial", 10, "bold"))
        self.vaciar_carro_button.grid(row=3, column=1, padx=5, pady=5)


    def cerrar_programa(self):
        """Función que se ejecuta cuando el programa se cierra."""
        if self.carrito:
            # Preguntar al usuario si desea devolver los productos al stock
            self.vaciar_carro()  # Vaciar el carrito y devolver los productos al stock
        self.root.quit()
        self.root.destroy() 
    def cargar_medios_pago(self):
        """Carga los medios de pago desde la base de datos."""
        medios_pago = self.controlador.obtener_medios_pago()
        self.medio_pago_combobox["values"] = [f"{id} - {nombre}" for id, nombre in medios_pago]

    def cargar_vendedor(self):
        """Carga los medios de pago desde la base de datos."""
        vendedor = self.controlador.obtener_vendedor()
        self.vendedor_combobox["values"] = [f"{id} - {nombre}" for id, nombre in vendedor]    

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
        usuario = self.vendedor_combobox.get()
        if not medio_pago_seleccionado:
            return messagebox.showerror("Error", "Debe seleccionar un medio de pago.")

        if not usuario:
            return messagebox.showerror("Error", "Debe seleccionar un vendedor")

        id_medio_pago = int(medio_pago_seleccionado.split(" - ")[0])
        id_usuario = int(usuario.split(" - ")[0])

        if not self.carrito:
            return messagebox.showwarning("Advertencia", "El carrito está vacío.")

        # Guardar en la base de datos

        exito = self.controlador.guardar_carro(self.carrito, id_medio_pago, self.total_final, id_usuario)
        if exito:
            self.carrito = []
            self.total_final = 0.0
            self.actualizar_tabla_carro()
            self.cargar_ventas_diarias()

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
    
    def tab_detalle_venta(self):
        
        tree_frame_dia = tk.Frame(self.tab_detalle, bg="beige")
        tree_frame_dia.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        self.invisible = ttk.Label(tree_frame_dia, text="", font=("Arial", 12, "bold"))
        self.invisible.grid(row=0, column=0, padx=195, sticky="w")
        fecha = date.today()

        self.total_dia = ttk.Label(tree_frame_dia, text=f"Fecha: {fecha.day} - {fecha.month} - {fecha.year}", font=("Arial", 12, "bold"))
        self.total_dia.grid(row=0, column=1, sticky="w")

        tree_frame_detalle_diario = tk.Frame(self.tab_detalle, bg="beige")
        tree_frame_detalle_diario.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

         # Scrollbars
        x_scroll = ttk.Scrollbar(tree_frame_detalle_diario, orient="horizontal")
        x_scroll.grid(row=1, column=0, sticky="ew")

        y_scroll = ttk.Scrollbar(tree_frame_detalle_diario, orient="vertical")
        y_scroll.grid(row=0, column=1, sticky="ns")

        # Treeview
        self.ventas_treeview = ttk.Treeview(
            tree_frame_detalle_diario,
            columns=("vendedor", "producto", "cantidad", "total"),
            show="headings",
            xscrollcommand=x_scroll.set,
            yscrollcommand=y_scroll.set
        )
        self.ventas_treeview.grid(row=0, column=0, sticky="nsew")

        # Configurar encabezados
        encabezados = [
            "Vendedor", "Cantidad Productos", "Cantidad Ventas", "Total Ventas"
        ]
        for col, texto in zip(self.ventas_treeview["columns"], encabezados):
            self.ventas_treeview.heading(col, text=texto)
            self.ventas_treeview.column(col, minwidth=140, width=240, stretch=True)

        # Configurar scrollbars
        x_scroll.config(command=self.ventas_treeview.xview)
        y_scroll.config(command=self.ventas_treeview.yview)

        # Ajustar tamaño dinámico de columnas
        
        tree_frame_detalle_diario.grid_rowconfigure(0, weight=1)
        tree_frame_detalle_diario.grid_columnconfigure(0, weight=1)


        # Total del día
        self.total_dia_label = ttk.Label(tree_frame_detalle_diario, text="Total Día: $0.00", font=("Arial", 12, "bold"))
        self.total_dia_label.grid(row=6, column=0, padx=10, pady=10, sticky="w")

        # Detalles por medio de pago
        self.total_efectivo_label = ttk.Label(tree_frame_detalle_diario, text="Total Efectivo: $0.00", font=("Arial", 12, "bold"))
        self.total_efectivo_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.total_debito_label = ttk.Label(tree_frame_detalle_diario, text="Total Débito: $0.00", font=("Arial", 12, "bold"))
        self.total_debito_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")

        self.total_credito_label = ttk.Label(tree_frame_detalle_diario, text="Total Crédito: $0.00", font=("Arial", 12, "bold"))
        self.total_credito_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")

        self.total_transferencia_label = ttk.Label(tree_frame_detalle_diario, text="Total Tansferencia: $0.00", font=("Arial", 12, "bold"))
        self.total_transferencia_label.grid(row=5, column=0, padx=10, pady=10, sticky="w")    

        # Botón para cerrar la caja
        """self.cerrar_caja_button = tk.Button(
            tree_frame_detalle_diario, text="Cerrar Caja", command=self.cerrar_caja, bg="blue", fg="white",
            font=("Arial", 12, "bold"), width=20, activebackground="darkblue", activeforeground="white"
        )
        self.cerrar_caja_button.grid(row=7, column=0, columnspan=2, pady=20)"""

        # Cargar los datos iniciales
        self.cargar_ventas_diarias()

    def cargar_ventas_diarias(self):
        """Carga los datos de las ventas diarias y los muestra en la tabla."""
        
        ventas = self.controlador.obtener_ventas_diarias()
        # Limpiar la tabla
        for item in self.ventas_treeview.get_children():
            self.ventas_treeview.delete(item)

        # Variables para totales
        total_dia = 0
        total_efectivo = 0
        total_debito = 0
        total_credito = 0
        total_transferencia = 0
        usuario_totales = {}
        # Insertar datos en la tabla
        for venta in ventas:
            usuario = venta[0]
            productos_vendidos = venta[1] if venta[1] is not None else 0
            cantidad_ventas = venta[2] if venta[2] is not None else 0
            monto_total = venta[3] if venta[3] is not None else 0.0
            if usuario not in usuario_totales:
                usuario_totales[usuario] = {
                    'cantidad_productos': 0,
                    'cantidad_ventas': 0,
                    'total_ventas': 0.0
                }
            
            usuario_totales[usuario]['cantidad_productos'] += productos_vendidos
            usuario_totales[usuario]['cantidad_ventas'] += cantidad_ventas
            usuario_totales[usuario]['total_ventas'] += monto_total
            if usuario.startswith("Total"):
                if usuario == "Total Efectivo":
                    total_efectivo = monto_total
                elif usuario == "Total Débito":
                    total_debito = monto_total
                elif usuario == "Total Crédito":
                    total_credito = monto_total
                elif usuario == "Total Transferencia":
                    total_transferencia = monto_total
            elif usuario == "Total General":
                total_dia = monto_total
            else:
                vendedor = usuario
                self.ventas_treeview.insert(
                    "", "end", values=(vendedor, productos_vendidos, cantidad_ventas, f"${monto_total:.2f}")
                )
        
        # Si el Total General no está presente, sumar todos los totales conocidos
        if total_dia == 0:
            total_dia = total_efectivo + total_debito + total_credito + total_transferencia

        # Mostrar totales
        self.total_dia_label.config(text=f"Total Día: ${total_dia:.2f}")
        self.total_efectivo_label.config(text=f"Total Efectivo: ${total_efectivo:.2f}")
        self.total_debito_label.config(text=f"Total Débito: ${total_debito:.2f}")
        self.total_credito_label.config(text=f"Total Crédito: ${total_credito:.2f}")
        self.total_transferencia_label.config(text=f"Total Transferencia: ${total_transferencia:.2f}")
        
        self.usuario_totales = usuario_totales

    def cerrar_caja(self):
        """Cierra la caja y guarda el total del día en la base de datos."""
        total_dia = self.total_dia_label.cget("text").replace("Total Día: $", "")
        total_efectivo = self.total_efectivo_label.cget("text").replace("Total Efectivo: $", "")
        total_debito = self.total_debito_label.cget("text").replace("Total Débito: $", "")
        total_credito = self.total_credito_label.cget("text").replace("Total Crédito: $", "")
        total_transferencia = self.total_transferencia_label.cget("text").replace("Total Transferencia: $", "")
        cantidad_ventas = sum(int(self.ventas_treeview.item(item, "values")[2]) for item in self.ventas_treeview.get_children())
        cantidad_articulos = sum(int(self.ventas_treeview.item(item, "values")[1]) for item in self.ventas_treeview.get_children())

        ventas_por_usuario = []

        for usuario, datos in self.usuario_totales.items():
            cantidad_productos = datos['cantidad_productos']
            cantidad_ventas_usuario = datos['cantidad_ventas']
            total_ventas_usuario = datos['total_ventas']
            ventas_por_usuario.append({
            'usuario': usuario,
            'cantidad_productos': cantidad_productos,
            'cantidad_ventas': cantidad_ventas_usuario,
            'total_ventas': total_ventas_usuario})
        

        exito = self.controlador.guardar_cierre_caja(
            float(total_dia),
            float(total_efectivo),
            float(total_debito),
            float(total_credito),
            float(total_transferencia),
            cantidad_ventas,
            cantidad_articulos,
            ventas_por_usuario
        )

        if exito:
            messagebox.showinfo("Éxito", "Caja cerrada correctamente.")
            self.cargar_ventas_diarias()
        else:
            messagebox.showerror("Error", "No se pudo cerrar la caja.")

    def actualizar_pestaña(self, event):

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
            self.cargar_ventas_diarias()
        except Exception:
            None
        try:
            self.cargar_marca_combobox2()
            self.actualizar_modelos2()
        except Exception:
            None 
        try:
            self.cargar_marcas_combobox()
        except Exception:
            None
        try:
            self.cargar_marca_compatibilicad_combobox()
            self.actualizar_modelos_compatibilidad()
        except Exception:
            None
        try:
            self.actualizar_modelos_compatibilidad()
        except Exception:
            None
        try:
            self.cargar_marca_compatibilicad_combobox()
        except Exception:
            None


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
            return True
        except Exception as e:
            return False
            

    def guardar_producto(self, datos):
        
        try:
            id = self.modelo.agregar_producto(
                datos["nombre"], datos["descripcion"], datos["codigo"],
                datos["precio"], datos["costo"], datos["largo"],
                datos["ancho"], datos["altura"], datos["imagenes"]
            )
            messagebox.showinfo("Éxito", "Producto registrado correctamente.")
            return(id, True)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar el producto: {e}")
            return(None, False)
        
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
            self.modelo.agregar_marca(datos["nombre"])
            messagebox.showinfo("Éxito", "Marca registrada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar la marca: {e}")

    def guardar_modelo(self, datos):
        try:
            self.modelo.agregar_modelo(
                datos["nombre"], datos["marca"]
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
    
    def obtener_vendedor(self):
        query = "SELECT id_usuario, nombre FROM usuario"
        self.modelo.cursor.execute(query)
        return self.modelo.cursor.fetchall()

    def obtener_ventas_diarias(self):
        try:
            a = self.modelo.obtener_ventas_diarias()
            return a
        except Exception as e:
            return []

    def guardar_carro(self, carrito, id_medio_pago, total, id_usuario):
        
        try:
            self.modelo.guardar_carro_modelo(carrito, id_medio_pago, total, id_usuario)
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

    def guardar_cierre_caja(self, total_dia, total_efectivo, total_debito, total_credito, total_transferencia, cantidad_ventas, cantidad_articulos, ventas_por_usuario):
        try:
            
            self.modelo.guardar_cierre_caja(total_dia, total_efectivo, total_debito, total_credito, total_transferencia, cantidad_ventas, cantidad_articulos, ventas_por_usuario)
            
            return True
        except Exception as e:
            return False
    
# Inicialización
if __name__ == "__main__":
    root = Tk()
    root.title("GESTIÓN DE BODEGA - REPUESTOS RONY")
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
