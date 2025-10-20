package main

import (
	"encoding/json"
	"fmt"
	"log"
	"mediamtx_authserver/auth_user/types"
	"mediamtx_authserver/database"
	"net/http"
)

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/api/auth",
		func(
			resp http.ResponseWriter,
			req *http.Request,
		) {
			resp.Header().Set("Content-Type", "application/json")
			var user types.Auth_details
			err := json.NewDecoder(req.Body).Decode(&user)
			if err != nil {
				log.Fatalf("there was an error in decoding the json %w", err)
				resp.WriteHeader(http.StatusInternalServerError)
				return
			}
			message, err := database.Add_user(user)
			if err != nil {
				log.Fatalf("there was an adding user to the database %w", err)
				resp.Write([]byte(err.Error()))
			}
			resp.Write([]byte(message))

		})
	fmt.Println("listening on port :8080")
	http.ListenAndServe("8080", mux)
}
