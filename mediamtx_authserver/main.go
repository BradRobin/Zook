package main

import (
	"encoding/json"
	"fmt"
	"mediamtx_authserver/auth_user/types"
	"mediamtx_authserver/database"
	"net/http"
)

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("POST /api/auth",
		func(
			resp http.ResponseWriter,
			req *http.Request,
		) {
			resp.Header().Set("Content-Type", "application/json")
			var user types.Signin
			err := json.NewDecoder(req.Body).Decode(&user)
			if err != nil {
				fmt.Println("there was an error in decoding the json %w", err)
				resp.WriteHeader(http.StatusInternalServerError)
				return
			}
			fmt.Println(user.Username)
			message, err := database.Add_user(user)
			if err != nil {
				fmt.Println("there was an adding user to the database %w", err)
				resp.Write([]byte(err.Error()))
			}
			resp.Write([]byte(message))

		})
	mux.HandleFunc("POST /api/login",
		func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			var user types.Logindetails
			err := json.NewDecoder(r.Body).Decode(&user)
			if err != nil {
				fmt.Println("there was an error decoding you user details")
				http.Error(w, "invalid json data", http.StatusBadRequest)
			}
			message, err := database.Get_user(user)
			if err != nil {
				w.Write([]byte(err.Error()))
				return
			}
			_, err2 := w.Write([]byte(message))
			if err2 != nil {
				fmt.Println(err2)
			}

		})
	fmt.Println("listening on port :8080")
	err := http.ListenAndServe(":8080", mux)
	if err != nil {
		fmt.Println(err)
	}
}
