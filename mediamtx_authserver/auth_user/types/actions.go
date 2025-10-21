package types

type action string

const (
	Publishaction  action = "publish"
	Readaction     action = "read"
	Playbackaction action = "playback"
	Apiaction      action = "api"
	Metricsaction  action = "metrics"
	Pprofaction    action = "pprof"
)
