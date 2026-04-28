from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Detection(db.Model):
    __tablename__ = 'detections'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    source: Mapped[str] = mapped_column(db.String(50))  # 'image', 'video', 'webcam'
    class_id: Mapped[int] = mapped_column(db.Integer)
    class_name: Mapped[str] = mapped_column(db.String(100))
    confidence: Mapped[float] = mapped_column(db.Float)
    image_path: Mapped[str] = mapped_column(db.String(255), nullable=True)
    session_id: Mapped[str] = mapped_column(db.String(100), nullable=True)
    processing_time_ms: Mapped[float] = mapped_column(db.Float, default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": round(self.confidence, 4),
            "image_path": self.image_path,
            "processing_time_ms": round(self.processing_time_ms, 2)
        }

class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    level: Mapped[str] = mapped_column(db.String(10))  # INFO, WARNING, ERROR
    message: Mapped[str] = mapped_column(db.Text)
    route: Mapped[str] = mapped_column(db.String(100), nullable=True)

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()

def add_detection(source, class_id, class_name, confidence, image_path=None, session_id=None, processing_time_ms=0.0):
    new_detection = Detection(
        source=source,
        class_id=class_id,
        class_name=class_name,
        confidence=confidence,
        image_path=image_path,
        session_id=session_id,
        processing_time_ms=processing_time_ms
    )
    db.session.add(new_detection)
    db.session.commit()
    return new_detection

def add_log(level, message, route=None):
    new_log = SystemLog(level=level, message=message, route=route)
    db.session.add(new_log)
    db.session.commit()
