package main

import (
	"encoding/json"
	"fmt"
	authuser "mediamtx_authserver/auth_user"
	"mediamtx_authserver/auth_user/types"
	"mediamtx_authserver/database"
	"net/http"

	"golang.org/x/crypto/bcrypt"
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
				return
			}
			check, err := authuser.Getuserdetails(user.Token)
			if err != nil {
				message, err := database.Get_user(user)
				if err != nil {
					w.Write([]byte(err.Error()))
					return
				}
				err3 := authuser.Saveusertoken(message)
				if err3 != nil {
					w.WriteHeader(http.StatusInternalServerError)
					w.Write([]byte("There was an internal server error"))
				}

				_, err2 := w.Write([]byte("successfully logged in"))
				if err2 != nil {
					fmt.Println("there was an error writing response ", err2)
					w.WriteHeader(http.StatusInternalServerError)
				}
			}
			err4 := bcrypt.CompareHashAndPassword([]byte(check.Password), []byte(user.Password))
			if err4 != nil {
				fmt.Println("there was an error confirming the password from cache/redis", err4)
				w.WriteHeader(http.StatusInternalServerError)
			}
			w.Write([]byte("You have logged in successfully"))
		})
	fmt.Println("listening on port :8080")
	err := http.ListenAndServe(":8080", mux)
	if err != nil {
		fmt.Println(err)
	}
}
