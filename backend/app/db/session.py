
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

if engine.dialect.name == "sqlite":
    import sqlite3
    from sqlalchemy import event

    def _geom_from_ewkt_stub(val):
        if not val:
            return None
        try:
            import shapely.wkt
            import shapely.wkb
            s = str(val)
            if ";" in s:
                s = s.split(";", 1)[1]
            geom = shapely.wkt.loads(s)
            return shapely.wkb.dumps(geom)
        except Exception:
            return None

    @event.listens_for(engine, "connect")
    def _set_sqlite_spatialite_stubs(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            dbapi_connection.create_function("RecoverGeometryColumn", 5, lambda *args: 1)
            dbapi_connection.create_function("CreateSpatialIndex", 2, lambda *args: 1)
            dbapi_connection.create_function("DisableSpatialIndex", 2, lambda *args: 1)
            dbapi_connection.create_function("DiscardGeometryColumn", 2, lambda *args: 1)
            dbapi_connection.create_function("GeomFromEWKT", 1, _geom_from_ewkt_stub)
            dbapi_connection.create_function("GeomFromText", -1, lambda *args: _geom_from_ewkt_stub(args[0]) if args else None)
            dbapi_connection.create_function("AsGeoJSON", -1, lambda *args: "{}")
            dbapi_connection.create_function("AsEWKT", 1, lambda x: str(x) if x else None)
            dbapi_connection.create_function("AsEWKB", 1, lambda x: x)
            dbapi_connection.create_function("AsText", 1, lambda x: str(x) if x else None)
            dbapi_connection.create_function("AsBinary", 1, lambda x: x)



SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
