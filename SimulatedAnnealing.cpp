#include "stroke.h"
#include <iostream>
#include <random>
#include <vector>
#include <string>
#include <cmath>
#include <limits>
#include <algorithm>

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

// Gracias Gemini
template <typename T>
static inline T clampT(T v, T lo, T hi) {
    return (v < lo) ? lo : (v > hi) ? hi : v;
}

// --- Parámetros del Problema ---
const int N_STROKES = 50; // Número de trazos.

// --- Lienzo Temporal ---
Canvas C_temp(0, 0);

// --- Funciones del Modelo ---

/**
 * MSE
 */
double calculate_mse(const std::vector<Stroke>& solution, const Canvas& C_target) {
    // 1. Renderizar la solución 'T' en el canvas temporal [cite: 106]
    C_temp.clear(255, 255, 255); // Fondo blanco
    render(solution, C_temp);   // 'render' es de stroke.cpp

    // 2. Calcular el MSE contra la imagen objetivo 'I' [cite: 102]
    double mse = 0.0;
    const size_t num_pixels = C_target.width * C_target.height;
    if (num_pixels == 0) return std::numeric_limits<double>::max();

    for (size_t i = 0; i < num_pixels * 3; ++i) {
        double diff = (double)C_temp.rgb[i] - (double)C_target.rgb[i];
        mse += diff * diff;
    }
    
    // Promedio de los errores al cuadrado [cite: 102]
    return mse / (double)(num_pixels * 3);
}

/**
 * Mutate (MOVIMIENTO)
 */
std::vector<Stroke> mutate_solution(std::vector<Stroke> s, int num_brushes) {
    if (s.empty()) return s;

    // 1. Elegir un trazo 't_j' al azar para mutar
    int stroke_idx = randInt(0, s.size() - 1);
    Stroke& t = s[stroke_idx];

    // 2. Elegir un parámetro de 't_j' al azar para mutar
    int param_idx = randInt(0, 7); // 8 parámetros en t_j

    // Definimos la "fuerza" de la mutación
    float pos_change = randFloat(-0.05f, 0.05f);
    float size_change = randFloat(-0.02f, 0.02f);
    float rot_change = randFloat(-10.0f, 10.0f);
    int color_change = randInt(-15, 15);

    switch (param_idx) {
        case 0: t.x_rel = clampT(t.x_rel + pos_change, 0.0f, 1.0f); break;
        case 1: t.y_rel = clampT(t.y_rel + pos_change, 0.0f, 1.0f); break;
        case 2: t.size_rel = clampT(t.size_rel + size_change, 0.05f, 1.0f); break; // Evitar tamaño 0
        case 3: t.rotation_deg = std::fmod(t.rotation_deg + rot_change, 360.0f); break;
        case 4: t.r = (uint8_t)clampT((int)t.r + color_change, 0, 255); break;
        case 5: t.g = (uint8_t)clampT((int)t.g + color_change, 0, 255); break;
        case 6: t.b = (uint8_t)clampT((int)t.b + color_change, 0, 255); break;
        case 7: t.type = randInt(0, num_brushes - 1); break; // Mutación
    }
    
    return s; // Devuelve la copia mutada
}

/**
 * Genera una solución inicial aleatoria
 * Crea un vector 'T' con N trazos aleatorios.
 */
std::vector<Stroke> create_random_solution(int N, int num_brushes) {
    std::vector<Stroke> solution;
    for (int i = 0; i < N; ++i) {
        solution.emplace_back(
            randFloat(0.0f, 1.0f),       // x_rel 
            randFloat(0.0f, 1.0f),       // y_rel 
            randFloat(0.1f, 0.4f),       // size_rel 
            randFloat(0.0f, 360.0f),     // rotation_deg 
            randInt(0, num_brushes - 1), // type 
            randInt(0, 255),             // R 
            randInt(0, 255),             // G 
            randInt(0, 255)              // B 
        );
    }
    return solution;
}


// --- Algoritmo Simulated Annealing ---

