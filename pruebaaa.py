import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime
import sqlite3

# Función para obtener la conexión a la base de datos
def obtener_conexion():
    return sqlite3.connect("finanzas.db")

# Función para agregar un gasto
def agregar_gasto():
    monto = entry_gasto.get()
    categoria = combo_categoria.get()
    fecha = entry_fecha.get_date()  # Obtiene la fecha seleccionada
    if not monto.isdigit():
        label_cargando.config(text="Por favor, ingrese un monto válido")
        return
    if categoria == "Selecciona una categoría":
        label_cargando.config(text="Por favor, seleccione una categoría")
        return

    # Verificar si se ha seleccionado una fecha, si no usar la fecha actual
    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d")  # Usa la fecha actual en formato yyyy-mm-dd

    # Guardar el gasto en la base de datos
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO gastos (monto, fecha, categoria) VALUES (?, ?, ?)", (monto, fecha, categoria))
    conn.commit()
    conn.close()

    # Limpiar campos de entrada después de agregar el gasto
    entry_gasto.delete(0, tk.END)
    combo_categoria.set("Selecciona una categoría")
    label_cargando.config(text=f"Gasto de {monto} USD agregado en {categoria} para {fecha}")

# Función para cargar los datos en el Treeview
def cargar_datos():
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

# Interfaz gráfica
root = tk.Tk()
root.title("Gestión de Finanzas Personales")

label_progreso = tk.Label(root, text="Progreso: 0.00 USD", font=("Arial", 14))
label_progreso.pack(pady=10)

label_cargando = tk.Label(root, text="", font=("Arial", 12))
label_cargando.pack(pady=5)

# Entradas y botones para ingresos
entry_ingreso = tk.Entry(root, font=("Arial", 14))
entry_ingreso.pack(pady=5)
entry_ingreso.insert(0, "Monto Ingreso")

# Entradas y botones para gastos
entry_gasto = tk.Entry(root, font=("Arial", 14))
entry_gasto.pack(pady=5)
entry_gasto.insert(0, "Monto Gasto")

combo_categoria = ttk.Combobox(root, values=["Selecciona una categoría", "Comida", "Transporte", "Vivienda", "Entretenimiento"], font=("Arial", 14))
combo_categoria.pack(pady=5)

# Campo para seleccionar la fecha del gasto (puede ser cualquier fecha, si no se selecciona, se tomará la actual)
entry_fecha = DateEntry(root, font=("Arial", 14), date_pattern="yyyy-mm-dd")
entry_fecha.pack(pady=5)

button_ingreso = tk.Button(root, text="Agregar Ingreso", font=("Arial", 14), command=agregar_gasto)
button_ingreso.pack(pady=5)

button_gasto = tk.Button(root, text="Agregar Gasto", font=("Arial", 14), command=agregar_gasto)
button_gasto.pack(pady=5)

root.mainloop()
