import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import datetime

conn = sqlite3.connect('finanzas.db')
cursor = conn.cursor()

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

    cursor.execute("INSERT INTO ingresos (monto, fecha) VALUES (?, ?)", (monto, fecha))
    conn.commit()
    messagebox.showinfo("Ingreso agregado", "Ingreso registrado correctamente.")
    actualizar_progreso()

def agregar_gasto():
    monto = float(entry_gasto.get())
    categoria = entry_categoria.get()
    fecha = entry_fecha.get()

    if not validar_fecha(fecha):  
        messagebox.showerror("Error", "La fecha no es válida. Debe estar en formato YYYY-MM-DD.")
        return

    cursor.execute("INSERT INTO gastos (monto, categoria, fecha) VALUES (?, ?, ?)", (monto, categoria, fecha))
    conn.commit()
    messagebox.showinfo("Gasto agregado", "Gasto registrado correctamente.")
    verificar_gasto_hormiga(monto, categoria)
    actualizar_progreso()

def verificar_gasto_hormiga(monto, categoria):
    if monto < 5:  # Umbral para "gastos hormiga"
        messagebox.showwarning("Alerta de Gastos Hormiga", f"Has registrado un gasto pequeño en {categoria}. ¡Revisa tus gastos frecuentes!")

def actualizar_progreso():
    cursor.execute("SELECT SUM(monto) FROM ingresos")
    ingresos_totales = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(monto) FROM gastos")
    gastos_totales = cursor.fetchone()[0]
    progreso = ingresos_totales - gastos_totales

    label_progreso.config(text=f"Progreso: {progreso:.2f} USD")

def mostrar_analisis():
    cursor.execute("SELECT * FROM gastos")
    gastos = cursor.fetchall()
    df = pd.DataFrame(gastos, columns=["ID", "Monto", "Categoria", "Fecha"])

    categorias = df['Categoria'].value_counts()
    categorias.plot(kind='bar', title="Gastos por Categoría", color='skyblue')
    plt.ylabel('Cantidad de Gastos')
    plt.xlabel('Categorías')
    plt.tight_layout()
    plt.show()

def sugerir_ahorro():
    cursor.execute("SELECT SUM(monto) FROM gastos")
    gastos_totales = cursor.fetchone()[0]
    sugerencia = max(0, gastos_totales * 0.1)  
    messagebox.showinfo("Sugerencia de Ahorro", f"Recomendamos ahorrar al menos {sugerencia:.2f} USD este mes.")

def simular_presupuesto():
    presupuesto = float(entry_presupuesto.get())
    cursor.execute("SELECT SUM(monto) FROM gastos")
    gastos_totales = cursor.fetchone()[0]
    saldo_restante = presupuesto - gastos_totales
    messagebox.showinfo("Simulador de Presupuesto", f"Saldo restante: {saldo_restante:.2f} USD")

def mostrar_progreso_mensual():
    
    cursor.execute("""
        SELECT strftime('%Y-%m', fecha) as mes, SUM(monto) FROM ingresos
        GROUP BY mes
    """)
    ingresos_mensuales = cursor.fetchall()

    cursor.execute("""
        SELECT strftime('%Y-%m', fecha) as mes, SUM(monto) FROM gastos
        GROUP BY mes
    """)
    gastos_mensuales = cursor.fetchall()

    df_ingresos = pd.DataFrame(ingresos_mensuales, columns=["Mes", "Ingresos"])
    df_gastos = pd.DataFrame(gastos_mensuales, columns=["Mes", "Gastos"])

  
    df_progreso = pd.merge(df_ingresos, df_gastos, on="Mes", how="outer").fillna(0)

    
    df_progreso.set_index('Mes').plot(kind='bar', stacked=True, title="Progreso Mensual: Ingresos vs Gastos", color=['#4CAF50', '#FF5722'])
    plt.ylabel('Monto (USD)')
    plt.xlabel('Mes')
    plt.tight_layout()
    plt.show()



