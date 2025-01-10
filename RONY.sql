drop database if exists Warexpert;
CREATE DATABASE IF NOT EXISTS Warexpert;
USE Warexpert;

create table probar(
id integer
);

create table marcas
(
	id_marca integer auto_increment primary key,
    nombre varchar(50)
);

create table modelo
(
	id_modelo integer auto_increment primary key,
    nombre varchar(150),
    marca integer,
    foreign key (marca) references marcas(id_marca) ON DELETE CASCADE
);
CREATE TABLE CATEGORIA(
	id_categoria integer auto_increment primary key,
    nombre varchar(55)
);
-- Tabla para productos principales (atributos únicos de cada producto)
CREATE TABLE Productos (
    id_producto integer AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion varchar(355),
    cantidad_TOTAl integer,
    codigo_producto varchar(255) NOT NULL,
    categoria integer,
    foreign key (categoria) references CATEGORIA(id_categoria)
);

create table compatibilidad_producto(
	id_compatibilidad_producto integer auto_increment primary key,
	año0 integer,
	año1 integer,
	marca integer,
	modelo integer,
	cilindrada float,
	producto integer,
	foreign key (producto) references productos(id_producto) ON DELETE CASCADE,
	foreign key (modelo) references modelo(id_modelo) ON DELETE CASCADE,
	foreign key (marca) references marcas(id_marca) ON DELETE CASCADE
);

-- Tabla para ubicación de los productos
CREATE TABLE Ubicaciones (
    id_ubicacion integer AUTO_INCREMENT PRIMARY KEY,
    pasillo integer,
    seccion integer,
    piso integer,
    cantidad integer,
    id_producto INT NOT NULL,
    FOREIGN KEY (id_producto) REFERENCES Productos(id_producto) ON DELETE CASCADE
);

-- Tabla para precios de los productos
CREATE TABLE Precios (
    id_precio integer AUTO_INCREMENT PRIMARY KEY,
    precio_cliente float NOT NULL,
    costo_empresa float NOT NULL,
    id_producto INT NOT NULL,
    FOREIGN KEY (id_producto) REFERENCES Productos(id_producto) ON DELETE CASCADE
);

-- Tabla para dimensiones de los productos
CREATE TABLE Dimensiones (
    id_dimension INT AUTO_INCREMENT PRIMARY KEY,
    largo float,
    ancho float,
    altura float,
    id_producto INT NOT NULL,
    FOREIGN KEY (id_producto) REFERENCES Productos(id_producto) ON DELETE CASCADE
);

-- Tabla para imágenes asociadas a los productos
CREATE TABLE Imagenes (
    id_imagen INT AUTO_INCREMENT PRIMARY KEY,
    url_imagen LONGBLOB NOT NULL,
    id_producto INT NOT NULL,
    FOREIGN KEY (id_producto) REFERENCES Productos(id_producto) ON DELETE CASCADE
);

create table medio_pago(
id_medio_pago integer auto_increment primary key,
nombre varchar(60)
);

INSERT INTO medio_pago (NOMBRE) VALUES 
("Efectivo"),
("Tarjeta de Debito"),
("Tarjeta de Credito"),
("Transferencia");

create table usuario(
id_usuario integer auto_increment primary key,
nombre varchar(60),
rut varchar(30)
);

INSERT INTO usuario (Nombre) VALUES 
("Rony Castro Araya"),
("Computador 2"),
("Computador 3"),
("Computador 4");

create table carro(
id_carro integer auto_increment primary key,
fecha datetime default current_timestamp,
medio_pago integer,
monto float,
usuario integer,
foreign key(usuario) references usuario(id_usuario),
foreign key(medio_pago) references medio_pago(id_medio_pago) ON DELETE CASCADE
);

create table detalle_carro(
id_detalle_carro integer auto_increment primary key,
producto integer,
cantidad integer,
total_producto float,
carro integer,
foreign key(producto) references productos(id_producto) ON DELETE CASCADE,
foreign key(carro) references carro(id_carro) ON DELETE CASCADE
);

CREATE TABLE detalle_diario (
    id_detalle_diario INTEGER AUTO_INCREMENT PRIMARY KEY,
    fecha DATE default (current_date), -- Fecha del día
    total_dia FLOAT NOT NULL, -- Total acumulado del día
    total_efectivo float not null,
    total_tranfe float not null,
    total_credito float not null,
    total_debito float not null,
    cantidad_ventas_total INTEGER NOT NULL, -- Número total de ventas
    activa bool default true,
    cantidad_articulos_total INTEGER NOT NULL -- Número total de artículos vendidos
);

create table detalle_diario_usuario(
	id_detalle_diario_usuario integer auto_increment primary key,
    cantidad_ventas integer,
    cantidad_articulos integer,
    detalle_diario integer,
    total_usuario float,
    usuario integer,
    foreign key(detalle_diario) references detalle_diario(id_detalle_diario),
    foreign key(usuario) references usuario(id_usuario)
);

-- Índices para optimización de búsqueda
CREATE INDEX idx_nombre ON Productos(nombre);
CREATE INDEX idx_codigo_producto ON Productos(codigo_producto);