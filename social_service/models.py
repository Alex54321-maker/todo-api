from sqlalchemy import Column, Integer, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# 1. Твоя модель Лайков
class Like(Base):
    __tablename__ = "likes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    post_id = Column(Integer, nullable=False)

# 2. Модель Подписок (из кодового письма №16)
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, nullable=False)
    following_id = Column(Integer, nullable=False)

    __table_args__ = (
        # Защита на уровне БД: уникальная пара (нельзя подписаться дважды)
        UniqueConstraint("follower_id", "following_id", name="uq_follower_following"),
        # Защита на уровне БД: запрет подписки на самого себя
        CheckConstraint("follower_id != following_id", name="check_self_subscription"),
    )
