package database

import (
	"context"
	"errors"
	"fmt"
	"mediamtx_authserver/auth_user/types"
	"time"

	"github.com/jackc/pgx/v5"
	"golang.org/x/crypto/bcrypt"
)

func connectionpool() (*pgx.Conn, error) {
	db_url := "postgres://deeznutz:0000@localhost:5433/postgres"

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	conn, err := pgx.Connect(ctx, db_url)
	if err != nil {
		return nil, err
	}
	return conn, nil
}

const (
	Mincost     int = 4
	Maxcost     int = 31
	DefaultCost int = 10
)

func Add_user(user types.Signin) (string, error) {
	conn, err := connectionpool()
	if err != nil {
		return "", fmt.Errorf("Add user error: %w", err)
	}

	generated, err := bcrypt.GenerateFromPassword([]byte(user.Password), DefaultCost)
	if err != nil {
		return "", types.Errorgeneratingpass
	}
	details := []interface{}{user.Username, generated, user.Action, user.Protocol}
	fmt.Println(details[0])
	_, err2 := conn.Exec(context.Background(), "insert into streaming.users(username,password,action,protocol) values ($1,$2,$3,$4)", details...)
	if err2 != nil {
		fmt.Println(err2)
		return "", types.Savingusererror
	}
	return "successfully saved user", nil
}
func Get_user(user types.Logindetails) (types.Signin, error) {
	conn, err := connectionpool()
	if err != nil {
		return types.Signin{}, fmt.Errorf("There was a server connection %s", user.Username)
	}
	var found types.Signin
	query := conn.QueryRow(context.Background(), "select * from streaming.users where username=$1", user.Username)
	err2 := query.Scan(&found)
	if err2 != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return types.Signin{}, err2
		} else {
			fmt.Println("error in scanning rows, %w", err2)
			return types.Signin{}, err2
		}
	}

	err4 := bcrypt.CompareHashAndPassword([]byte(found.Password), []byte(user.Password))
	if err4 != nil {
		fmt.Println("there was an error in encrypting the password")
		return types.Signin{}, err4
	} else {
		return found, nil
	}
}
