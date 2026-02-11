from flask import Flask, render_template_string, request, redirect, session, send_file
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import grey
from datetime import date
import datetime
import os

app = Flask(__name__)
app.secret_key = "club_futbol_secreto"
DB = "club.db"

# ---------- BASE DE DATOS ----------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        password TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS jugadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        documento TEXT,
        telefono TEXT,
        acudiente TEXT,
        categoria TEXT,
        estado TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS pagos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        jugador_id INTEGER,
        mes TEXT,
        valor INTEGER,
        fecha TEXT
    )""")

    if not c.execute("SELECT * FROM usuarios").fetchone():
        c.execute("INSERT INTO usuarios VALUES (NULL,'admin','1234')")

    conn.commit()
    conn.close()

# ---------- FACTURA ----------
def generar_factura(nombre, mes, valor):
    if not os.path.exists("facturas"):
        os.mkdir("facturas")

    numero = int(datetime.datetime.now().timestamp())
    archivo = f"facturas/factura_{numero}.pdf"

    c = canvas.Canvas(archivo, pagesize=letter)
    ancho, alto = letter

    # Encabezado
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, alto - 50, "CLUB DE FÚTBOL")

    c.setFont("Helvetica", 11)
    c.drawString(50, alto - 75, "Comprobante de Pago")

    c.setFont("Helvetica", 10)
    c.drawRightString(ancho - 50, alto - 60, f"Factura Nº {numero}")
    c.drawRightString(ancho - 50, alto - 80, f"Fecha: {datetime.date.today()}")

    c.line(50, alto - 110, ancho - 50, alto - 110)

    # Datos jugador
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, alto - 150, "Jugador:")
    c.setFont("Helvetica", 11)
    c.drawString(120, alto - 150, nombre)

    # Tabla
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, alto - 190, "Concepto")
    c.drawString(350, alto - 190, "Valor")
    c.line(50, alto - 195, ancho - 50, alto - 195)

    c.setFont("Helvetica", 10)
    c.drawString(50, alto - 220, f"Mensualidad {mes}")
    c.drawString(350, alto - 220, f"$ {valor}")

    # Total
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, alto - 270, "TOTAL:")
    c.drawString(350, alto - 270, f"$ {valor}")

    # Pie
    c.setFont("Helvetica", 9)
    c.setFillColor(grey)
    c.drawCentredString(ancho / 2, 90, "Gracias por su pago")
    c.drawCentredString(ancho / 2, 75, "Este documento sirve como comprobante")

    c.save()
    return archivo

# ---------- UTIL ----------
def protegido():
    return 'usuario' in session

# ---------- DISEÑO ----------
HTML_BASE = """
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Club de Fútbol</title>

<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">

<style>
body {
  min-height: 100vh;
  background:
    linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)),
    url('/static/cancha.jpg') no-repeat center center fixed;
  background-size: cover;
  font-family: 'Segoe UI', Tahoma, sans-serif;
}

/* CONTENEDOR PRINCIPAL */
.app-container {
  max-width: 1200px;
  margin: auto;
  padding-top: 30px;
}

/* TARJETA PRINCIPAL */
.card-app {
  background-color: rgba(255,255,255,0.97);
  border-radius: 20px;
  box-shadow: 0 15px 35px rgba(0,0,0,0.25);
  border: none;
}

/* HEADER */
.app-header {
  border-bottom: 1px solid #e9ecef;
  padding-bottom: 15px;
  margin-bottom: 25px;
}

.app-header h3 {
  font-weight: 800;
  margin: 0;
}

/* DASHBOARD */
.dashboard-card {
  border-radius: 18px;
  padding: 1.2rem;
  color: #fff;
  box-shadow: 0 8px 20px rgba(0,0,0,0.2);
}

.dashboard-card h6 {
  opacity: 0.9;
  margin-bottom: 5px;
}

.dashboard-card h3 {
  font-size: 2.2rem;
  font-weight: 800;
}

