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
    monto = float(entry_ingreso.get())
    fecha = entry_fecha.get()

    if not validar_fecha(fecha):
        messagebox.showerror("Error", "La fecha no es válida. Debe estar en formato YYYY-MM-DD.")
        return

    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ingresos (monto, fecha) VALUES (?, ?)", (monto, fecha))
    conn.commit()
    conn.close()
    messagebox.showinfo("Ingreso agregado", "Ingreso registrado correctamente.")
    actualizar_progreso()

def agregar_gasto():
    monto = float(entry_gasto.get())
    categoria = entry_categoria.get()
    fecha = entry_fecha.get()

    if not validar_fecha(fecha):
        messagebox.showerror("Error", "La fecha no es válida. Debe estar en formato YYYY-MM-DD.")
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
    # Usamos threading para evitar que la interfaz se congele
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

    # Eliminar el mensaje de carga
    label_cargando.config(text="")
    label_cargando.pack_forget()

def mostrar_progreso_mensual():
    # Usamos threading para evitar que la interfaz se congele
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
    fig.add_trace(go.Bar(x=df["Mes"], y=df["Ingresos"], name="Ingresos", marker_color="lightseagreen"))
    fig.add_trace(go.Bar(x=df["Mes"], y=df["Gastos"], name="Gastos", marker_color="lightcoral"))
    fig.update_layout(barmode="group", title="Progreso Mensual: Ingresos vs Gastos", template="plotly_white")
    fig.show()

    conn.close()

    # Eliminar el mensaje de carga
    label_cargando.config(text="")
    label_cargando.pack_forget()

# Interfaz principal
root = tk.Tk()
root.title("Gestión de Finanzas Personales")
root.geometry("500x700")
root.config(bg="#E0F7FA")

# Estilo moderno
style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", font=("Arial", 12), padding=10, relief="flat", background="#00796B", foreground="white")
style.map("TButton", background=[("active", "#004D40")])

# Título
header_label = tk.Label(root, text="Gestión de Finanzas Personales", font=("Arial", 18, "bold"), bg="#00796B", fg="#FFFFFF")
header_label.pack(pady=20, padx=10)

# Campos de ingreso
frame = tk.Frame(root, bg="#E0F7FA")
frame.pack(pady=10, padx=10)

tk.Label(frame, text="Monto de Ingreso", font=("Arial", 12), bg="#E0F7FA", fg="#004D40").grid(row=0, column=0, pady=5, sticky="w")
entry_ingreso = tk.Entry(frame, font=("Arial", 12))
entry_ingreso.grid(row=0, column=1, pady=5)

tk.Label(frame, text="Fecha (YYYY-MM-DD)", font=("Arial", 12), bg="#E0F7FA", fg="#004D40").grid(row=1, column=0, pady=5, sticky="w")
entry_fecha = DateEntry(frame, font=("Arial", 12), date_pattern="yyyy-mm-dd")
entry_fecha.grid(row=1, column=1, pady=5)

ttk.Button(frame, text="Agregar Ingreso", command=agregar_ingreso).grid(row=2, column=0, columnspan=2, pady=10)

# Campos de gasto
tk.Label(frame, text="Monto de Gasto", font=("Arial", 12), bg="#E0F7FA", fg="#004D40").grid(row=3, column=0, pady=5, sticky="w")
entry_gasto = tk.Entry(frame, font=("Arial", 12))
entry_gasto.grid(row=3, column=1, pady=5)

tk.Label(frame, text="Categoría de Gasto", font=("Arial", 12), bg="#E0F7FA", fg="#004D40").grid(row=4, column=0, pady=5, sticky="w")
categorias_predeterminadas = ['Alimentos', 'Transporte', 'Entretenimiento', 'Salud', 'Ropa', 'Vivienda']
entry_categoria = ttk.Combobox(frame, values=categorias_predeterminadas, font=("Arial", 12), state="readonly")
entry_categoria.grid(row=4, column=1, pady=5)
entry_categoria.set('')

ttk.Button(frame, text="Agregar Gasto", command=agregar_gasto).grid(row=5, column=0, columnspan=2, pady=10)

# Progreso y análisis
label_progreso = tk.Label(root, text="Progreso: 0 USD", font=("Arial", 14, "bold"), bg="#E0F7FA", fg="#00796B")
label_progreso.pack(pady=10)

label_cargando = tk.Label(root, text="", font=("Arial", 12), bg="#E0F7FA", fg="#004D40")

ttk.Button(root, text="Ver Análisis de Gasto por Categoría", command=mostrar_analisis).pack(pady=10)

ttk.Button(root, text="Ver Progreso Mensual", command=mostrar_progreso_mensual).pack(pady=10)

# Cargar progreso al inicio
actualizar_progreso()

# Ejecutar la interfaz
root.mainloop()
