import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sqlite3
import pandas as pd
import plotly.graph_objects as go
from tkcalendar import DateEntry
import datetime
import threading

# Función para crear nueva conexión en cada hilo
def obtener_conexion():
    return sqlite3.connect('finanzas.db')

# Funciones
def validar_fecha(fecha):
    """Valida si la fecha está en formato YYYY-MM-DD"""
    try:
        datetime.datetime.strptime(fecha, '%Y-%m-%d') 
        return True
    except ValueError:
        return False

def agregar_ingreso():
    monto = entry_ingreso.get()
    fecha = entry_fecha.get()

    if not monto:
        messagebox.showerror("Error", "Por favor, ingresa el monto del ingreso.")
        return

    if not validar_fecha(fecha):
        messagebox.showerror("Error", "La fecha no es válida. Debe estar en formato YYYY-MM-DD.")
        return

    try:
        monto = float(monto)
    except ValueError:
        messagebox.showerror("Error", "El monto debe ser un número válido.")
        return

    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ingresos (monto, fecha) VALUES (?, ?)", (monto, fecha))
    conn.commit()
    conn.close()
    messagebox.showinfo("Ingreso agregado", "Ingreso registrado correctamente.")
    actualizar_progreso()

def agregar_gasto():
    monto = entry_gasto.get()
    categoria = entry_categoria.get()
    fecha = entry_fecha_gasto.get()  # Obtener la fecha del gasto

    if not monto:
        messagebox.showerror("Error", "Por favor, ingresa el monto del gasto.")
        return

    if not categoria:
        messagebox.showerror("Error", "Por favor, selecciona una categoría de gasto.")
        return

    if not validar_fecha(fecha):
        messagebox.showerror("Error", "La fecha no es válida. Debe estar en formato YYYY-MM-DD.")
        return

    try:
        monto = float(monto)
    except ValueError:
        messagebox.showerror("Error", "El monto debe ser un número válido.")
        return

    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO gastos (monto, categoria, fecha) VALUES (?, ?, ?)", (monto, categoria, fecha))
    conn.commit()
    conn.close()
    messagebox.showinfo("Gasto agregado", "Gasto registrado correctamente.")
    actualizar_progreso()


def actualizar_progreso():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(monto) FROM ingresos")
    ingresos_totales = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(monto) FROM gastos")
    gastos_totales = cursor.fetchone()[0] or 0
    progreso = ingresos_totales - gastos_totales
    label_progreso.config(text=f"Progreso: {progreso:.2f} USD")
    conn.close()

def mostrar_analisis():
    label_cargando.config(text="Generando gráfico, por favor espere...")
    label_cargando.pack(pady=5)
    thread = threading.Thread(target=generar_grafico_analisis)
    thread.daemon = True
    thread.start()

def generar_grafico_analisis():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT categoria, SUM(monto) as total FROM gastos GROUP BY categoria")
    datos = cursor.fetchall()

    if datos:
        df = pd.DataFrame(datos, columns=["Categoria", "Total"])
        fig = go.Figure(data=[go.Pie(labels=df["Categoria"], values=df["Total"], textinfo="label+percent", hole=0.3)])
        fig.update_layout(title="Distribución de Gastos por Categoría", template="plotly_white")
        fig.show()
    else:
        messagebox.showinfo("Sin datos", "No hay gastos registrados para analizar.")
    conn.close()

    label_cargando.config(text="")
    label_cargando.pack_forget()

def mostrar_progreso_mensual():
    label_cargando.config(text="Generando gráfico, por favor espere...")
    label_cargando.pack(pady=5)
    thread = threading.Thread(target=generar_grafico_progreso_mensual)
    thread.daemon = True
    thread.start()

def generar_grafico_progreso_mensual():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(""" 
        SELECT strftime('%Y-%m', fecha) as mes, SUM(monto) as ingresos FROM ingresos GROUP BY mes
    """)
    ingresos_mensuales = cursor.fetchall()

    cursor.execute(""" 
        SELECT strftime('%Y-%m', fecha) as mes, SUM(monto) as gastos FROM gastos GROUP BY mes
    """)
    gastos_mensuales = cursor.fetchall()

    df_ingresos = pd.DataFrame(ingresos_mensuales, columns=["Mes", "Ingresos"])
    df_gastos = pd.DataFrame(gastos_mensuales, columns=["Mes", "Gastos"])

    df = pd.merge(df_ingresos, df_gastos, on="Mes", how="outer").fillna(0)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["Mes"], 
        y=df["Ingresos"], 
        name="Ingresos", 
        marker_color="lightseagreen", 
        width=0.1  # Hacer las barras más delgadas (ancho más pequeño)
    ))

    fig.add_trace(go.Bar(
        x=df["Mes"], 
        y=df["Gastos"], 
        name="Gastos", 
        marker_color="lightcoral", 
        width=0.1  # Hacer las barras más delgadas (ancho más pequeño)
    ))

    fig.update_layout(
        barmode="group", 
        title="Progreso Mensual: Ingresos vs Gastos", 
        template="plotly_white",
        height=1500,  # Aumentar la altura del gráfico
        margin={"t": 50, "b": 50, "l": 50, "r": 50}  # Ajustar márgenes si es necesario
    )

    fig.show()
    conn.close()

    label_cargando.config(text="")
    label_cargando.pack_forget()