.bg-total { background: linear-gradient(135deg,#0d6efd,#084298); }
.bg-activo { background: linear-gradient(135deg,#198754,#0f5132); }
.bg-inactivo { background: linear-gradient(135deg,#dc3545,#842029); }
.bg-pagos { background: linear-gradient(135deg,#ffc107,#664d03); }

/* TABLAS */
.table {
  border-radius: 14px;
  overflow: hidden;
}

.table th {
  background-color: #f1f3f5;
  font-weight: 600;
}

/* BOTONES */
.btn {
  border-radius: 12px;
}

.btn-sm {
  padding: 5px 12px;
}
</style>
</head>

<body>
<div class="app-container">
  <div class="card card-app">
    <div class="card-body">

      <div class="app-header">
        <h3>⚽ Club de Fútbol</h3>
      </div>

      {{content|safe}}

    </div>
  </div>
</div>
</body>
</html>
"""

# ---------- LOGIN ----------
@app.route('/login', methods=['GET','POST'])
def login():
    error = ""
    if request.method == 'POST':
        u = request.form['usuario']
        p = request.form['password']
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        user = c.execute(
            "SELECT * FROM usuarios WHERE usuario=? AND password=?", (u,p)
        ).fetchone()
        conn.close()
        if user:
            session['usuario'] = u
            return redirect('/')
        error = "Credenciales incorrectas"

    return render_template_string(HTML_BASE, content=f"""
    <div class="col-md-4 mx-auto">
      <h4 class="mb-3">Iniciar sesión</h4>
      <form method="post">
        <input class="form-control mb-2" name="usuario" placeholder="Usuario">
        <input class="form-control mb-2" type="password" name="password" placeholder="Contraseña">
        <button class="btn btn-primary w-100">Ingresar</button>
      </form>
      <p class="text-danger mt-2">{error}</p>
    </div>
    """)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def index():
    if not protegido():
        return redirect('/login')

    q = request.args.get('q','')
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # ----- DASHBOARD -----
    total_jugadores = c.execute(
        "SELECT COUNT(*) FROM jugadores"
    ).fetchone()[0]

    activos = c.execute(
        "SELECT COUNT(*) FROM jugadores WHERE estado='Activo'"
    ).fetchone()[0]

    inactivos = c.execute(
        "SELECT COUNT(*) FROM jugadores WHERE estado='Inactivo'"
    ).fetchone()[0]

    mes_actual = datetime.date.today().strftime("%Y-%m")
    pagos_mes = c.execute(
        "SELECT COUNT(*) FROM pagos WHERE fecha LIKE ?",
        (f"{mes_actual}%",)
    ).fetchone()[0]
    # ----- FIN DASHBOARD -----

    # ----- LISTADO -----
    if q:
        jugadores = c.execute(
            "SELECT * FROM jugadores WHERE nombre LIKE ? OR documento LIKE ?",
            (f"%{q}%", f"%{q}%")
        ).fetchall()
    else:
        jugadores = c.execute(
            "SELECT * FROM jugadores"
        ).fetchall()

    # ✅ CERRAR SOLO UNA VEZ, AQUÍ
    conn.close()

    filas = ""
    for j in jugadores:
        filas += f"""
        <tr>
          <td>{j[1]}</td>
          <td>{j[5]}</td>
          <td>{j[6]}</td>
          <td>
            <a class="btn btn-sm btn-secondary" href="/historial/{j[0]}">Historial</a>
            <a class="btn btn-sm btn-success" href="/pagar/{j[0]}">Pagar</a>
            <a class="btn btn-sm btn-warning" href="/editar/{j[0]}">Editar</a>
            <a class="btn btn-sm btn-danger" href="/eliminar/{j[0]}" onclick="return confirm('¿Eliminar?')">Eliminar</a>
          </td>
        </tr>
        """

    return render_template_string(HTML_BASE, content=f"""
<div class="row mb-4 text-center">
  <div class="col-md-3">
    <div class="card border-primary">
      <div class="card-body">
        <h6>Total jugadores</h6>
        <h3>{total_jugadores}</h3>
      </div>
    </div>
  </div>

  <div class="col-md-3">
    <div class="card border-success">
      <div class="card-body">
        <h6>Activos</h6>
        <h3 class="text-success">{activos}</h3>
      </div>
    </div>
  </div>

  <div class="col-md-3">
    <div class="card border-danger">
      <div class="card-body">
        <h6>Inactivos</h6>
        <h3 class="text-danger">{inactivos}</h3>
      </div>
    </div>
  </div>

  <div class="col-md-3">
    <div class="card border-warning">
      <div class="card-body">
        <h6>Pagos del mes</h6>
        <h3>{pagos_mes}</h3>
      </div>
    </div>
  </div>
</div>

<form class="row g-2 mb-3">
  <div class="col-md-6">
    <input class="form-control" name="q" placeholder="Buscar jugador" value="{q}">
  </div>
  <div class="col-md-2">
    <button class="btn btn-primary w-100">Buscar</button>
  </div>
  <div class="col-md-4 text-end">
    <a class="btn btn-success" href="/nuevo">➕ Nuevo</a>
    <a class="btn btn-outline-dark" href="/logout">Salir</a>
  </div>
</form>

<table class="table table-striped">
  <tr><th>Nombre</th><th>Categoría</th><th>Estado</th><th>Acciones</th></tr>
  {filas}
</table>
""")

# ---------- NUEVO ----------
@app.route('/nuevo', methods=['GET','POST'])
def nuevo():
    if not protegido():
        return redirect('/login')

    if request.method == 'POST':
        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("""
            INSERT INTO jugadores 
            VALUES (NULL,?,?,?,?,?,?)
        """, (
            request.form['nombre'],
            request.form['documento'],
            request.form['telefono'],
            request.form['acudiente'],
            request.form['categoria'],
            'Activo'
        ))

        conn.commit()
        conn.close()
        return redirect('/')

    return render_template_string(HTML_BASE, content="""
    <h4 class="mb-3">Registrar jugador</h4>

    <form method="post" class="row g-3">

      <div class="col-md-6">
        <input class="form-control" name="nombre" placeholder="Nombre completo" required>
      </div>

      <div class="col-md-6">
        <input class="form-control" name="documento" placeholder="Documento" required>
      </div>

      <div class="col-md-6">
        <input class="form-control" name="telefono" placeholder="Teléfono">
      </div>

      <div class="col-md-6">
        <input class="form-control" name="acudiente" placeholder="Acudiente">
      </div>

      <div class="col-md-6">
        <select class="form-select" name="categoria" required>
          <option value="">Seleccionar categoría</option>
          <option>Sub 8</option>
          <option>Sub 10</option>
          <option>Sub 12</option>
          <option>Sub 14</option>
          <option>Sub 16</option>
          <option>Sub 18</option>
          <option>Mayores</option>
        </select>
      </div>

      <div class="col-12 mt-3">
        <button class="btn btn-primary">Guardar</button>
        <a class="btn btn-secondary ms-2" href="/">Volver</a>
      </div>

    </form>
    """)

# ---------- EDITAR ----------
@app.route('/editar/<int:id>', methods=['GET','POST'])
def editar(id):
    if not protegido():
        return redirect('/login')

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    jugador = c.execute(
        "SELECT * FROM jugadores WHERE id=?", (id,)
    ).fetchone()

    if request.method == 'POST':
        c.execute("""
            UPDATE jugadores SET
            nombre=?,
            documento=?,
            telefono=?,
            acudiente=?,
            categoria=?,
            estado=?
            WHERE id=?
        """, (
            request.form['nombre'],
            request.form['documento'],
            request.form['telefono'],
            request.form['acudiente'],
            request.form['categoria'],
            request.form['estado'],
            id
        ))

        conn.commit()
        conn.close()
        return redirect('/')

    conn.close()

    return render_template_string(HTML_BASE, content=f"""
    <h4 class="mb-3">Editar jugador</h4>

    <form method="post" class="row g-3">

      <div class="col-md-6">
        <input class="form-control" name="nombre" value="{jugador[1]}" required>
      </div>

      <div class="col-md-6">
        <input class="form-control" name="documento" value="{jugador[2]}" required>
      </div>

      <div class="col-md-6">
        <input class="form-control" name="telefono" value="{jugador[3]}">
      </div>

      <div class="col-md-6">
        <input class="form-control" name="acudiente" value="{jugador[4]}">
      </div>

      <div class="col-md-6">
        <select class="form-select" name="categoria" required>
          <option {"selected" if jugador[5]=="Sub 8" else ""}>Sub 8</option>
          <option {"selected" if jugador[5]=="Sub 10" else ""}>Sub 10</option>
          <option {"selected" if jugador[5]=="Sub 12" else ""}>Sub 12</option>
          <option {"selected" if jugador[5]=="Sub 14" else ""}>Sub 14</option>
          <option {"selected" if jugador[5]=="Sub 16" else ""}>Sub 16</option>
          <option {"selected" if jugador[5]=="Sub 18" else ""}>Sub 18</option>
          <option {"selected" if jugador[5]=="Mayores" else ""}>Mayores</option>
        </select>
      </div>

      <div class="col-md-6">
        <select class="form-select" name="estado">
          <option {"selected" if jugador[6]=="Activo" else ""}>Activo</option>
          <option {"selected" if jugador[6]=="Inactivo" else ""}>Inactivo</option>
        </select>
      </div>

      <div class="col-12 mt-3">
        <button class="btn btn-primary">Guardar cambios</button>
        <a class="btn btn-secondary ms-2" href="/">Volver</a>
      </div>

    </form>
    """)


# ---------- PAGAR ----------
@app.route('/pagar/<int:id>', methods=['GET','POST'])
def pagar(id):
    if not protegido(): return redirect('/login')
    if request.method == 'POST':
        mes = request.form['mes']
        valor = request.form['valor']
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        nombre = c.execute("SELECT nombre FROM jugadores WHERE id=?", (id,)).fetchone()[0]
        c.execute("INSERT INTO pagos VALUES (NULL,?,?,?,?)",
                  (id, mes, valor, str(datetime.date.today())))
        conn.commit()
        conn.close()
        return send_file(generar_factura(nombre, mes, valor), as_attachment=True)

    return render_template_string(HTML_BASE, content="""
    <h4>Registrar pago</h4>
    <form method="post">
      <input class="form-control mb-2" name="mes" placeholder="Mes">
      <input class="form-control mb-2" name="valor" placeholder="Valor">
      <button class="btn btn-success">Generar factura</button>
      <a class="btn btn-secondary" href="/">Volver</a>
    </form>
    """)

# ---------- HISTORIAL ----------
@app.route('/historial/<int:id>')
def historial(id):
    if not protegido(): return redirect('/login')
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    pagos = c.execute("SELECT mes,valor,fecha FROM pagos WHERE jugador_id=?", (id,)).fetchall()
    nombre = c.execute("SELECT nombre FROM jugadores WHERE id=?", (id,)).fetchone()[0]
    conn.close()

    filas = "".join([f"<li>{p[0]} - ${p[1]} ({p[2]})</li>" for p in pagos]) or "<li>Sin pagos</li>"

    return render_template_string(HTML_BASE, content=f"""
    <h4>Historial de pagos - {nombre}</h4>
    <ul>{filas}</ul>
    <a class="btn btn-secondary" href="/">Volver</a>
    """)

# ---------- ELIMINAR ----------
@app.route('/eliminar/<int:id>')
def eliminar(id):
    if not protegido(): return redirect('/login')
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM jugadores WHERE id=?", (id,))
    c.execute("DELETE FROM pagos WHERE jugador_id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    init_db() 