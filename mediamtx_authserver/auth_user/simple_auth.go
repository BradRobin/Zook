package authuser

import (
	"fmt"
	"mediamtx_authserver/auth_user/types"
)

// Simplified version without Redis/JWT for testing
func Saveusertoken(request types.Signin) error {
	fmt.Printf("User %s token saved (simplified)\n", request.Username)
	return nil
}

func Getuserdetails(token string) (types.Signin, error) {
	return types.Signin{}, fmt.Errorf("token not found")
}

