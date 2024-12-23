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

# Establecer el umbral para los gastos hormiga
UMBRAL_GASTO_HORMIGA = 5.00  

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
    monto = entry_ingreso.get()  
    fecha = entry_fecha.get()
    categoria = combo_categoria.get()  

    if not monto:
        messagebox.showerror("Error", "Por favor, ingresa el monto del gasto.")
        return
    
    if not fecha:
        fecha = datetime.datetime.now().strftime("%Y-%m-%d") 

    if not categoria or categoria == 'Selecciona una categoría':
        messagebox.showerror("Error", "Por favor, selecciona una categoría de gasto.")
        return

    try:
        monto = float(monto)
    except ValueError:
        messagebox.showerror("Error", "El monto debe ser un número válido.")
        return

    # Verificar si el gasto es un gasto hormiga
    if monto < UMBRAL_GASTO_HORMIGA:
        respuesta = messagebox.askyesno("Gasto Hormiga", f"El monto de {monto} USD parece un gasto hormiga. ¿Estás seguro de que deseas agregarlo?")
        if not respuesta:
            return

    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO gastos (monto, categoria, fecha) VALUES (?, ?, ?)", (monto, categoria, fecha))
    conn.commit()
    conn.close()
    messagebox.showinfo("Gasto agregado", "Gasto registrado correctamente.")
    actualizar_progreso()
    entry_ingreso.delete(0, tk.END)
    combo_categoria.set("Selecciona una categoría")
    label_cargando.config(text=f"Gasto de {monto} USD agregado en {categoria} para {fecha}")

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
        try:
            df = pd.DataFrame(datos, columns=["Categoria", "Total"])
            if df.empty:
                messagebox.showwarning("Sin datos", "No hay datos suficientes para generar un gráfico.")
                return
            fig = go.Figure(data=[go.Pie(labels=df["Categoria"], values=df["Total"], textinfo="label+percent", hole=0.3)])
            fig.update_layout(title="Distribución de Gastos por Categoría", template="plotly_white")
            fig.show()
        except Exception as e:
            print(f"Error al generar gráfico: {e}")
            messagebox.showerror("Error", "Hubo un problema al generar el gráfico.")
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
        width=0.1
    ))

    fig.add_trace(go.Bar(
        x=df["Mes"], 
        y=df["Gastos"], 
        name="Gastos", 
        marker_color="lightcoral", 
        width=0.1
    ))

    fig.update_layout(
        barmode="group", 
        title="Progreso Mensual: Ingresos vs Gastos", 
        template="plotly_white",
        height=1500,
        margin={"t": 50, "b": 50, "l": 50, "r": 50}
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

        tree.pack(fill=tk.BOTH, expand=True)
        for fecha, monto in ingresos:
            tree.insert("", tk.END, values=("Ingreso", fecha, f"{monto:.2f}"))

        for fecha, categoria, monto in gastos:
            tree.insert("", tk.END, values=("Gasto", fecha, categoria, f"{monto:.2f}"))

        conn.close()

    # Crear ventana con tabla
    estado_ventana = tk.Toplevel(root)
    estado_ventana.title("Estado de Cuenta")
    tree = ttk.Treeview(estado_ventana, columns=("Tipo", "Fecha", "Categoría/Monto"), show="headings")
    tree.heading("Tipo", text="Tipo")
    tree.heading("Fecha", text="Fecha")
    tree.heading("Categoría/Monto", text="Categoría/Monto")
    
    cargar_datos()


# Crear interfaz gráfica
root = tk.Tk()
root.title("Gestión de Finanzas Personales")

frame_izq = tk.Frame(root)
frame_izq.pack(side=tk.LEFT, padx=20, pady=20)

frame_derecho = tk.Frame(root)
frame_derecho.pack(side=tk.LEFT, padx=20, pady=20)

label_ingreso = tk.Label(frame_izq, text="Monto:")
label_ingreso.grid(row=0, column=0, padx=10, pady=10)

entry_ingreso = tk.Entry(frame_izq)
entry_ingreso.grid(row=0, column=1, padx=10, pady=10)

label_fecha = tk.Label(frame_izq, text="Fecha (YYYY-MM-DD):")
label_fecha.grid(row=1, column=0, padx=10, pady=10)

entry_fecha = tk.Entry(frame_izq)
entry_fecha.grid(row=1, column=1, padx=10, pady=10)

label_categoria = tk.Label(frame_izq, text="Categoría de Gasto:")
label_categoria.grid(row=2, column=0, padx=10, pady=10)

combo_categoria = ttk.Combobox(frame_izq, values=["Selecciona una categoría", "Alimentos", "Transporte", "Vivienda", "Entretenimiento", "Otros"])
combo_categoria.set("Selecciona una categoría")
combo_categoria.grid(row=2, column=1, padx=10, pady=10)

# Botones
boton_agregar_ingreso = tk.Button(frame_izq, text="Agregar Ingreso", command=agregar_ingreso)
boton_agregar_ingreso.grid(row=3, column=0, padx=10, pady=10)

boton_agregar_gasto = tk.Button(frame_izq, text="Agregar Gasto", command=agregar_gasto)
boton_agregar_gasto.grid(row=3, column=1, padx=10, pady=10)

label_cargando = tk.Label(frame_izq, text="")
label_cargando.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

label_progreso = tk.Label(frame_izq, text="Progreso: 0.00 USD")
label_progreso.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

boton_mostrar_analisis = tk.Button(frame_derecho, text="Mostrar Análisis de Gastos", command=mostrar_analisis)
boton_mostrar_analisis.pack(pady=10)

boton_mostrar_progreso_mensual = tk.Button(frame_derecho, text="Mostrar Progreso Mensual", command=mostrar_progreso_mensual)
boton_mostrar_progreso_mensual.pack(pady=10)

boton_simular_presupuesto = tk.Button(frame_derecho, text="Simular Presupuesto", command=simular_presupuesto)
boton_simular_presupuesto.pack(pady=10)

boton_ver_presupuesto = tk.Button(frame_derecho, text="Ver Presupuesto", command=ver_presupuesto)
boton_ver_presupuesto.pack(pady=10)

boton_reiniciar_presupuesto = tk.Button(frame_derecho, text="Reiniciar Presupuesto", command=reiniciar_presupuesto)
boton_reiniciar_presupuesto.pack(pady=10)

boton_ver_estado = tk.Button(frame_derecho, text="Ver Estado de Cuenta", command=mostrar_estado_cuenta)
boton_ver_estado.pack(pady=10)

root.mainloop()
