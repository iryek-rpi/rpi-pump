#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" 
Publish some messages to queue
"""
import paho.mqtt.publish as publish

msgs = [{
    'topic': "kids/yolo",
    'payload': "jump"
}, {
    'topic': "adult/pics",
    'payload': "some photo"
}, {
    'topic': "adult/news",
    'payload': "extra extra"
}, {
    'topic': "adult/news",
    'payload': "super extra"
}]

#host = "X230T.local"
host = "192.168.0.2"

if __name__ == '__main__':
  # publish a single message
  publish.single(topic="kids/yolo", payload="just do it", hostname=host)

  # publish multiple messages
  publish.multiple(msgs, hostname=host)

  publish.single(topic="pump", payload=123.75, hostname=host)

# vi: set fileencoding=utf-8 :