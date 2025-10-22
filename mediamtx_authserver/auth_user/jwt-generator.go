package authuser

import (
	"fmt"
	"mediamtx_authserver/auth_user/types"
	"mediamtx_authserver/database"
	"os"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

type Myclaims struct {
	Username string   `json:"username"`
	Roles    []string `json:"roles"`
	jwt.RegisteredClaims
}

func JwtGenerator(username string) (string, error) {
	claims := Myclaims{
		Username: username,
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    "authserver",
			Subject:   username,
			Audience:  jwt.ClaimStrings{"mediamtx"},
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(20 * time.Minute)),
			NotBefore: jwt.NewNumericDate(time.Now()),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	privatekey, _ := os.ReadDir("../keys/private.key")
	signedtoken, err := token.SignedString(privatekey)
	if err != nil {
		fmt.Println(types.Errorsigningtoken)
		return "", types.Errorsigningtoken
	}
	return signedtoken, nil
}

// this is for when we want to save a logged in user
func Saveusertoken(request types.Signin) error {
	token, err := JwtGenerator(request.Username)
	if err != nil {
		fmt.Println("This error is in saveusertoken jwtgen", err)
		return types.Errorsigningtoken
	}
	values := []interface{}{request.Username, request.Id, request.Action, request.Protocol, request.Password}
	err2 := database.Redisset(token, values)
	if err2 != nil {
		fmt.Println("there was a problem in saveusertoken redisset", err)
		return types.Errorredisstore
	}
	return nil
}
func Getuserdetails(token string) (types.Signin, error) {
	value, err := database.RedisGet(token)
	if err != nil {
		return types.Signin{}, err
	}
	return value, nil

}
