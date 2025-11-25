import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# ================= CONFIGURACIÓN =================
# Ajusta si tu carpeta 'parciales' está en otro sitio
root_dir = './parciales' 

# ================= FUNCIÓN DE LECTURA =================
def leer_reporte_custom(filepath):
    """
    Lee el formato específico:
    - Línea 2: Time_Sec al final.
    - Debajo de '--- Historial...': Lista vertical de MSEs.
    """
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # 1. Extraer Tiempo Total
        # La línea 0 son headers. La línea 1 tiene los datos.
        if len(lines) < 2: return None, None
        
        raw_data_line = lines[1].strip().split()
        if not raw_data_line: return None, None
        
        # El tiempo suele ser la última columna
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
                    pass 
        
        return tiempo_total, historial_mse
        
    except Exception as e:
        print(f"Error leyendo {filepath}: {e}")
        return None, None

# ================= PROCESAMIENTO =================
data_resumen = []
data_evolucion = []

# Regex para carpetas tipo "bach_0.995"
patron_carpeta = re.compile(r"([a-zA-Z]+)_(\d+\.\d+)")

print("Leyendo archivos...")

for entry in os.listdir(root_dir):
    full_path = os.path.join(root_dir, entry)
    
    if os.path.isdir(full_path):
        match = patron_carpeta.match(entry)
        if match:
            pintura = match.group(1)      # ej: bach
            alpha = float(match.group(2)) # ej: 0.995
            
            archivo_reporte = os.path.join(full_path, "reporte.txt")
            
            if os.path.exists(archivo_reporte):
                tiempo, lista_mse = leer_reporte_custom(archivo_reporte)
                
                if tiempo is not None and lista_mse:
                    # Datos Resumen
                    mse_final = lista_mse[-1]
                    data_resumen.append({
                        'pintura': pintura,
                        'alpha': alpha,
                        'mse_final': mse_final,
                        'tiempo_total': tiempo
                    })
                    
                    # Datos Evolución
                    df_temp = pd.DataFrame({'iteracion': range(len(lista_mse)), 'mse': lista_mse})
                    df_temp['pintura'] = pintura
                    df_temp['alpha'] = alpha
                    data_evolucion.append(df_temp)

df_resumen = pd.DataFrame(data_resumen)
if data_evolucion:
    df_total_evolucion = pd.concat(data_evolucion, ignore_index=True)
else:
    df_total_evolucion = pd.DataFrame()

print(f"Procesados {len(df_resumen)} casos.")

# ================= GRÁFICO 1: COMPARACIÓN FINAL (Conectado) =================
if not df_resumen.empty:
    plt.figure(figsize=(12, 8))
    sns.set_style("whitegrid")
    
    # Obtenemos lista de pinturas y asignamos colores fijos
    pinturas = df_resumen['pintura'].unique()
    palette = sns.color_palette("tab10", n_colors=len(pinturas))
    pintura_colors = dict(zip(pinturas, palette))
    
    # Iteramos por cada pintura para dibujar su línea y puntos
    for pintura in pinturas:
        # Filtramos y ORDENAMOS por alpha (para que la línea siga la secuencia lógica)
        df_p = df_resumen[df_resumen['pintura'] == pintura].sort_values(by='alpha')
        
        # Dibujamos línea y marcadores
        plt.plot(df_p['tiempo_total'], df_p['mse_final'], 
                 marker='o', markersize=8, 
                 label=pintura, color=pintura_colors[pintura], 
                 linestyle='-', linewidth=2, alpha=0.8)
        
        # Ponemos las etiquetas simplificadas (ej: 0.995 -> 5)
        for _, row in df_p.iterrows():
            # Tomamos el último caracter de la representación string del float
            # ej: "0.995" -> "5"
            label_text = str(row['alpha'])[-1]
            
            plt.text(row['tiempo_total'], row['mse_final'], 
                     f" {label_text}", 
                     fontsize=10, fontweight='bold', 
                     color=pintura_colors[pintura],
                     ha='left', va='bottom')

    plt.title('Comparación Final: MSE vs Tiempo (Puntos conectados por orden de Alpha)', fontsize=14)
    plt.xlabel('Tiempo Total (segundos)', fontsize=12)
    plt.ylabel('MSE Final (Menor es mejor)', fontsize=12)
    plt.legend(title='Pintura')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    
    plt.savefig('grafico_1_comparacion_final.png', dpi=150)
    plt.show()
    print("Generado: grafico_1_comparacion_final.png")
else:
    print("Sin datos para gráfico 1.")

# ================= GRÁFICO 2: EVOLUCIÓN (Sin cambios mayores) =================
if not df_total_evolucion.empty:
    for pintura in df_total_evolucion['pintura'].unique():
        plt.figure(figsize=(12, 6))
        data_local = df_total_evolucion[df_total_evolucion['pintura'] == pintura]
        
        sns.lineplot(data=data_local, x='iteracion', y='mse', hue='alpha', 
                     palette='viridis', linewidth=1.5)
        
        plt.title(f'Evolución MSE - {pintura.upper()}', fontsize=14)
        plt.xlabel('Iteraciones')
        plt.ylabel('MSE')
        # plt.yscale('log') # Descomentar si quieres escala logarítmica
        plt.legend(title='Alpha')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        
        filename = f'grafico_2_evolucion_{pintura}.png'
        plt.savefig(filename, dpi=150)
        plt.close()
        print(f"Generado: {filename}")