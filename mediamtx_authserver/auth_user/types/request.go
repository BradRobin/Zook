package types

type UserRequest struct {
	Username string   `json:"username"`
	Token    string   `json:"token"`
	Id       string   `json:"id"`
	Path     string   `json:"path"`
	Action   []string `json:"action"`
	Protocol string   `json:"protocol"`
}
