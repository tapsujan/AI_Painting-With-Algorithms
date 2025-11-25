import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# ================= CONFIGURACIÓN =================
root_dir = './parciales' 

# Definición de las variables de mutación que se esperan en la primera sección del reporte.txt
MUTATION_VARS = ['Mut_X', 'Mut_Y', 'Mut_Size', 'Mut_Rot', 'Mut_R', 'Mut_G', 'Mut_B', 'Mut_Type']
NUM_MUT_VARS = len(MUTATION_VARS)

# ================= FUNCIÓN DE PARSEO PERSONALIZADA =================
def leer_reporte_histograma(filepath):
    """
    Lee la primera sección del reporte.txt para extraer los conteos de mutación
    y el tiempo total de ejecución.
    """
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 2: 
            return None, None
        
        # Línea 1 (índice 1) contiene los valores
        raw_data_line = lines[1].strip().split()
        
        # Esperamos al menos 9 valores: 8 conteos de mutación + 1 tiempo
        if len(raw_data_line) < NUM_MUT_VARS + 1:
            # print(f"Advertencia: Datos incompletos en {filepath}")
            return None, None
            
        # Los primeros 8 valores son los conteos
        counts = [float(x) for x in raw_data_line[:NUM_MUT_VARS]]
        
        # El 9º valor es el tiempo total (asumiendo que sigue el orden del header)
        tiempo_total = float(raw_data_line[NUM_MUT_VARS]) 
        
        return counts, tiempo_total
        
    except Exception as e:
        # print(f"Error leyendo {filepath}: {e}")
        return None, None

# ================= PROCESAMIENTO DE DATOS =================
data_raw = []

# Regex para capturar nombre y alpha desde la carpeta (ej: bach_0.995)
patron_carpeta = re.compile(r"([a-zA-Z]+)_(\d+\.\d+)")

print("Iniciando lectura de archivos y cálculo de eficiencia...")

for entry in os.listdir(root_dir):
    full_path = os.path.join(root_dir, entry)
    
    if os.path.isdir(full_path):
        match = patron_carpeta.match(entry)
        if match:
            pintura = match.group(1)      
            alpha = float(match.group(2)) 
            
            archivo_reporte = os.path.join(full_path, "reporte.txt")
            
            if os.path.exists(archivo_reporte):
                counts, tiempo = leer_reporte_histograma(archivo_reporte)
                
                if counts is not None and tiempo is not None and tiempo > 0:
                    # Crear un diccionario para esta corrida
                    run_data = {'pintura': pintura, 'alpha': alpha}
                    
                    # Calcular la eficiencia (Conteo / Tiempo) por cada tipo de mutación
                    for i, mut_var in enumerate(MUTATION_VARS):
                        eficiencia = counts[i] / tiempo
                        run_data[mut_var] = eficiencia
                        
                    data_raw.append(run_data)

df_raw = pd.DataFrame(data_raw)

if df_raw.empty:
    print("No se pudieron cargar datos válidos para el histograma. Verifica el formato de reporte.txt.")
else:
    # 1. Transformar a formato "long" para que sea fácil de plotear en seaborn
    df_efficiency = df_raw.melt(
        id_vars=['pintura', 'alpha'], 
        value_vars=MUTATION_VARS,
        var_name='Mutacion', 
        value_name='Eficiencia'
    )

    # 2. Generar el gráfico de barras agrupado
    plt.figure(figsize=(14, 8))
    sns.set_style("whitegrid")

    # Usamos barplot con 'dodge' para agrupar por Mutación y segmentar por Pintura (color)
    sns.barplot(
        data=df_efficiency,
        x='Mutacion',
        y='Eficiencia',
        hue='pintura',
        ci='sd', # Muestra la desviación estándar como barra de error
        capsize=0.1
    )

    plt.title('Eficiencia Media de Mutación por Pintura', fontsize=16)
    plt.xlabel('Variable de Mutación', fontsize=12)
    plt.ylabel('Eficiencia Media (Mutaciones/Segundo)', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='Pintura')
    plt.tight_layout()

    filename = 'histograma_eficiencia_mutacion.png'
    plt.savefig(filename, dpi=150)
    plt.show()
    print(f"Gráfico generado exitosamente: {filename}")