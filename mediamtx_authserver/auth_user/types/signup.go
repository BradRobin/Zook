package types

type Signin struct {
	Username string   `json:"username"`
	Password string   `json:"password"`
	Action   []string `json:"action"`
	Protocol []string `json:"protocol"`
}

// TODO: remember to add these to user
// Token    string   `json:"token"`
// Id       string   `json:"id"`
