# MQTT_ant_scale

MQTT client to read and broadcast values from ANT compatible scale.

Based on code from https://johannesbader.ch/blog/track-your-heartrate-on-raspberry-pi-with-ant/

Uses python-ant from https://github.com/baderj/python-ant as suggested in the original source (USB fixes for supporting Suunto Movestick Mini)

There is nothing special in the handlng of the connection - open a channel, search with infinite timeout - after the scale has finished 
communicating and disconnects, the ANT device automatically goes back into search mode.
