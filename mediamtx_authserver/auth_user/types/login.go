package types

type Logindetails struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

type Gentoken struct {
	Token string `json:"token"`
}
