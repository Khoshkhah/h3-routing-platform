#pragma once

#include <string>
#include <vector>
#include <iostream>
#include <curl/curl.h>
#include <nlohmann/json.hpp>

// minimal dependency on external json lib
using json = nlohmann::json;

namespace routing {

struct RouteRequest {
    std::string dataset;
    double start_lat, start_lng;
    double end_lat, end_lng;
    std::string mode = "knn";
};

class Client {
    std::string base_url;

    static size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
        ((std::string*)userp)->append((char*)contents, size * nmemb);
        return size * nmemb;
    }

public:
    Client(std::string url = "http://localhost:8082") : base_url(url) {}

    json route(const RouteRequest& req) {
        CURL* curl = curl_easy_init();
        std::string readBuffer;
        
        if(curl) {
            json payload = {
                {"dataset", req.dataset},
                {"start_lat", req.start_lat}, {"start_lng", req.start_lng},
                {"end_lat", req.end_lat}, {"end_lng", req.end_lng},
                {"mode", req.mode}
            };
            std::string data = payload.dump();

            struct curl_slist* headers = NULL;
            headers = curl_slist_append(headers, "Content-Type: application/json");

            std::string url = base_url + "/route";
            curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
            curl_easy_setopt(curl, CURLOPT_POST, 1L);
            curl_easy_setopt(curl, CURLOPT_POSTFIELDS, data.c_str());
            curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
            curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

            curl_easy_perform(curl);
            curl_easy_cleanup(curl);
            
            try {
                return json::parse(readBuffer);
            } catch(...) {
                return json{{"error", "parse error"}, {"raw", readBuffer}};
            }
        }
        return json{{"error", "curl init failed"}};
    }
};

} // namespace routing
