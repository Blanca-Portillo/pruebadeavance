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
    monto = entry_ingreso.get()  
    fecha = entry_fecha.get()
    categoria = combo_categoria.get()  
   

    if not monto:
        messagebox.showerror("Error", "Por favor, ingresa el monto del gasto.")
        return
    
    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d") 


    if not categoria or categoria == 'Selecciona una categoría':
        messagebox.showerror("Error", "Por favor, selecciona una categoría de gasto.")
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

        tree.pack(fill=tk.BOTH, expand=True)
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

    # Conectar a la base de datos y obtener los datos
    conn = obtener_conexion()
    cursor = conn.cursor()

    # Obtener ingresos
    cursor.execute("SELECT 'Ingreso' AS tipo, monto, fecha, 'General' AS categoria FROM ingresos")
    ingresos = cursor.fetchall()

    # Verificación de datos obtenidos de ingresos
    print("Ingresos obtenidos:", ingresos)

     # Obtener ingresos
    cursor.execute("SELECT 'Ingreso' AS tipo, monto, fecha, 'General' AS categoria FROM ingresos")
    ingresos = cursor.fetchall()

    # Obtener gastos
    cursor.execute("SELECT 'Gasto' AS tipo, monto, fecha, categoria FROM gastos")
    gastos = cursor.fetchall()

    # Combinar ingresos y gastos
    registros = ingresos + gastos  # Combina los dos conjuntos de datos

    # Filtrar registros para asegurar que la fecha no sea None
    registros = [registro for registro in registros if registro[2] not in (None, "")]

    # Ordenar los registros por fecha
    registros.sort(key=lambda x: x[2])  # Ordenar solo los que tienen una fecha válida

    # Insertar registros en el Treeview
    for registro in registros:
        tree.insert("", "end", values=registro)


    conn.close()

    # Botón para cerrar la ventana
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

# Añadir el campo de categoría para los gastos
tk.Label(frame, text="Categoría de Gasto", font=("Arial", 12)).grid(row=2, column=0, pady=5)
combo_categoria = ttk.Combobox(frame, values=["Alimentación", "Transporte", "Vivienda", "Entretenimiento", "Otros"], font=("Arial", 12))
combo_categoria.grid(row=2, column=1, pady=5)

# Botón para agregar ingreso
ttk.Button(frame, text="Agregar Ingreso", command=agregar_ingreso).grid(row=3, column=1, pady=10)

# Botón para agregar gasto
ttk.Button(frame, text="Agregar Gasto", command=agregar_gasto).grid(row=4, column=1, pady=10)


# Presupuesto
tk.Label(frame, text="Presupuesto Total (USD)", font=("Arial", 12), bg="#E0F7FA", fg="#004D40").grid(row=6, column=0, pady=5, sticky="w")
entry_presupuesto = tk.Entry(frame, font=("Arial", 12))
entry_presupuesto.grid(row=6, column=1, pady=5)

ttk.Button(frame, text="Simular Presupuesto", command=simular_presupuesto).grid(row=7, column=0, columnspan=2, pady=10)

# Botón para ver presupuesto
ttk.Button(frame, text="Ver Presupuesto", command=ver_presupuesto).grid(row=8, column=0, columnspan=2, pady=10)

# Progreso
label_progreso = tk.Label(root, text="Progreso: 0.00 USD", font=("Arial", 14), bg="#E0F7FA", fg="#004D40")
label_progreso.pack(pady=10)

# Cargando
label_cargando = tk.Label(root, text="", font=("Arial", 12), bg="#E0F7FA", fg="red")

# Botones de análisis
frame_grafico = tk.Frame(root, bg="#E0F7FA")
frame_grafico.pack(pady=20, padx=15)
ttk.Button(frame_grafico, text="Ver Estado de Cuenta", command=mostrar_estado_cuenta).pack(fill="x", pady=5)
ttk.Button(frame, text="Reiniciar Presupuesto", command=reiniciar_presupuesto).grid(row=9, column=0, columnspan=2, pady=10)
ttk.Button(frame_grafico, text="Ver Análisis de Gastos", command=mostrar_analisis).pack(fill="x", pady=5)
ttk.Button(frame_grafico, text="Ver Progreso Mensual", command=mostrar_progreso_mensual).pack(fill="x", pady=5)

root.mainloop()