def reiniciar_presupuesto():
    confirmacion = messagebox.askyesno("Confirmar", "¿Estás seguro de que deseas reiniciar todos los datos?")
    if confirmacion:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ingresos")
        cursor.execute("DELETE FROM gastos")
        conn.commit()
        conn.close()
        actualizar_progreso()
        messagebox.showinfo("Reinicio", "Se han reiniciado todos los datos.")

def mostrar_estado_cuenta():
    def cargar_datos():
        conn = obtener_conexion()
        cursor = conn.cursor()

        # Cargar ingresos
        cursor.execute("SELECT fecha, monto FROM ingresos")
        ingresos = cursor.fetchall()

        # Cargar gastos
        cursor.execute("SELECT fecha, categoria, monto FROM gastos")
        gastos = cursor.fetchall()

        # Limpiar Treeview
        for row in tree.get_children():
            tree.delete(row)

        # Mostrar ingresos
        for ingreso in ingresos:
            tree.insert("", "end", values=("Ingreso", ingreso[1], ingreso[0], "N/A"))

        # Mostrar gastos
        for gasto in gastos:
            tree.insert("", "end", values=("Gasto", gasto[2], gasto[0], gasto[1]))  # Aquí se cambió el orden para mostrar monto, fecha y categoría

        conn.close()

    # Crear Treeview para mostrar los datos
    tree_window = tk.Toplevel(root)
    tree_window.title("Estado de Cuenta")
    
    tree = ttk.Treeview(tree_window, columns=("Tipo", "Monto", "Fecha", "Categoría"), show="headings")
    tree.heading("Tipo", text="Tipo")
    tree.heading("Monto", text="Monto (USD)")
    tree.heading("Fecha", text="Fecha")
    tree.heading("Categoría", text="Categoría")

    tree.pack(fill=tk.BOTH, expand=True)

    cargar_datos_button = tk.Button(tree_window, text="Cargar Datos", command=cargar_datos)
    cargar_datos_button.pack(pady=10)

    conn = obtener_conexion()
    cursor = conn.cursor()

    cursor.execute("SELECT 'Ingreso' AS tipo, monto, fecha, 'General' AS categoria FROM ingresos")
    ingresos = cursor.fetchall()

    cursor.execute("SELECT 'Gasto' AS tipo, monto, fecha, categoria FROM gastos")
    gastos = cursor.fetchall()

    registros = ingresos + gastos

    registros = [registro for registro in registros if registro[2] is not None]

    registros.sort(key=lambda x: x[2])

    for registro in registros:
        tree.insert("", "end", values=registro)

    conn.close()

    ttk.Button(tree_window, text="Cerrar", command=tree_window.destroy).pack(pady=10)


# Interfaz principal
root = tk.Tk()
root.title("Gestión de Finanzas Personales")
root.geometry("500x750")
root.config(bg="#E0F7FA")

# Estilo moderno
style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", font=("Arial", 12), padding=10, relief="flat", background="#00796B", foreground="white")
style.map("TButton", background=[("active", "#004D40")])

style.configure("TLabel", font=("Arial", 12), background="#E0F7FA")

style.configure("TEntry", font=("Arial", 12), padding=5)

# Widgets
label_progreso = ttk.Label(root, text="Progreso: 0.00 USD", font=("Arial", 14), anchor="center")
label_progreso.pack(pady=10)

entry_ingreso = ttk.Entry(root, font=("Arial", 12))
entry_ingreso.pack(pady=5)

entry_fecha = DateEntry(root, width=12, background="darkblue", foreground="white", borderwidth=2)
entry_fecha.pack(pady=5)

button_ingreso = ttk.Button(root, text="Agregar Ingreso", command=agregar_ingreso)
button_ingreso.pack(pady=5)

entry_gasto = ttk.Entry(root, font=("Arial", 12))
entry_gasto.pack(pady=5)

entry_categoria = ttk.Combobox(root, values=["Alimentación", "Transporte", "Ropa", "Entretenimiento", "Otros"], font=("Arial", 12))
entry_categoria.pack(pady=5)

entry_fecha_gasto = DateEntry(root, width=12, background="darkblue", foreground="white", borderwidth=2)
entry_fecha_gasto.pack(pady=5)

button_gasto = ttk.Button(root, text="Agregar Gasto", command=agregar_gasto)
button_gasto.pack(pady=5)

label_cargando = ttk.Label(root, text="", font=("Arial", 10), foreground="red")

# Botones
button_analisis = ttk.Button(root, text="Análisis de Gastos", command=mostrar_analisis)
button_analisis.pack(pady=5)

button_progreso_mensual = ttk.Button(root, text="Progreso Mensual", command=mostrar_progreso_mensual)
button_progreso_mensual.pack(pady=5)

button_reiniciar = ttk.Button(root, text="Reiniciar Datos", command=reiniciar_presupuesto)
button_reiniciar.pack(pady=5)

button_estado_cuenta = ttk.Button(root, text="Estado de Cuenta", command=mostrar_estado_cuenta)
button_estado_cuenta.pack(pady=5)

# Ejecutar la ventana principal
root.mainloop()
