package database

import (
	"context"
	"encoding/json"
	"fmt"
	"mediamtx_authserver/auth_user/types"
	"time"

	"github.com/redis/go-redis/v9"
)

func Redisconn() redis.Client {
	rdb := redis.NewClient(&redis.Options{
		Addr:         "localhost:6379", // use default Addr
		Password:     "",               // no password set
		DB:           0,                // use default DB
		PoolSize:     10,
		MinIdleConns: 3,
	})
	pong, err := rdb.Ping(context.Background()).Result()
	fmt.Println(pong, err)
	return *rdb
}
func Redisset(token string, values interface{}) error {
	conn := Redisconn()
	data, _ := json.Marshal(values)
	status := conn.SetEx(context.Background(), token, data, 30*time.Minute)
	err := status.Err()
	if err != nil {
		return err
	}
	fmt.Printf("redis command %s", status)
	return nil
}
func RedisGet(token string) (types.Signin, error) {
	var temp types.Signin
	conn := Redisconn()
	value, status := conn.Get(context.Background(), token).Result()
	if status != nil {
		return types.Signin{}, status
	}
	json.Unmarshal([]byte(value), &temp)

	return temp, nil
}
