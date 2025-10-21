a client opens ups the browser(streamer) we fetch or basically send to a url like http://localhost:8889/mystream/publish

then i setup the server for mediamtx 

user flow
user first signs (username,password,action,(decided by the device they use)) returning a token
then decide what the next action is, is it watching (token,id,path,action,protocol)
they then hit up mediamtx server which call the auth server to check if the user has logged in 
start streaming 

user login(username,password)
then decide what the next action is, is it watching (token,id,path,action,protocol)
they then hit up mediamtx server which call the auth server to check if the user has logged in 
start streaming 