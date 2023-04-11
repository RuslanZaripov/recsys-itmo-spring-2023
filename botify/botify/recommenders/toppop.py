import random
from typing import List

from .random import Random
from .recommender import Recommender


class TopPop(Recommender):
    def __init__(self, tracks_redis, top_tracks: List[int], catalog):
        self.random = Random(tracks_redis)
        self.top_tracks = top_tracks
        self.catalog = catalog

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        if self.top_tracks:
            shuffled = list(self.top_tracks)
            random.shuffle(shuffled)

            self.catalog.app.logger.info(f"Recommending from top 100 tracks {shuffled[0]}")

            return shuffled[0]

        return self.random.recommend_next(user, prev_track, prev_track_time)
