from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import Like, Subscription
import models  # Убедитесь, что импорт моделей у вас настроен так
from models import Like
from sqlalchemy import func  #  dict[int, int]:

def toggle_like(db: Session, user_id: int, task_id: int) -> dict:
    """Поставить лайк. Если лайк уже существует — убираем его (Toggle-логика)."""
    # 1. Пров
    # 
    # ряем, существует ли уже такой лайк
    existing_like = db.query(Like).filter(Like.user_id == user_id, Like.post_id == task_id).first()
    
    if existing_like:
        # Если лайк нашли — пользователь нажал кнопку второй раз, значит это АНЛАЙК
        db.delete(existing_like)
        db.commit()
        return {"status": "unliked", "message": f"Лайк с задачи {task_id} успешно убран"}
    
    # 2. Если лайка нет — создаем новый
    new_like = Like(user_id=user_id, post_id=task_id)
    try:
        db.add(new_like)
        db.commit()
        db.refresh(new_like)
        return {"status": "liked", "message": f"Задача {task_id} успешно лайкнута"}
    except IntegrityError:
        # Редкий краевой сценарий: если два запроса прилетели одновременно в один миг
        db.rollback()
        return {"status": "already_exists", "message": "Лайк уже зафиксирован в базе"}

def get_task_likes_count(db: Session, task_id: int) -> int:
    """Получить общее количество лайков под конкретной задачей."""
    return db.query(Like).filter(Like.task_id == task_id).count()
def toggle_subscription(db: Session, follower_id: int, following_id: int) -> dict:
    """Умный переключатель подписок: подписывает, если нет, и отписывает, если уже подписан."""
    # 1. Ищем, есть ли уже такая подписка в базе
    existing_sub = db.query(Subscription).filter(
        Subscription.follower_id == follower_id,
        Subscription.following_id == following_id
    ).first()

    if existing_sub:
        # Если нашли — это повторный клик, то есть ОТПИСКА
        db.delete(existing_sub)
        db.commit()
        return {"status": "unsubscribed", "message": f"Вы успешно отписались от пользователя {following_id}"}

    # 2. Если подписки нет — пытаемся подписаться
    new_sub = Subscription(follower_id=follower_id, following_id=following_id)
    try:
        db.add(new_sub)
        db.commit()
        db.refresh(new_sub)
        return {"status": "subscribed", "message": f"Вы успешно подписались на пользователя {following_id}"}
    except IntegrityError as e:
        db.rollback()
        # Сюда прилетит ошибка, если сработает наш CheckConstraint (подписка на себя) или UniqueConstraint
        return {"status": "error", "message": "Действие невозможно: дубликат или попытка подписаться на себя"}


def get_following_list(db: Session, follower_id: int):
    records = db.query(Subscription).filter(Subscription.follower_id == follower_id).all()
    return [record.following_id for record in records]

    """Пакетный подсчет лайков для списка задач (избегаем проблемы N+1)."""
    if not entity_ids:
        return {}

    # Делаем групповой запрос: SELECT post_id, COUNT(id) FROM likes WHERE post_id IN (...) GROUP BY post_id
    results = (
        db.query(Like.post_id, func.count(Like.id))
        .filter(Like.post_id.in_(entity_ids))
        .group_by(Like.post_id)
        .all()
    )

    # Превращаем результат вида [(12, 5), (15, 2)] в удобный словарь {12: 5, 15: 2}
    return {post_id: count for post_id, count in results}


