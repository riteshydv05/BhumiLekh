from app.db.session import Base, engine
from app.models.document import Document


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


if __name__ == "__main__":
    init_db()
