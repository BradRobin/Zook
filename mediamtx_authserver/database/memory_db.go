package database

import (
	"errors"
	"fmt"
	"mediamtx_authserver/auth_user/types"
	"sync"

	"golang.org/x/crypto/bcrypt"
)

// In-memory database for testing
var (
	users = make(map[string]types.Signin)
	mu    sync.RWMutex
)

// Initialize with default user
func init() {
	// Add Brad user with password 12345678
	hashedPassword, _ := bcrypt.GenerateFromPassword([]byte("12345678"), DefaultCost)
	users["Brad"] = types.Signin{
		Username: "Brad",
		Password: string(hashedPassword),
		Action:   []string{"read"},
		Protocol: []string{"webrtc"},
	}
	fmt.Println("Database initialized with user: Brad")
}

const (
	Mincost     int = 4
	Maxcost     int = 31
	DefaultCost int = 10
)

func Add_user(user types.Signin) (string, error) {
	mu.Lock()
	defer mu.Unlock()

	// Check if user already exists
	if _, exists := users[user.Username]; exists {
		return "", fmt.Errorf("user already exists")
	}

	generated, err := bcrypt.GenerateFromPassword([]byte(user.Password), DefaultCost)
	if err != nil {
		return "", types.Errorgeneratingpass
	}

	// Store user in memory
	user.Password = string(generated)
	users[user.Username] = user
	
	fmt.Printf("User %s registered successfully\n", user.Username)
	return "successfully saved user", nil
}

func Get_user(user types.Logindetails) (types.Signin, error) {
	mu.RLock()
	defer mu.RUnlock()

	found, exists := users[user.Username]
	if !exists {
		return types.Signin{}, errors.New("user not found")
	}

	err := bcrypt.CompareHashAndPassword([]byte(found.Password), []byte(user.Password))
	if err != nil {
		fmt.Println("password comparison failed:", err)
		return types.Signin{}, errors.New("invalid password")
	}

	return found, nil
}
