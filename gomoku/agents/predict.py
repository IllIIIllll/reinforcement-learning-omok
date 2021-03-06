# © 2020 지성. all rights reserved.
# <llllllllll@kakao.com>
# Apache License 2.0

import numpy as np

from gomoku.agents.base import Agent
from gomoku import encoders
from gomoku import board
from gomoku import kerasutil

# 에이전트 초기화
class DeepLearningAgent(Agent):
    def __init__(self, model, encoder):
        Agent.__init__(self)
        self.model = model
        self.encoder = encoder

    # 수 확률 예측
    def predict(self, game_state):
        encoded_state = self.encoder.encode(game_state)
        input_tensor = np.array([encoded_state])
        return self.model.predict(input_tensor)[0]

    def select_move(self, game_state):
        num_moves = self.encoder.board_width * self.encoder.board_height
        move_probs = self.predict(game_state)
        # 확률이 가장 높은 수와 가장 낮은 수의 차이 증가
        move_probs = move_probs ** 3
        eps = 1e-6
        # 예측값이 0 또는 1에 가까워지는 것 방지
        move_probs = np.clip(move_probs, eps, 1 - eps)
        # 다른 확률 분포 생성을 위한 재 정규화
        move_probs = move_probs / np.sum(move_probs)
        # 각 수별 확률을 이용하여 순위가 매겨진 수 리스트 생성
        candidates = np.arange(num_moves)
        ranked_moves = np.random.choice(
            candidates,
            num_moves,
            replace=False,
            p=move_probs
        )

        for point_idx in ranked_moves:
            point = self.encoder.decode_point_index(point_idx)
            if game_state.is_valid_move(board.Move.play(point)):
                return board.Move.play(point)

    # 에이전트 직렬화
    def serialize(self, h5file):
        h5file.create_group('encoder')
        h5file['encoder'].attrs['name'] = self.encoder.name()
        h5file['encoder'].attrs['board_width'] = self.encoder.board_width
        h5file['encoder'].attrs['board_height'] = self.encoder.board_height
        h5file.create_group('model')
        kerasutil.save_model_to_hdf5_group(self.model, h5file['model'])

# HDF5 파일에서 DeepLearningAgent 역직렬화
def load_prediction_agent(h5file):
    model = kerasutil.load_model_from_hdf5_group(h5file['model'])
    encoder_name = h5file['encoder'].attrs['name']
    if not isinstance(encoder_name, str):
        encoder_name = encoder_name.decode('ascii')
    board_width = h5file['encoder'].attrs['board_width']
    board_height = h5file['encoder'].attrs['board_height']
    encoder = encoders.get_encoder_by_name(
        encoder_name, (board_width, board_height)
    )
    return DeepLearningAgent(model, encoder)