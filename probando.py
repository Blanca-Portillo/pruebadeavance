import tkinter as tk
from tkinter import messagebox
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import datetime
from cryptography.fernet import Fernet

# Generar una clave para cifrado (solo una vez)
# key = Fernet.generate_key()
# with open("secret.key", "wb") as key_file:
#     key_file.write(key)

# Cargar la clave de cifrado
def load_key():
    return open("secret.key", "rb").read()

# Cifrar datos
def encrypt_data(data):
    key = load_key()
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data.encode())
    return encrypted_data

# Descifrar datos
def decrypt_data(encrypted_data):
    key = load_key()
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data).decode()
    return decrypted_data

# Conexión a la base de datos SQLite
conn = sqlite3.connect('finanzas.db')
cursor = conn.cursor()

# Crear tablas necesarias en la base de datos
cursor.execute('''
CREATE TABLE IF NOT EXISTS ingresos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monto REAL,
    fecha DATE
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monto REAL,
    categoria TEXT,
    fecha DATE
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS metas_ahorro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meta REAL,
    fecha DATE
)''')

conn.commit()

# Funciones de la app

def agregar_ingreso():
    try:
        monto = float(entry_ingreso.get())
        fecha = entry_fecha.get()
        encrypted_monto = encrypt_data(str(monto))
        cursor.execute("INSERT INTO ingresos (monto, fecha) VALUES (?, ?)", (encrypted_monto, fecha))
        conn.commit()
        messagebox.showinfo("Ingreso agregado", "Ingreso registrado correctamente.")
        actualizar_progreso()
    except ValueError:
        messagebox.showerror("Error", "Por favor, ingresa un monto válido.")

def agregar_gasto():
    try:
        monto = float(entry_gasto.get())
        categoria = entry_categoria.get()
        fecha = entry_fecha.get()
        encrypted_monto = encrypt_data(str(monto))
        cursor.execute("INSERT INTO gastos (monto, categoria, fecha) VALUES (?, ?, ?)", (encrypted_monto, categoria, fecha))
        conn.commit()
        messagebox.showinfo("Gasto agregado", "Gasto registrado correctamente.")
        verificar_gasto_hormiga(monto, categoria)
        actualizar_progreso()
    except ValueError:
        messagebox.showerror("Error", "Por favor, ingresa un monto válido.")

def verificar_gasto_hormiga(monto, categoria):
    if monto < 5:  # Umbral para "gastos hormiga"
        messagebox.showwarning("Alerta de Gastos Hormiga", f"Has registrado un gasto pequeño en {categoria}. ¡Revisa tus gastos frecuentes!")

def actualizar_progreso():
    cursor.execute("SELECT SUM(monto) FROM ingresos")
    ingresos_totales = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(monto) FROM gastos")
    gastos_totales = cursor.fetchone()[0]
    
    if ingresos_totales is None:
        ingresos_totales = 0
    if gastos_totales is None:
        gastos_totales = 0
    
    progreso = ingresos_totales - gastos_totales

    label_progreso.config(text=f"Progreso: {progreso} USD")

def mostrar_analisis():
    cursor.execute("SELECT * FROM gastos")
    gastos = cursor.fetchall()
    
    # Desencriptar los datos de los gastos
    gastos_descifrados = [(decrypt_data(gasto[1]), gasto[2], gasto[3]) for gasto in gastos]
    df = pd.DataFrame(gastos_descifrados, columns=["Monto", "Categoria", "Fecha"])
    
    # Análisis gráfico
    plt.figure(figsize=(8,6))
    df['Categoria'].value_counts().plot(kind='bar', title="Gastos por Categoría", color='skyblue')
    plt.xlabel("Categoría")
    plt.ylabel("Cantidad de Gastos")
    plt.show()

def sugerir_ahorro():
    cursor.execute("SELECT SUM(monto) FROM gastos")
    gastos_totales = cursor.fetchone()[0]
    sugerencia = max(0, gastos_totales * 0.1)  # Ahorro recomendado del 10%
    messagebox.showinfo("Sugerencia de Ahorro", f"Recomendamos ahorrar al menos {sugerencia} USD este mes.")

def simular_presupuesto():
    try:
        presupuesto = float(entry_presupuesto.get())
        cursor.execute("SELECT SUM(monto) FROM gastos")
        gastos_totales = cursor.fetchone()[0]
        saldo_restante = presupuesto - gastos_totales
        messagebox.showinfo("Simulador de Presupuesto", f"Saldo restante: {saldo_restante} USD")
    except ValueError:
        messagebox.showerror("Error", "Por favor, ingresa un presupuesto válido.")

# Interfaz de Usuario

root = tk.Tk()
root.title("Gestión de Finanzas Personales")

# Ingreso de datos
tk.Label(root, text="Monto de Ingreso").grid(row=0, column=0)
entry_ingreso = tk.Entry(root)
entry_ingreso.grid(row=0, column=1)

tk.Label(root, text="Fecha (YYYY-MM-DD)").grid(row=1, column=0)
entry_fecha = tk.Entry(root)
entry_fecha.grid(row=1, column=1)

tk.Button(root, text="Agregar Ingreso", command=agregar_ingreso).grid(row=2, column=0, columnspan=2)

tk.Label(root, text="Monto de Gasto").grid(row=3, column=0)
entry_gasto = tk.Entry(root)
entry_gasto.grid(row=3, column=1)

tk.Label(root, text="Categoría de Gasto").grid(row=4, column=0)
entry_categoria = tk.Entry(root)
entry_categoria.grid(row=4, column=1)

tk.Button(root, text="Agregar Gasto", command=agregar_gasto).grid(row=5, column=0, columnspan=2)

# Progreso
label_progreso = tk.Label(root, text="Progreso: 0 USD")
label_progreso.grid(row=6, column=0, columnspan=2)

# Analizar gastos
tk.Button(root, text="Ver Análisis de Gastos", command=mostrar_analisis).grid(row=7, column=0, columnspan=2)

# Sugerencias de ahorro
tk.Button(root, text="Ver Sugerencias de Ahorro", command=sugerir_ahorro).grid(row=8, column=0, columnspan=2)

# Simulador de presupuesto
tk.Label(root, text="Presupuesto Total").grid(row=9, column=0)
entry_presupuesto = tk.Entry(root)
entry_presupuesto.grid(row=9, column=1)

tk.Button(root, text="Simular Presupuesto", command=simular_presupuesto).grid(row=10, column=0, columnspan=2)

root.mainloop()

# Cerrar la conexión al finalizar
conn.close()
