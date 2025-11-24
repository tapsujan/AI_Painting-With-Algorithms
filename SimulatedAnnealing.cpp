#include "stroke.h"
#include <iostream>
#include <random>
#include <vector>
#include <string>
#include <cmath>
#include <limits>
#include <algorithm>
#include <format>
#include <filesystem> // C++17: Para crear directorios
#include <fstream>    // Para escribir el .txt
#include <chrono>     // Para medir el tiempo

namespace fs = std::filesystem;

// --- RNG Global  ---
static std::mt19937 rng(std::random_device{}());

int randInt(int min, int max) {
    std::uniform_int_distribution<int> dist(min, max);
    return dist(rng);
}

float randFloat(float min, float max) {
    std::uniform_real_distribution<float> dist(min, max);
    return dist(rng);
}

template <typename T>
static inline T clampT(T v, T lo, T hi) {
    return (v < lo) ? lo : (v > hi) ? hi : v;
}

// --- Parámetros del Problema ---
const int N_STROKES = 50; 
Canvas C_temp(0, 0);

// --- Estructura para Estadísticas ---
struct RunStats {
    long long accepted_mutations[8] = {0}; // Contadores para cada tipo de parámetro
    // 0:x, 1:y, 2:size, 3:rot, 4:r, 5:g, 6:b, 7:type
    std::vector<double> mse_history;
};

// --- Funciones del Modelo ---

double calculate_mse(const std::vector<Stroke>& solution, const Canvas& C_target) {
    // 1. Renderizar
    C_temp.clear(255, 255, 255); 
    render(solution, C_temp);   

    // 2. Calcular MSE
    double mse = 0.0;
    const size_t num_pixels = C_target.width * C_target.height;
    if (num_pixels == 0) return std::numeric_limits<double>::max();

    for (size_t i = 0; i < num_pixels * 3; ++i) {
        double diff = (double)C_temp.rgb[i] - (double)C_target.rgb[i];
        mse += diff * diff;
    }
    return mse / (double)(num_pixels * 3);
}

/**
 * Mutate: Ahora recibe param_idx desde fuera para poder trackearlo
 */
void apply_mutation(Stroke& t, int param_idx, int num_brushes) {
    float pos_change = randFloat(-0.05f, 0.05f);
    float size_change = randFloat(-0.02f, 0.02f);
    float rot_change = randFloat(-10.0f, 10.0f);
    int color_change = randInt(-15, 15);

    switch (param_idx) {
        case 0: t.x_rel = clampT(t.x_rel + pos_change, 0.0f, 1.0f); break;
        case 1: t.y_rel = clampT(t.y_rel + pos_change, 0.0f, 1.0f); break;
        case 2: t.size_rel = clampT(t.size_rel + size_change, 0.05f, 1.0f); break;
        case 3: t.rotation_deg = std::fmod(t.rotation_deg + rot_change, 360.0f); break;
        case 4: t.r = (uint8_t)clampT((int)t.r + color_change, 0, 255); break;
        case 5: t.g = (uint8_t)clampT((int)t.g + color_change, 0, 255); break;
        case 6: t.b = (uint8_t)clampT((int)t.b + color_change, 0, 255); break;
        case 7: t.type = randInt(0, num_brushes - 1); break;
    }
}

std::vector<Stroke> create_random_solution(int N, int num_brushes) {
    std::vector<Stroke> solution;
    solution.reserve(N);
    for (int i = 0; i < N; ++i) {
        solution.emplace_back(
            randFloat(0.0f, 1.0f), randFloat(0.0f, 1.0f),       
            randFloat(0.1f, 0.4f), randFloat(0.0f, 360.0f),     
            randInt(0, num_brushes - 1), 
            randInt(0, 255), randInt(0, 255), randInt(0, 255)
        );
    }
    return solution;
}

// --- Main ---

