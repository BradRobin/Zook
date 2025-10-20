package database

import (
	"context"
	"fmt"
	"github.com/jackc/pgx/v5"
	"golang.org/x/crypto/bcrypt"
	"mediamtx_authserver/auth_user/types"
	"time"
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

func Add_user(user types.Auth_details) (string, error) {
	conn, err := connectionpool()
	if err != nil {
		return "", fmt.Errorf("Add user error: %w", err)
	}
	const (
		Mincost     int = 4
		Maxcost     int = 31
		DefaultCost int = 10
	)
	generated, err := bcrypt.GenerateFromPassword([]byte(user.Password), DefaultCost)
	if err != nil {
		return "", types.Errorgeneratingpass
	}
	details := []interface{}{user.Username, generated, user.Action, user.Protocol}
	_, err2 := conn.Exec(context.Background(), "insert into streaming(username,password,action,protocol) values ()", details...)
	if err2 != nil {
		return "", types.Savingusererror
	}
	return "successfully saved user", nil
}
