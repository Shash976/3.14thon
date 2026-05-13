#include <imgui.h>
#include <implot.h>

#include "imgui_impl_glfw.h"
#include "imgui_impl_opengl3.h"

#include <GLFW/glfw3.h>

#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <thread>
#include <chrono>
#include <iostream>

// ------------------------------------------------------------
// CSV reader (one row per call)
// ------------------------------------------------------------
bool read_next_csv_row(std::ifstream& file, double& t, double& i) {
    std::string line;
    if (!std::getline(file, line))
        return false;

    std::stringstream ss(line);
    std::string ts, is;

    std::getline(ss, ts, ',');
    std::getline(ss, is, ',');

    t = std::stod(ts);
    i = std::stod(is);
    return true;
}

// ------------------------------------------------------------
// Main
// ------------------------------------------------------------
int main() {
    // ----------------- GLFW -----------------
    if (!glfwInit()) {
        std::cerr << "Failed to initialize GLFW\n";
        return -1;
    }

    const char* glsl_version = "#version 330";
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);

    GLFWwindow* window = glfwCreateWindow(1280, 720,
        "Real-Time CSV Plot", nullptr, nullptr);
    if (!window) {
        glfwTerminate();
        return -1;
    }

    glfwMakeContextCurrent(window);
    glfwSwapInterval(1); // VSync

    // ----------------- ImGui -----------------
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImPlot::CreateContext();

    ImGuiIO& io = ImGui::GetIO();
    (void)io;

    ImGui::StyleColorsDark();

    ImGui_ImplGlfw_InitForOpenGL(window, true);
    ImGui_ImplOpenGL3_Init(glsl_version);

    // ----------------- CSV -----------------
    std::ifstream file("data.csv");
    if (!file.is_open()) {
        std::cerr << "Failed to open data.csv\n";
        return -1;
    }

    std::string header;
    std::getline(file, header); // skip header

    std::vector<double> time_data;
    std::vector<double> current_data;

    bool streaming = true;
    double playback_speed = 1.0;

    // ----------------- Main loop -----------------
    while (!glfwWindowShouldClose(window)) {
        glfwPollEvents();

        ImGui_ImplOpenGL3_NewFrame();
        ImGui_ImplGlfw_NewFrame();
        ImGui::NewFrame();

        // ----------------- UI -----------------
        ImGui::Begin("Controls");

        ImGui::Checkbox("Streaming", &streaming);
        ImGui::SliderDouble("Playback speed",
            &playback_speed, 0.1, 5.0, "%.1fx");

        ImGui::Text("Samples: %zu", time_data.size());

        ImGui::End();

        // ----------------- Data streaming -----------------
        if (streaming) {
            double t, i;
            if (read_next_csv_row(file, t, i)) {
                time_data.push_back(t);
                current_data.push_back(i);
            }
        }

        // ----------------- Plot -----------------
        ImGui::Begin("Real-Time Plot");

        if (ImPlot::BeginPlot("Current vs Time",
                              ImVec2(-1, 500))) {

            ImPlot::SetupAxes("Time (s)", "Current (A)");
            ImPlot::SetupAxisLimits(ImAxis_X1,
                time_data.empty() ? 0.0 : time_data.back() - 5.0,
                time_data.empty() ? 5.0 : time_data.back(),
                ImGuiCond_Always);

            if (!time_data.empty()) {
                ImPlot::PlotLine("Current",
                    time_data.data(),
                    current_data.data(),
                    time_data.size());
            }

            ImPlot::EndPlot();
        }

        ImGui::End();

        // ----------------- Render -----------------
        ImGui::Render();
        int display_w, display_h;
        glfwGetFramebufferSize(window, &display_w, &display_h);
        glViewport(0, 0, display_w, display_h);
        glClearColor(0.1f, 0.1f, 0.1f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
        glfwSwapBuffers(window);

        // ----------------- Timing -----------------
        std::this_thread::sleep_for(
            std::chrono::milliseconds(
                static_cast<int>(20 / playback_speed)
            )
        );
    }

    // ----------------- Cleanup -----------------
    ImPlot::DestroyContext();
    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();

    glfwDestroyWindow(window);
    glfwTerminate();

    return 0;
}
