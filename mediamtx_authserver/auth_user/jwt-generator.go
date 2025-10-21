package authuser

import (
	"mediamtx_authserver/auth_user/types"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

type Myclaims struct {
	Username string   `json:"username"`
	Roles    []string `json:"username"`
	jwt.RegisteredClaims
}

func JwtGenerator(user types.UserRequest) (string, error) {
	claims := Myclaims{
		Username: user.Username,
		Roles:    user.Action,
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    "authserver",
			Subject:   user.Username,
			Audience:  jwt.ClaimStrings{"mediamtx"},
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(20 * time.Minute)),
			NotBefore: jwt.NewNumericDate(time.Now()),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)

}
