package types

import "errors"

var (
	Decodingusererror         = errors.New("There was an error decoding user values")
	Dbconnectionerror         = errors.New("Error in connecting to the database")
	Hashtooshort              = errors.New("the password is too short")
	Mismatchedhashandpassword = errors.New("incorrect password")
	Hashtoolong               = errors.New("the password is too long")
	Errorgeneratingpass       = errors.New("ther was an in issue in saving your password")
	Savingusererror           = errors.New("There was an error saving user")
)