int main(int a, char** args) {
    if (a != 3) {
        std::cerr << "Uso: ./programa [nombre_imagen] [alpha]\n";
        return 1;
    }

    // --- 0. Configuración de Directorios y Tiempo ---
    auto start_time = std::chrono::high_resolution_clock::now();
    
    std::string imgName = args[1];
    std::string alphaStr = args[2];
    float alpha = std::stof(alphaStr);
    
    // Crear carpeta ./parciales/nombre_alpha
    std::string folderPath = std::format("parciales/{}_{}", imgName, alphaStr);
    try {
        if (!fs::exists("parciales")) fs::create_directory("parciales");
        if (!fs::exists(folderPath)) fs::create_directory(folderPath);
    } catch (const std::exception& e) {
        std::cerr << "Error creando directorios: " << e.what() << "\n";
        return 1;
    }

    std::string fuente = "instancias/" + imgName + ".png";

    // --- 1. Cargar Recursos ---
    {
        ImageGray b0, b1, b2, b3;
        if (!loadImageGray("brushes/1.jpg", b0)) return 1;
        if (!loadImageGray("brushes/2.jpg", b1)) return 1;
        if (!loadImageGray("brushes/3.jpg", b2)) return 1;
        if (!loadImageGray("brushes/4.jpg", b3)) return 1;
        gBrushes.push_back(std::move(b0)); gBrushes.push_back(std::move(b1));
        gBrushes.push_back(std::move(b2)); gBrushes.push_back(std::move(b3));
    }
    const int NUM_BRUSHES = gBrushes.size();

    Canvas C_target(0, 0);
    if (!loadImageRGB_asCanvas(fuente, C_target)) {
        std::cerr << "Error cargando fuente.\n";
        return 1;
    }
    C_temp = Canvas(C_target.width, C_target.height);

    // --- 2. Parámetros SA ---
    double T = 10000.0;         
    const double T_final = 0.1; 
    const int iter_por_temp = 250; 

    // --- 3. Estado Inicial ---
    std::vector<Stroke> sol_actual = create_random_solution(N_STROKES, NUM_BRUSHES);
    double costo_actual = calculate_mse(sol_actual, C_target);

    std::vector<Stroke> sol_mejor = sol_actual;
    double costo_mejor = costo_actual;
    
    RunStats stats; // Estructura para guardar datos

    std::cout << "Inicio SA | Costo Inicial: " << costo_mejor << "\n";

    // --- 4. Bucle SA ---
    long long total_iter = 0;
    int temp_step = 0; // Contador para nombrar los archivos parciales

    while (T > T_final) {

        for (int i = 0; i < iter_por_temp; ++i) {
            
            // A. Crear copia para mutar
            std::vector<Stroke> sol_nueva = sol_actual;

            // B. Seleccionar qué mutar (para llevar registro)
            int stroke_idx = randInt(0, N_STROKES - 1);
            int param_idx = randInt(0, 7); // 0..7 variables

            // C. Aplicar mutación específica
            apply_mutation(sol_nueva[stroke_idx], param_idx, NUM_BRUSHES);
            
            // D. Evaluar
            double costo_nuevo = calculate_mse(sol_nueva, C_target);
            double delta_E = costo_nuevo - costo_actual;

            // E. Criterio de Aceptación
            bool accepted = false;
            if (delta_E < 0) {
                accepted = true; 
            } else {
                double prob = std::exp(-delta_E / T);
                if (randFloat(0.0f, 1.0f) < prob) {
                    accepted = true;
                }
            }

            if (accepted) {
                sol_actual = std::move(sol_nueva);
                costo_actual = costo_nuevo;
                // Registrar éxito de este parámetro
                stats.accepted_mutations[param_idx]++; 

                if (costo_actual < costo_mejor) {
                    sol_mejor = sol_actual;
                    costo_mejor = costo_actual;
                }
            }
        } 

        // 1. Guardar MSE actual
        stats.mse_history.push_back(costo_actual);

        // Enfriamiento
        T = T * alpha; 
        total_iter += iter_por_temp;
        temp_step++;

        /*
        if (total_iter % (iter_por_temp * 10) == 0)
            std::cout << "Iter: " << total_iter << " | T: " << T << " | MSE: " << costo_mejor << "\n";
        */

        if (total_iter % (iter_por_temp * 500) == 0) {
            Canvas C_parcial(C_target.width, C_target.height);
            render(sol_mejor, C_parcial); 
            std::string pName = std::format("{}/iter_{:04d}_T_{:.2f}.png", folderPath, temp_step, T);
            savePNG(C_parcial, pName);
        }
    }

    // --- 5. Finalización y Reporte ---
    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> diff = end_time - start_time;
    double duration_sec = diff.count();

    std::cout << "Terminado en " << duration_sec << "s. MSE Final: " << costo_mejor << "\n";

    // Guardar imagen final
    Canvas C_final(C_target.width, C_target.height);
    render(sol_mejor, C_final);
    savePNG(C_final, std::format("{}/FINAL.png", folderPath));

    // Guardar LOG .txt
    std::string logName = std::format("{}/reporte.txt", folderPath);
    std::ofstream logFile(logName);
    if (logFile.is_open()) {
        // Primera fila: Encabezados de contadores + Tiempo
        logFile << "Mut_X Mut_Y Mut_Size Mut_Rot Mut_R Mut_G Mut_B Mut_Type Time_Sec\n";
        
        // Segunda fila: Datos de contadores + Tiempo
        for(int k=0; k<8; ++k) logFile << stats.accepted_mutations[k] << " ";
        logFile << duration_sec << "\n";

        // %
        for(int k=0; k<8; ++k) logFile << stats.accepted_mutations[k]/total_iter << " ";
        logFile << duration_sec << "\n";

        logFile << "--- Historial MSE por cambio de temperatura ---\n";
        for (double val : stats.mse_history) {
            logFile << val << "\n";
        }
        logFile.close();
    }

    return 0;
}