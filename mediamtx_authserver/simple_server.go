package main

import (
	"fmt"
	"net/http"
)

func main() {
	mux := http.NewServeMux()
	
	// Health check endpoint
	mux.HandleFunc("GET /", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"ok","message":"Zook Auth Server Running"}`))
	})
	
	// Simple auth endpoint for testing
	mux.HandleFunc("POST /api/auth", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("successfully saved user"))
	})
	
	// Simple login endpoint for testing
	mux.HandleFunc("POST /api/login", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("successfully logged in"))
	})
	
	fmt.Println("listening on port :8080")
	err := http.ListenAndServe(":8080", mux)
	if err != nil {
		fmt.Println("Server error:", err)
	}
}
