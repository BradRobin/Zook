package main

import (
	"encoding/json"
	"fmt"
	authuser "mediamtx_authserver/auth_user"
	"mediamtx_authserver/auth_user/types"
	"mediamtx_authserver/database"
	"net/http"
)

// CORS middleware wrapper for all requests
func corsHandler(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

func main() {
	mux := http.NewServeMux()

	// Health check endpoint
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"ok","message":"Zook Auth Server Running"}`))
	})

	// Registration endpoint
	mux.HandleFunc("/api/auth", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		var user types.Signin
		err := json.NewDecoder(r.Body).Decode(&user)
		if err != nil {
			fmt.Println("there was an error in decoding the json:", err)
			http.Error(w, "invalid json data", http.StatusBadRequest)
			return
		}

		fmt.Println("Registering user:", user.Username)
		message, err := database.Add_user(user)
		if err != nil {
			fmt.Println("there was an error adding user to the database:", err)
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Write([]byte(message))
	})

	// Login endpoint
	mux.HandleFunc("/api/login", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		var user types.Logindetails
		err := json.NewDecoder(r.Body).Decode(&user)
		if err != nil {
			fmt.Println("there was an error decoding user details:", err)
			http.Error(w, "invalid json data", http.StatusBadRequest)
			return
		}

		fmt.Printf("Login attempt for user: %s\n", user.Username)

		// Get user from database
		foundUser, err := database.Get_user(user)
		if err != nil {
			fmt.Println("user not found or password incorrect:", err)
			http.Error(w, "invalid credentials", http.StatusUnauthorized)
			return
		}

		// Save user token to cache
		err = authuser.Saveusertoken(foundUser)
		if err != nil {
			fmt.Println("error saving user token:", err)
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		fmt.Printf("User %s logged in successfully\n", user.Username)
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("successfully logged in"))
	})

	// Wrap the mux with CORS handler
	handler := corsHandler(mux)

	fmt.Println("Database initialized")
	fmt.Println("listening on port :8080")
	err := http.ListenAndServe(":8080", handler)
	if err != nil {
		fmt.Println("Server error:", err)
	}
}
