from .random import Random
from .recommender import Recommender

import random

from .sticky_artist import StickyArtist


class Custom(Recommender):
    def __init__(self, tracks_redis_connection, artist_redis_connection, catalog, data_logger):
        self.tracks_redis = tracks_redis_connection
        self.fallback = StickyArtist(tracks_redis_connection, artist_redis_connection, catalog)
        self.catalog = catalog
        self.data_logger = data_logger
        self.threshold = 0.85

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        previous_track = self.tracks_redis.get(prev_track)

        if previous_track is not None:
            self.track_user_info(prev_track, prev_track_time, user)

        self.catalog.app.logger.info(
            f"Check {user} for pop {self.catalog.user_listened_tracks_amount[user]} {prev_track_time}"
        )
        if previous_track is None or (
                (self.catalog.user_listened_tracks_amount[user] % 4 == 0) and (prev_track_time < self.threshold)):

            recommendations = self.get_recs_from_highly_rated(set(), user)

            track = set(self.catalog.top_tracks[:1000]).intersection(recommendations)

            if track:
                self.catalog.app.logger.info("Recommending from top 100 tracks")
                return self.get_random(track)

        recommendations = self.get_recs_with_removed_listened(previous_track, user)

        if not recommendations or prev_track_time < self.threshold:
            recommendations = self.get_recs_from_highly_rated(recommendations, user)

        return self.get_random(recommendations)

    def get_recs_from_highly_rated(self, recommendations, user):
        if user in self.catalog.user_highly_rated:
            self.catalog.app.logger.info("Making recs from highly rated tracks")

            higly_reated_track_id = random.choice(list(self.catalog.user_highly_rated[user]))
            higly_reated_track = self.tracks_redis.get(higly_reated_track_id)
            recommendations = self.get_recs_with_removed_listened(higly_reated_track, user)

        return recommendations

    @staticmethod
    def get_random(recommendations):
        shuffled = list(recommendations)
        random.shuffle(shuffled)
        return shuffled[0]

    def get_recs_with_removed_listened(self, previous_track, user):
        previous_track = self.catalog.from_bytes(previous_track)
        return self.remove_listened(previous_track.recommendations, user)

    def track_user_info(self, prev_track, prev_track_time, user):
        if prev_track_time > self.threshold:
            # self.catalog.app.logger.info(f"User {user} listened track {prev_track} with {prev_track_time}")
            self.catalog.user_highly_rated.setdefault(user, set()).add(prev_track)

        self.catalog.user_history.setdefault(user, set()).add(prev_track)
        counter = self.catalog.user_listened_tracks_amount.setdefault(user, 0)
        self.catalog.user_listened_tracks_amount[user] = counter + 1

    def remove_listened(self, recommendations, user):
        return [track for track in recommendations if track not in self.catalog.user_history[user]]
