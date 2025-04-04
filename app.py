import os
from dotenv import load_dotenv
import mysql.connector
from flask import request, redirect, url_for, render_template, Flask, session
from datetime import datetime
from decimal import Decimal

dotenv_path = os.path.join(os.path.dirname(__file__), "datos.env")
load_dotenv(dotenv_path=dotenv_path)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Clave secreta para la sesión


def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            use_pure=True
        )
        print('Conexion exitosa a la base de datos')
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        c_nom = request.form['c_nom']
        c_contrasena = request.form['c_contrasena']

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Buscar el cliente en la base de datos
        cursor.execute("SELECT * FROM clientes WHERE c_nom = %s", (c_nom,))
        cliente = cursor.fetchone()

        if cliente:
            # Verificar la contraseña
            if cliente['c_contrasena'] == c_contrasena:
                # Iniciar sesión
                session['c_id_cliente'] = cliente['c_id_cliente']
                session['c_nom'] = cliente['c_nom']
                connection.close()
                return redirect(url_for('index'))
            else:
                connection.close()
                return render_template('login.html', error='Contraseña incorrecta')
        else:
            # Registrar el cliente si no existe
            sql = "INSERT INTO clientes (c_nom, c_contrasena) VALUES (%s, %s)"
            val = (c_nom, c_contrasena)
            cursor.execute(sql, val)
            connection.commit()

            # Iniciar sesión
            session['c_id_cliente'] = cursor.lastrowid
            session['c_nom'] = c_nom
            connection.close()
            return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('c_id_cliente', None)
    session.pop('c_nom', None)
    return redirect(url_for('login'))

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'c_id_cliente' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/agregar_producto', methods=['GET', 'POST'])
@login_required
def agregar_producto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        tipo = request.form['tipo']
        precio = request.form['precio']
        stock = request.form['stock']
        imagen = request.files['imagen']  # Obtener el archivo de imagen

        # Guardar la imagen en una carpeta
        if imagen:
            filename = imagen.filename
            imagen.save(os.path.join('static/imagenes', filename))  # Guardar en la carpeta 'static/imagenes'
            imagen_url = 'imagenes/' + filename  # URL para acceder a la imagen

            connection = get_db_connection()
            with connection.cursor() as cursor:
                sql = "INSERT INTO productos (p_nom, p_tipo, p_precio, p_stock, p_imagen) VALUES (%s, %s, %s, %s, %s)"
                val = (nombre, tipo, precio, stock, imagen_url)
                cursor.execute(sql, val)
                connection.commit()
            connection.close()

            return redirect(url_for('index'))
        else:
            return "Error: No se ha subido ninguna imagen."

    return render_template("agregar.html")  # Mostrar el formulario

