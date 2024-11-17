class SimuladorDeGastos:
    def __init__(self, ingresos_mensuales, gastos_fijos, ahorro_objetivo):
        self.ingresos_mensuales = ingresos_mensuales
        self.gastos_fijos = gastos_fijos
        self.ahorro_objetivo = ahorro_objetivo

    def calcular_proyeccion(self, meses):
        resultado = []
        saldo_inicial = 0
        for mes in range(1, meses + 1):
            saldo_inicial += self.ingresos_mensuales - self.gastos_fijos
            resultado.append({
                "Mes": mes,
                "Saldo Estimado": saldo_inicial,
                "Cumple Ahorro": saldo_inicial >= self.ahorro_objetivo
            })
        return resultado
