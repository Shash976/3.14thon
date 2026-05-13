#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <sstream>

using namespace std;

vector<vector<string>> read_csv(const string& file_path) {
    ifstream file(file_path);
    string line;
    int header_end = -1;
    int line_num = 0;

    // Find the line with "***End_of_Header***"
    while (getline(file, line)) {
        if (line.find("***End_of_Header***") != string::npos) {
            header_end = line_num;
            break;
        }
        line_num++;
    }

    // Skip to data section and read CSV
    vector<vector<string>> data;
    int count = 0;
    while (getline(file, line) && count < 5) {  // Read first 5 rows
        istringstream iss(line);
        vector<string> row;
        string token;
        
        while (iss >> token) {
            row.push_back(token);
        }
        data.push_back(row);
        count++;
    }

    file.close();

    return data;
}

int main() {
    string file_path = R"(C:\Users\shash\OneDrive - purdue.edu\Pulse Rate Wearable Sensor\heartrate.data)";

    vector<vector<string>> data = read_csv(file_path);

    // Print data
    for (const auto& row : data) {
        for (const auto& cell : row) {
            cout << cell << " ";
        }
        cout << "\n";
    }

    return 0;
}

