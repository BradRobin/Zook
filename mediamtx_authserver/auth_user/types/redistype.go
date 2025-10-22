package types

// this is the data type to store in redis with the token as key
type Redisstoretype struct {
	Username string   `json:"username"`
	Id       string   `json:"userid"`
	Action   []string `json:"action"`
	Protocol []string `json:"protocol"`
	Path     []string `json:"path"`
}