root = tk.Tk()
root.title("Gestión de Finanzas Personales")

root.geometry("600x800") 
root.resizable(False, False)  

root.config(bg="#f4f4f9")


header_label = tk.Label(root, text="Gestión de Finanzas Personales", font=("Arial", 18, "bold"), bg="#2196F3", fg="white", padx=20, pady=10)
header_label.grid(row=0, column=0, columnspan=2, pady=10)


tk.Label(root, text="Monto de Ingreso", font=("Arial", 12), bg="#f4f4f9").grid(row=1, column=0, pady=10)
entry_ingreso = tk.Entry(root, font=("Arial", 12), bd=2, relief="solid")
entry_ingreso.grid(row=1, column=1, pady=10, padx=10)

tk.Label(root, text="Fecha (YYYY-MM-DD)", font=("Arial", 12), bg="#f4f4f9").grid(row=2, column=0, pady=10)
entry_fecha = tk.Entry(root, font=("Arial", 12), bd=2, relief="solid")
entry_fecha.grid(row=2, column=1, pady=10, padx=10)

tk.Button(root, text="Agregar Ingreso", command=agregar_ingreso, bg="#4CAF50", fg="white", font=("Arial", 12), relief="raised").grid(row=3, column=0, columnspan=2, pady=10)

tk.Label(root, text="Monto de Gasto", font=("Arial", 12), bg="#f4f4f9").grid(row=4, column=0, pady=10)
entry_gasto = tk.Entry(root, font=("Arial", 12), bd=2, relief="solid")
entry_gasto.grid(row=4, column=1, pady=10, padx=10)

tk.Label(root, text="Categoría de Gasto", font=("Arial", 12), bg="#f4f4f9").grid(row=5, column=0, pady=10)


categorias_predeterminadas = ['Alimentos', 'Transporte', 'Entretenimiento', 'Salud', 'Ropa', 'Vivienda']

entry_categoria = ttk.Combobox(root, values=categorias_predeterminadas, font=("Arial", 12), state="normal")
entry_categoria.grid(row=5, column=1, pady=10, padx=10)
entry_categoria.set('') 

tk.Button(root, text="Agregar Gasto", command=agregar_gasto, bg="#FF5722", fg="white", font=("Arial", 12), relief="raised").grid(row=6, column=0, columnspan=2, pady=10)

label_progreso = tk.Label(root, text="Progreso: 0 USD", font=("Arial", 14, "bold"), bg="#f4f4f9", fg="#4CAF50")
label_progreso.grid(row=7, column=0, columnspan=2, pady=10)


tk.Button(root, text="Ver Análisis de Gastos", command=mostrar_analisis, bg="#2196F3", fg="white", font=("Arial", 12), relief="raised").grid(row=8, column=0, columnspan=2, pady=10)

# Progreso mensual
tk.Button(root, text="Ver Progreso Mensual", command=mostrar_progreso_mensual, bg="#673AB7", fg="white", font=("Arial", 12), relief="raised").grid(row=9, column=0, columnspan=2, pady=10)

# Sugerencia de ahorro
tk.Button(root, text="Sugerir Ahorro", command=sugerir_ahorro, bg="#FFC107", fg="white", font=("Arial", 12), relief="raised").grid(row=10, column=0, columnspan=2, pady=10)

# Simulación de presupuesto
tk.Label(root, text="Presupuesto", font=("Arial", 12), bg="#f4f4f9").grid(row=11, column=0, pady=10)
entry_presupuesto = tk.Entry(root, font=("Arial", 12), bd=2, relief="solid")
entry_presupuesto.grid(row=11, column=1, pady=10, padx=10)

tk.Button(root, text="Simular Presupuesto", command=simular_presupuesto, bg="#009688", fg="white", font=("Arial", 12), relief="raised").grid(row=12, column=0, columnspan=2, pady=10)

root.mainloop()