@app.route("/actualizar/<int:producto_id>", methods=["GET", "POST"])
@login_required
def actualizar_producto(producto_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        nombre = request.form['nombre']
        tipo = request.form['tipo']
        precio = request.form['precio']
        stock = request.form['stock']
        imagen = request.files['imagen']  # Obtener el archivo de imagen

        # Guardar la imagen en una carpeta
        if imagen:
            filename = imagen.filename
            imagen.save(os.path.join('static/imagenes', filename))  # Guardar en la carpeta 'static/imagenes'
            imagen_url = 'imagenes/' + filename  # URL para acceder a la imagen

            sql = "UPDATE productos SET p_nom=%s, p_tipo=%s, p_precio=%s, p_stock=%s, p_imagen=%s WHERE p_id_producto=%s"
            val = (nombre, tipo, precio, stock, imagen_url, producto_id)
        else:
            sql = "UPDATE productos SET p_nom=%s, p_tipo=%s, p_precio=%s, p_stock=%s WHERE p_id_producto=%s"
            val = (nombre, tipo, precio, stock, producto_id)

        cursor.execute(sql, val)
        connection.commit()
        connection.close()

        return redirect(url_for('index'))
    else:
        cursor.execute("SELECT * FROM productos WHERE p_id_producto = %s", (producto_id,))
        producto = cursor.fetchone()
        connection.close()
        return render_template('actualizar.html', producto=producto, c_nom=session['c_nom'])  # Pasar el nombre del cliente

@app.route('/eliminar/<int:producto_id>', methods=['POST'])
@login_required
def eliminar_producto(producto_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    sql = "DELETE FROM productos WHERE p_id_producto = %s"
    val = (producto_id,)
    cursor.execute(sql, val)
    connection.commit()
    connection.close()
    return redirect(url_for('index'))

@app.route('/')
@login_required
def index():
    connection = get_db_connection()
    with connection.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT * FROM productos")
        productos = cursor.fetchall()
    connection.close()
    return render_template('index.html', productos=productos, c_nom=session['c_nom'])

@app.route("/ventas", methods=["GET", "POST"])
@login_required
def ventas():
    connection = get_db_connection()
    if request.method == "POST":
        # Obtener datos del formulario
        producto_id = int(request.form.get("producto_id"))
        cantidad_vendida = int(request.form.get("cantidad"))
        c_id_cliente = session['c_id_cliente']  # Obtener el ID del cliente de la sesión

        # Obtener los datos del producto seleccionado
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM productos WHERE p_id_producto = %s", (producto_id,))
            producto = cursor.fetchone()

        # Verificar si hay suficiente stock
        if producto["p_stock"] < cantidad_vendida:
            connection.close()
            return "Error: No hay suficiente stock disponible.", 400

        # Calcular el subtotal
        precio_producto = float(producto["p_precio"])
        subtotal = precio_producto * cantidad_vendida

        # Registrar la venta en la tabla 'ventas'
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO ventas (v_fecha, v_subtotal, c_id_cliente) VALUES (%s, %s, %s)",  # Incluir c_id_cliente
                (fecha_actual, subtotal, c_id_cliente)
            )
            connection.commit()

            # Obtener el ID de la venta recién registrada
            venta_id = cursor.lastrowid

        # Recuperar los valores de v_iva y v_total desde la base de datos
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT v_iva, v_total FROM ventas WHERE v_id_venta = %s", (venta_id,))
            venta = cursor.fetchone()

            # Registrar los detalles de la venta en la tabla 'detalles_ventas'
            cursor.execute(
                "INSERT INTO detalles_ventas (d_id_producto, d_id_venta, d_precio_producto, d_cantidad_producto) "
                "VALUES (%s, %s, %s, %s)",
                (producto_id, venta_id, precio_producto, cantidad_vendida)
            )
            connection.commit()

        # Actualizar el stock del producto
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE productos SET p_stock = p_stock - %s WHERE p_id_producto = %s",
                (cantidad_vendida, producto_id)
            )
            connection.commit()

        connection.close()

        # Generar la factura
        factura = {
            "venta_id": venta_id,
            "fecha": fecha_actual,
            "producto": producto["p_nom"],
            "cantidad": cantidad_vendida,
            "precio_unitario": precio_producto,
            "subtotal": subtotal,
            "iva": float(venta["v_iva"]),  # Recuperado de la base de datos
            "total": float(venta["v_total"])  # Recuperado de la base de datos
        }

        print("Factura generada:", factura)  # Depuración
        return render_template("factura.html", factura=factura)

    # Obtener todos los productos para mostrarlos en la lista
    with connection.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT * FROM productos WHERE p_stock > 0")
        productos = cursor.fetchall()
    connection.close()

    return render_template("ventas.html", productos=productos, c_nom=session['c_nom'])

# Ruta para obtener la lista de productos como JSON
@app.route("/productos")
def obtener_productos():
    connection = get_db_connection()
    with connection.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT p_id_producto, p_nom FROM productos")
        productos = cursor.fetchall()
    connection.close()
    return jsonify(productos)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000,
            debug=os.getenv("DEBUG", "False").lower() == "true")
