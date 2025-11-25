import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# ================= CONFIGURACIÓN =================
root_dir = './parciales' 

# ================= FUNCIÓN DE LECTURA =================
def leer_reporte_custom(filepath):
    """
    Lee el formato específico: Time_Sec en línea 2 y lista de MSEs
    """
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 2: return None, None
        
        # Extraer Tiempo (último valor de la línea de datos)
        raw_data_line = lines[1].strip().split()
        if not raw_data_line: return None, None
        tiempo_total = float(raw_data_line[-1]) 
        
        # Extraer Historial MSE
        historial_mse = []
        leyendo_historial = False
        
        for line in lines:
            line = line.strip()
            if "Historial MSE" in line:
                leyendo_historial = True
                continue
            
            if leyendo_historial and line:
                try:
                    historial_mse.append(float(line))
                except ValueError:
                    pass 
        
        return tiempo_total, historial_mse
        
    except Exception as e:
        print(f"Error leyendo {filepath}: {e}")
        return None, None

# ================= CARGA DE DATOS =================
data_evolucion = []

patron_carpeta = re.compile(r"([a-zA-Z]+)_(\d+\.\d+)")

print("Leyendo archivos...")

for entry in os.listdir(root_dir):
    full_path = os.path.join(root_dir, entry)
    
    if os.path.isdir(full_path):
        match = patron_carpeta.match(entry)
        if match:
            pintura = match.group(1)      
            alpha = float(match.group(2)) 
            
            archivo_reporte = os.path.join(full_path, "reporte.txt")
            
            if os.path.exists(archivo_reporte):
                _, lista_mse = leer_reporte_custom(archivo_reporte)
                
                if lista_mse:
                    # Crear DataFrame temporal para esta ejecución
                    df_temp = pd.DataFrame({
                        'iteracion': range(len(lista_mse)), 
                        'mse': lista_mse
                    })
                    df_temp['pintura'] = pintura
                    df_temp['alpha'] = alpha
                    data_evolucion.append(df_temp)

# Concatenar todos los datos
if data_evolucion:
    df_total_evolucion = pd.concat(data_evolucion, ignore_index=True)
else:
    df_total_evolucion = pd.DataFrame()

print(f"Datos cargados. Total filas: {len(df_total_evolucion)}")

# ================= GRÁFICO NUEVO: Comparación Alpha 0.998 =================

# 1. Filtramos solo el alpha que nos interesa
target_alpha = 0.998
df_filtered = df_total_evolucion[df_total_evolucion['alpha'] == target_alpha]

if not df_filtered.empty:
    plt.figure(figsize=(12, 7))
    sns.set_style("whitegrid")
    
    # 2. Generamos el gráfico
    # x: iteración, y: mse, hue (color): pintura
    sns.lineplot(
        data=df_filtered, 
        x='iteracion', 
        y='mse', 
        hue='pintura', 
        linewidth=2,
        alpha=0.9
    )
    
    plt.title(f'Comparación de Convergencia (Alpha = {target_alpha})', fontsize=16)
    plt.xlabel('Iteraciones', fontsize=12)
    plt.ylabel('MSE', fontsize=12)
    plt.legend(title='Pintura', fontsize=10, title_fontsize=11)
    
    # Opcional: Escala logarítmica si las diferencias son muy grandes al inicio
    # plt.yscale('log') 
    
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    
    nombre_archivo = f'grafico_comparacion_alpha_{target_alpha}.png'
    plt.savefig(nombre_archivo, dpi=150)
    plt.show()
    print(f"Gráfico generado exitosamente: {nombre_archivo}")

else:
    print(f"No se encontraron datos para alpha = {target_alpha}")