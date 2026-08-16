from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Application(Base):
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True)
    company = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False)
    link = Column(Text, nullable=True)
    status = Column(String(50), default="Applied")
    type = Column(String(50), default="Domestic")

engine = create_engine('sqlite:///jobs.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)