int main(int a, char** args) {
    if (a != 3) {
        std::cerr<<"Error en cantidad de argumentos.\n Por favor sigue el formato [nombre] [alpha]";
        return 1;
    }
    std::string fuente = "instancias/"+std::string(args[1])+".png";
    float alpha = std::stof(args[2]); //(T_nueva = T * alpha)
    // 1) Cargar brushes
    {
        ImageGray b0, b1, b2, b3;
        if (!loadImageGray("brushes/1.jpg", b0)) return 1;
        if (!loadImageGray("brushes/2.jpg", b1)) return 1;
        if (!loadImageGray("brushes/3.jpg", b2)) return 1;
        if (!loadImageGray("brushes/4.jpg", b3)) return 1;
        gBrushes.push_back(std::move(b0));
        gBrushes.push_back(std::move(b1));
        gBrushes.push_back(std::move(b2));
        gBrushes.push_back(std::move(b3));
    }
    const int NUM_BRUSHES = gBrushes.size();
    std::cout << "Cargados " << NUM_BRUSHES << " brushes.\n";

    // 2) Cargar Imagen Objetivo
    Canvas C_target(0, 0);
    if (!loadImageRGB_asCanvas(fuente, C_target)) {
        std::cerr << "Error: No se pudo cargar la fuente.\n";
        return 1;
    }
    std::cout << "Imagen objetivo cargada: " 
              << C_target.width << "x" << C_target.height << "\n";
    
    // Inicializar el canvas
    C_temp = Canvas(C_target.width, C_target.height);

    // 3) PARAMETROS
    double T = 10000.0;         // Temperatura inicial (alta)
    const double T_final = 0.1; // Temperatura final (baja)
    const int iter_por_temp = 250; // Iteraciones antes de enfriar

    // 4) Inicialización
    std::vector<Stroke> sol_actual = create_random_solution(N_STROKES, NUM_BRUSHES);
    double costo_actual = calculate_mse(sol_actual, C_target);

    std::vector<Stroke> sol_mejor = sol_actual;
    double costo_mejor = costo_actual;

    std::cout << "Costo inicial (MSE): " << costo_mejor << std::endl;

    // 5) Bucle Principal de Recocido (SA)
    long total_iter = 0;
    while (T > T_final) {

        for (int i = 0; i < iter_por_temp; ++i) {
            
            // Generar un vecino
            std::vector<Stroke> sol_nueva = mutate_solution(sol_actual, NUM_BRUSHES);
            
            // Evaluar el costo del vecino
            double costo_nuevo = calculate_mse(sol_nueva, C_target);

            // Calcular diferencia de energía/costo
            double delta_E = costo_nuevo - costo_actual;

            // Decidir si aceptamos la nueva solución
            if (delta_E < 0) {
                // Es mejor: aceptamos siempre
                sol_actual = std::move(sol_nueva);
                costo_actual = costo_nuevo;
            } else {
                // Es peor: aceptamos con probabilidad e^(-delta_E / T)
                double prob = std::exp(-delta_E / T);
                if (randFloat(0.0f, 1.0f) < prob) {
                    sol_actual = std::move(sol_nueva);
                    costo_actual = costo_nuevo;
                }
                // Si no, la descartamos y 'sol_actual' no cambia
            }

            // Actualizar la mejor solución global encontrada
            if (costo_actual < costo_mejor) {
                sol_mejor = sol_actual;
                costo_mejor = costo_actual;
            }
        } // fin iter_por_temp

        // Enfriar la temperatura
        T = T * alpha; 
        total_iter += iter_por_temp;

        // Imprimir progreso
        if (total_iter % (iter_por_temp * 10) == 0) {
            std::cout << "Iter: " << total_iter << ", T: " << T 
                      << ", Mejor MSE: " << costo_mejor << "\n";
        }

    } // fin while T

    std::cout << "Optimización terminada.\n";
    std::cout << "Mejor MSE final: " << costo_mejor << "\n";

    // 6) Renderizar y Guardar la MEJOR solución encontrada
    Canvas C_final(C_target.width, C_target.height);
    render(sol_mejor, C_final);

    if (!savePNG(C_final, "output.png")) {
        std::cerr << "Error guardando output.png\n";
        return 1;
    }
    
    std::cout << "OK: guardado output.png\n";
    return 0;
}