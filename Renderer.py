import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# ================= CONFIGURACIÓN =================
root_dir = './parciales'  # Ruta a tu carpeta con los resultados

# ================= FUNCIÓN DE PARSEO PERSONALIZADA =================
def leer_reporte_custom(filepath):
    """
    Lee el formato específico de tu reporte.txt:
    - Línea 2: Contiene el Time_Sec al final.
    - Debajo de '--- Historial...': Lista de MSEs.
    """
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # 1. Extraer Tiempo Total
        # La línea 0 son los headers, la línea 1 son los datos finales.
        # Asumimos que el Time_Sec es la última columna (según tu archivo).
        raw_data_line = lines[1].strip().split()
        tiempo_total = float(raw_data_line[-1]) 
        
        # 2. Extraer Historial de MSE
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
                    pass # Ignorar líneas vacías o extrañas al final
        
        return tiempo_total, historial_mse
        
    except Exception as e:
        print(f"Error leyendo {filepath}: {e}")
        return None, None

# ================= PROCESAMIENTO DE DATOS =================
data_resumen = []     # Gráfico 1: Puntos finales
data_evolucion = []   # Gráfico 2: Curvas

# Regex para capturar nombre y alpha desde la carpeta (ej: bach_0.995)
patron_carpeta = re.compile(r"([a-zA-Z]+)_(\d+\.\d+)")

print("Iniciando lectura de archivos...")

for entry in os.listdir(root_dir):
    full_path = os.path.join(root_dir, entry)
    
    if os.path.isdir(full_path):
        match = patron_carpeta.match(entry)
        if match:
            pintura = match.group(1)    # ej: bach
            alpha = float(match.group(2)) # ej: 0.995
            
            archivo_reporte = os.path.join(full_path, "reporte.txt")
            
            if os.path.exists(archivo_reporte):
                tiempo, lista_mse = leer_reporte_custom(archivo_reporte)
                
                if tiempo is not None and lista_mse:
                    # --- Datos para Gráfico 1 (Resumen) ---
                    mse_final = lista_mse[-1] # El último valor del historial
                    data_resumen.append({
                        'pintura': pintura,
                        'alpha': alpha,
                        'mse_final': mse_final,
                        'tiempo_total': tiempo
                    })
                    
                    # --- Datos para Gráfico 2 (Evolución) ---
                    # Creamos un DataFrame temporal para esta ejecución
                    df_temp = pd.DataFrame({
                        'iteracion': range(len(lista_mse)),
                        'mse': lista_mse
                    })
                    df_temp['pintura'] = pintura
                    df_temp['alpha'] = alpha
                    data_evolucion.append(df_temp)

# Unimos toda la data de evolución
if data_evolucion:
    df_total_evolucion = pd.concat(data_evolucion, ignore_index=True)
else:
    df_total_evolucion = pd.DataFrame()

df_resumen = pd.DataFrame(data_resumen)

print(f"Procesados {len(df_resumen)} reportes correctamente.")

# ================= GRAFICO 1: COMPARACIÓN FINAL (Scatter Plot) =================
if not df_resumen.empty:
    plt.figure(figsize=(12, 7))
    sns.set_style("whitegrid")
    
    # Ordenamos para que la leyenda salga limpia
    df_resumen = df_resumen.sort_values(by=['pintura', 'alpha'])
    
    # Plot principal
    plot = sns.scatterplot(
        data=df_resumen, 
        x='tiempo_total', 
        y='mse_final', 
        hue='pintura', 
        style='pintura', # Distinta forma por pintura para accesibilidad
        s=150,           # Tamaño de puntos
        alpha=0.8
    )
    
    # Anotar el valor de Alpha al lado de cada punto
    for i, row in df_resumen.iterrows():
        plt.text(
            row['tiempo_total'], 
            row['mse_final'], 
            f"  α={row['alpha']}", 
            fontsize=9, 
            ha='left', 
            va='center',
            color='black'
        )

    plt.title('Comparación de Eficiencia: MSE Final vs Tiempo de Cómputo', fontsize=16)
    plt.xlabel('Tiempo Total (segundos)', fontsize=12)
    plt.ylabel('MSE Final (Menor es mejor)', fontsize=12)
    plt.legend(title='Pintura', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    
    plt.savefig('grafico_1_comparacion_final.png', dpi=300)
    plt.show()
    print("-> Gráfico 1 guardado: grafico_1_comparacion_final.png")
else:
    print("No hay datos suficientes para el gráfico 1.")

# ================= GRAFICO 2: EVOLUCIÓN (Uno por pintura) =================
if not df_total_evolucion.empty:
    pinturas_unicas = df_total_evolucion['pintura'].unique()
    
    for pintura in pinturas_unicas:
        plt.figure(figsize=(12, 6))
        
        # Filtramos datos de esa pintura
        data_local = df_total_evolucion[df_total_evolucion['pintura'] == pintura]
        
        # Lineplot: X=Iteración, Y=MSE, Color=Alpha
        sns.lineplot(
            data=data_local, 
            x='iteracion', 
            y='mse', 
            hue='alpha', 
            palette='viridis', # Gradiente de colores para ver la "temperatura" del alpha
            linewidth=1.5
        )
        
        plt.title(f'Evolución de Convergencia - Pintura: {pintura.upper()}', fontsize=15)
        plt.xlabel('Iteraciones', fontsize=12)
        plt.ylabel('Mean Squared Error (MSE)', fontsize=12)
        
        # NOTA: El MSE suele bajar muy rápido al inicio. 
        # Si se ve todo aplastado, descomenta la siguiente línea:
        # plt.yscale('log') 
        
        plt.legend(title='Alpha', loc='upper right')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        
        filename = f'grafico_2_evolucion_{pintura}.png'
        plt.savefig(filename, dpi=300)
        plt.close()
        print(f"-> Gráfico 2 guardado: {filename}")
else:
    print("No hay datos suficientes para los gráficos de evolución.")