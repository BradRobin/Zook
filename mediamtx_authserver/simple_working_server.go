package main

import (
	"fmt"
	"net/http"
	"strings"
)

func corsMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next(w, r)
	}
}

func main() {
	// Health check
	http.HandleFunc("/", corsMiddleware(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprint(w, `{"status":"ok","message":"Zook Auth Server Running"}`)
	}))

	// Login endpoint - accepts Brad/12345678
	http.HandleFunc("/api/login", corsMiddleware(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		w.Header().Set("Content-Type", "application/json")

		// Read body
		buf := new(strings.Builder)
		_, err := buf.ReadFrom(r.Body)
		if err != nil {
			http.Error(w, "Error reading body", http.StatusBadRequest)
			return
		}

		body := buf.String()
		fmt.Println("Login request:", body)

		// Simple check for Brad and 12345678
		if strings.Contains(body, "Brad") && strings.Contains(body, "12345678") {
			fmt.Println("Login successful for Brad")
			w.WriteHeader(http.StatusOK)
			fmt.Fprint(w, "successfully logged in")
		} else {
			fmt.Println("Login failed - invalid credentials")
			http.Error(w, "invalid credentials", http.StatusUnauthorized)
		}
	}))

	fmt.Println("===========================================")
	fmt.Println("Zook Simple Auth Server")
	fmt.Println("Listening on :8080")
	fmt.Println("Username: Brad")
	fmt.Println("Password: 12345678")
	fmt.Println("===========================================")

	err := http.ListenAndServe(":8080", nil)
	if err != nil {
		fmt.Println("Server error:", err)
	}
}
