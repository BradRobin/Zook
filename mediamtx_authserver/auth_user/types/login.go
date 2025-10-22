package types

type Logindetails struct {
	Username string `json:"username"`
	Password string `json:"password"`
	Token    string `json:"token"`
}

type Gentoken struct {
	Token string `json:"token"`
}
