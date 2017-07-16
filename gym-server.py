#!/usr/bin/env python3
import os
import socket

import gym

import gym_pb2


class Environment:
    def __init__(self, conn):
        self.env = gym.make('CartPole-v0')
        self.conn = conn

    def _recv_message(self, cls):
        message_pb_len = int.from_bytes(self.conn.recv(1), byteorder='little')
        message_pb = self.conn.recv(message_pb_len)
        message = cls()
        message.ParseFromString(message_pb)
        return message

    def _send_message(self, message):
        message_pb = message.SerializeToString()
        self.conn.sendall(len(message_pb).to_bytes(1, byteorder='little'))
        self.conn.sendall(message_pb)

    def run(self):
        while True:
            request = self._recv_message(gym_pb2.Request)
            if request.type == gym_pb2.Request.DONE: break
            elif request.type == gym_pb2.Request.RESET: self.reset()
            elif request.type == gym_pb2.Request.STEP: self.step()

    def reset(self):
        observation = self.env.reset()
        self._send_message(gym_pb2.State(observation=observation, reward=0.0, done=False))

    def step(self):
        action = self._recv_message(gym_pb2.Action)
        observation, reward, done, _ = self.env.step(action.value)
        self._send_message(gym_pb2.State(observation=observation, reward=reward, done=done))


if __name__ == '__main__':
    socket_filepath = '/tmp/gym-server-socket'
    try:
        os.remove(socket_filepath)
    except FileNotFoundError:
        pass

    socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    socket.bind(socket_filepath)
    socket.listen()

    while True:
        try:
            conn, _ = socket.accept()
            env = Environment(conn)
            env.run()
        except BrokenPipeError:
            pass
        finally:
            del env
