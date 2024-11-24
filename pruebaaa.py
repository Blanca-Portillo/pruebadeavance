import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sqlite3
import pandas as pd
import plotly.graph_objects as go
from tkcalendar import DateEntry
import datetime
import threading

import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image, ImageTk

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
    fecha = entry_fecha.get()

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
    cursor.execute("INSERT INTO gastos (monto, categoria) VALUES (?, ?)", (monto, categoria))
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

def simular_presupuesto():
    presupuesto_texto = entry_presupuesto.get()
    
    if not presupuesto_texto:
        messagebox.showerror("Error", "Por favor, ingresa un presupuesto.")
        return
    
    try:
        presupuesto = float(presupuesto_texto)
    except ValueError:
        messagebox.showerror("Error", "El presupuesto debe ser un número válido.")
        return

    # Validación para presupuesto negativo
    if presupuesto < 0:
        messagebox.showerror("Error", "El presupuesto debe ser mayor o igual a 0.")
        return
    
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(monto) FROM gastos")
    gastos_totales = cursor.fetchone()[0] or 0
    saldo_restante = presupuesto - gastos_totales
    messagebox.showinfo("Simulador de Presupuesto", f"Saldo restante: {saldo_restante:.2f} USD")

    conn.close()

def ver_presupuesto():
    presupuesto_texto = entry_presupuesto.get()
    
    if not presupuesto_texto:
        messagebox.showerror("Error", "Por favor, ingresa un presupuesto.")
        return
    
    try:
        presupuesto = float(presupuesto_texto)
    except ValueError:
        messagebox.showerror("Error", "El presupuesto debe ser un número válido.")
        return

    # Validación para presupuesto negativo
    if presupuesto < 0:
        messagebox.showerror("Error", "El presupuesto debe ser mayor o igual a 0.")
        return
    
    messagebox.showinfo("Presupuesto Total", f"Tu presupuesto total es: {presupuesto:.2f} USD")


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
            tree.insert("", "end", values=("Gasto", gasto[1], "N/A", gasto[0]))

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
    

# Configuración de la interfaz gráfica
root = tk.Tk()
root.title("Gestión de Finanzas Personales")

# Etiquetas
label_ingreso = tk.Label(root, text="Monto Ingreso:")
label_ingreso.pack()

entry_ingreso = tk.Entry(root)
entry_ingreso.pack()

label_fecha = tk.Label(root, text="Fecha (YYYY-MM-DD):")
label_fecha.pack()

entry_fecha = tk.Entry(root)
entry_fecha.pack()

label_gasto = tk.Label(root, text="Monto Gasto:")
label_gasto.pack()

entry_gasto = tk.Entry(root)
entry_gasto.pack()

label_categoria = tk.Label(root, text="Categoría Gasto:")
label_categoria.pack()

entry_categoria = tk.Entry(root)
entry_categoria.pack()

label_presupuesto = tk.Label(root, text="Presupuesto:")
label_presupuesto.pack()

entry_presupuesto = tk.Entry(root)
entry_presupuesto.pack()

label_progreso = tk.Label(root, text="Progreso: 0.00 USD")
label_progreso.pack()

label_cargando = tk.Label(root, text="")
label_cargando.pack(pady=5)

# Botones
button_agregar_ingreso = tk.Button(root, text="Agregar Ingreso", command=agregar_ingreso)
button_agregar_ingreso.pack(pady=10)

button_agregar_gasto = tk.Button(root, text="Agregar Gasto", command=agregar_gasto)
button_agregar_gasto.pack(pady=10)

button_mostrar_analisis = tk.Button(root, text="Mostrar Análisis de Gastos", command=mostrar_analisis)
button_mostrar_analisis.pack(pady=10)

button_mostrar_progreso_mensual = tk.Button(root, text="Mostrar Progreso Mensual", command=mostrar_progreso_mensual)
button_mostrar_progreso_mensual.pack(pady=10)

button_simular_presupuesto = tk.Button(root, text="Simular Presupuesto", command=simular_presupuesto)
button_simular_presupuesto.pack(pady=10)

button_ver_presupuesto = tk.Button(root, text="Ver Presupuesto", command=ver_presupuesto)
button_ver_presupuesto.pack(pady=10)

button_reiniciar_presupuesto = tk.Button(root, text="Reiniciar Datos", command=reiniciar_presupuesto)
button_reiniciar_presupuesto.pack(pady=10)

button_mostrar_estado_cuenta = tk.Button(root, text="Mostrar Estado de Cuenta", command=mostrar_estado_cuenta)
button_mostrar_estado_cuenta.pack(pady=10)

root.mainloop()
