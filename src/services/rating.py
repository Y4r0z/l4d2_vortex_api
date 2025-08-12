from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database import models as Models
from src.database import crud as Crud
from typing import Dict, Any, Optional, List
import datetime
from dataclasses import dataclass

@dataclass
class RatingComponent:
    points: int
    normalized_score: float

@dataclass
class PlayerRating:
    shooting_skills: RatingComponent
    game_efficiency: RatingComponent
    combat_effectiveness: RatingComponent
    experience_activity: RatingComponent
    total_points: int
    rating: float
    rating_class: str

class RatingService:
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_player_rating(self, user_id: int) -> Optional[PlayerRating]:
        seasonal_data = self._get_seasonal_performance(user_id)
        playtime_data = self._get_player_playtime_data(user_id)
        shooting_data = self._get_shooting_combat_data(user_id)
        
        if not seasonal_data and playtime_data.get('total_hours', 0) < 5:
            return None
        
        core_rating = self._calculate_core_performance(seasonal_data, playtime_data)
        shooting_rating = self._calculate_shooting_performance(shooting_data)
        experience_rating = self._calculate_experience_factor(playtime_data, seasonal_data)
        combat_rating = self._calculate_combat_performance(shooting_data, seasonal_data)
        
        total_rating = (core_rating * 0.60 + shooting_rating * 0.15 + 
                       combat_rating * 0.15 + experience_rating * 0.10)
        
        stability_modifier = self._calculate_stability_modifier(seasonal_data, playtime_data)
        final_rating = total_rating * stability_modifier
        
        shooting_points = self._rating_to_points(shooting_rating)
        efficiency_points = self._rating_to_points(core_rating)
        combat_points = self._rating_to_points(combat_rating)
        experience_points = self._rating_to_points(experience_rating)
        final_points = self._rating_to_points(final_rating)
        
        return PlayerRating(
            shooting_skills=RatingComponent(
                points=shooting_points,
                normalized_score=round(shooting_rating, 1)
            ),
            game_efficiency=RatingComponent(
                points=efficiency_points,
                normalized_score=round(core_rating, 1)
            ),
            combat_effectiveness=RatingComponent(
                points=combat_points,
                normalized_score=round(combat_rating, 1)
            ),
            experience_activity=RatingComponent(
                points=experience_points,
                normalized_score=round(experience_rating, 1)
            ),
            total_points=final_points,
            rating=round(final_rating, 1),
            rating_class=self._get_rating_class(final_rating)
        )
    
    def _calculate_core_performance(self, seasonal_data: Dict, playtime_data: Dict) -> float:
        total_hours = playtime_data.get('total_hours', 0)
        if total_hours < 1:
            return 10.0
        
        if not seasonal_data or not seasonal_data.get('seasons'):
            return 15.0
        
        seasons = seasonal_data['seasons']
        recent_seasons = seasons[-6:] if len(seasons) > 6 else seasons
        
        if not recent_seasons:
            return 15.0
        
        season_hours = []
        season_scores = []
        
        for season in recent_seasons:
            season_score = season['agression'] + season['support'] + season['perks']
            if season_score > 0:
                estimated_season_hours = total_hours / max(len(seasons), 1)
                if estimated_season_hours > 0:
                    efficiency = season_score / estimated_season_hours
                    season_hours.append(estimated_season_hours)
                    season_scores.append(efficiency)
        
        if not season_scores:
            return 20.0
        
        avg_efficiency = sum(season_scores) / len(season_scores)
        
        base_performance = min(avg_efficiency / 100 * 100, 100)
        
        consistency_factor = 1.0
        if len(season_scores) >= 3:
            score_variance = sum((score - avg_efficiency) ** 2 for score in season_scores) / len(season_scores)
            consistency_factor = max(0.7, 1.0 - (score_variance / (avg_efficiency ** 2)) * 0.5)
        
        improvement_factor = 1.0
        if len(season_scores) >= 4:
            recent_avg = sum(season_scores[-2:]) / 2
            early_avg = sum(season_scores[:2]) / 2
            if early_avg > 0:
                improvement_ratio = recent_avg / early_avg
                improvement_factor = min(1.2, max(0.8, improvement_ratio))
        
        final_score = base_performance * consistency_factor * improvement_factor
        return min(final_score, 100)
    
    def _calculate_shooting_performance(self, shooting_data: Dict) -> float:
        if not shooting_data or shooting_data.get('total_shots', 0) < 500:
            return 40.0
        
        accuracy = shooting_data.get('accuracy', 0)
        headshot_ratio = shooting_data.get('headshot_ratio', 0)
        damage_efficiency = shooting_data.get('damage_efficiency', 0)
        
        accuracy_score = min(accuracy / 0.5 * 100, 100)
        headshot_score = min(headshot_ratio / 0.2 * 100, 100)
        damage_score = min(damage_efficiency / 30 * 100, 100)
        
        return (accuracy_score * 0.4 + headshot_score * 0.35 + damage_score * 0.25)
    
    def _calculate_combat_performance(self, shooting_data: Dict, seasonal_data: Dict) -> float:
        base_score = 45.0
        
        if shooting_data and shooting_data.get('total_shots', 0) >= 100:
            kd_factor = shooting_data.get('kill_death_ratio', 1.0)
            special_kills_ratio = shooting_data.get('special_kills_ratio', 0.1)
            
            kd_score = min(kd_factor / 2.5 * 100, 100)
            special_score = min(special_kills_ratio / 0.4 * 100, 100)
            
            base_score = (kd_score * 0.6 + special_score * 0.4)
        
        if seasonal_data and seasonal_data.get('seasons'):
            recent_seasons = seasonal_data['seasons'][-3:]
            agression_scores = [s['agression'] for s in recent_seasons if s['agression'] > 0]
            
            if agression_scores:
                avg_agression = sum(agression_scores) / len(agression_scores)
                agression_bonus = min(avg_agression / 1000 * 20, 25)
                base_score = min(base_score + agression_bonus, 100)
        
        return base_score
    
    def _calculate_experience_factor(self, playtime_data: Dict, seasonal_data: Dict) -> float:
        total_hours = playtime_data.get('total_hours', 0)
        monthly_hours = playtime_data.get('monthly_hours', 0)
        
        if total_hours < 1:
            return 5.0
        
        experience_base = min(total_hours / 300 * 70, 70)
        
        activity_factor = 1.0
        if total_hours > 10:
            expected_monthly = total_hours / 12
            if expected_monthly > 0:
                activity_ratio = monthly_hours / expected_monthly
                if activity_ratio < 0.3:
                    activity_factor = 0.6
                elif activity_ratio > 2.0:
                    activity_factor = 1.1
        
        seasons_count = len(seasonal_data.get('seasons', [])) if seasonal_data else 0
        participation_score = min(seasons_count / 6 * 30, 30)
        
        return min((experience_base + participation_score) * activity_factor, 100)
    
    def _calculate_stability_modifier(self, seasonal_data: Dict, playtime_data: Dict) -> float:
        modifier = 1.0
        
        total_hours = playtime_data.get('total_hours', 0)
        if total_hours < 10:
            modifier *= 0.8
        elif total_hours > 200:
            modifier *= 1.05
        
        if seasonal_data and len(seasonal_data.get('seasons', [])) >= 3:
            seasons = seasonal_data['seasons']
            recent_performance = sum(s['agression'] + s['support'] + s['perks'] for s in seasons[-2:]) / 2
            overall_performance = sum(s['agression'] + s['support'] + s['perks'] for s in seasons) / len(seasons)
            
            if overall_performance > 0:
                stability_ratio = recent_performance / overall_performance
                if 0.8 <= stability_ratio <= 1.2:
                    modifier *= 1.1
                elif stability_ratio < 0.5 or stability_ratio > 2.0:
                    modifier *= 0.9
        
        monthly_hours = playtime_data.get('monthly_hours', 0)
        if monthly_hours < 2:
            modifier *= 0.85
        
        return max(modifier, 0.7)
    
    def _get_seasonal_performance(self, user_id: int) -> Dict:
        seasons_query = self.db.query(Models.ScoreSeason).filter(
            Models.ScoreSeason.userId == user_id
        ).order_by(Models.ScoreSeason.date).all()
        
        if not seasons_query:
            return {}
        
        seasons_data = []
        for season in seasons_query:
            seasons_data.append({
                'agression': season.agression,
                'support': season.support,
                'perks': season.perks,
                'date': season.date
            })
        
        return {'seasons': seasons_data}
    
    def _get_shooting_combat_data(self, user_id: int) -> Dict:
        shots = Crud.get_player_shots(self.db, user_id)
        hits = Crud.get_player_hits(self.db, user_id)
        kills = Crud.get_player_kills(self.db, user_id)
        
        if not shots or shots.player_fire < 100:
            return {}
        
        accuracy = shots.player_hits / shots.player_fire if shots.player_fire > 0 else 0
        
        total_hits = (hits.HEAD + hits.CHEST + hits.STOMACH + hits.LEFT_ARM + 
                     hits.RIGHT_ARM + hits.LEFT_LEG + hits.RIGHT_LEG) if hits else 0
        headshot_ratio = hits.HEAD / total_hits if total_hits > 0 else 0
        
        damage_efficiency = shots.player_damage / shots.player_fire if shots.player_fire > 0 else 0
        
        total_kills = (kills.infected_killed + kills.smoker_killed + kills.boomer_killed + 
                      kills.hunter_killed + kills.spitter_killed + kills.jockey_killed + 
                      kills.charger_killed + kills.witch_killed + kills.tank_killed) if kills else 0
        
        kd_ratio = total_kills / shots.player_death if shots.player_death > 0 else total_kills
        
        special_kills = (kills.smoker_killed + kills.boomer_killed + kills.hunter_killed + 
                        kills.spitter_killed + kills.jockey_killed + kills.charger_killed + 
                        kills.witch_killed + kills.tank_killed) if kills else 0
        special_ratio = special_kills / kills.infected_killed if kills and kills.infected_killed > 0 else 0
        
        return {
            'total_shots': shots.player_fire,
            'accuracy': accuracy,
            'headshot_ratio': headshot_ratio,
            'damage_efficiency': damage_efficiency,
            'kill_death_ratio': kd_ratio,
            'special_kills_ratio': special_ratio
        }
    
    def _get_player_playtime_data(self, user_id: int) -> Dict:
        sessions = self.db.query(Models.PlaySession).filter(
            Models.PlaySession.userId == user_id,
            Models.PlaySession.timeTo.isnot(None)
        ).all()
        
        total_seconds = 0
        monthly_seconds = 0
        one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        
        for session in sessions:
            if session.timeTo and session.timeFrom:
                duration = session.timeTo - session.timeFrom
                session_seconds = int(duration.total_seconds())
                total_seconds += session_seconds
                
                if session.timeFrom >= one_month_ago:
                    monthly_seconds += session_seconds
        
        return {
            'total_hours': total_seconds / 3600,
            'monthly_hours': monthly_seconds / 3600
        }
    
    def _rating_to_points(self, rating: float) -> int:
        if rating >= 90:
            return int(4500 + (rating - 90) * 150)
        elif rating >= 80:
            return int(3200 + (rating - 80) * 130)
        elif rating >= 70:
            return int(2200 + (rating - 70) * 100)
        elif rating >= 60:
            return int(1400 + (rating - 60) * 80)
        elif rating >= 45:
            return int(800 + (rating - 45) * 40)
        else:
            return int(200 + rating * 13)
    
    def _get_rating_class(self, rating: float) -> str:
        if rating >= 100:
            return "Элита VI"
        elif rating >= 90:
            return "Эксперт V"
        elif rating >= 70:
            return "Опытный IV"
        elif rating >= 60:
            return "Сильный III"
        elif rating >= 50:
            return "Средний II"
        else:
            return "Новичок I"