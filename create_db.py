import sqlalchemy
from sqlalchemy.orm import sessionmaker
import os
from models import create_tables, Words
from dotenv import load_dotenv

load_dotenv()

def create_db():
    DNS = os.getenv('DNS')
    engine = sqlalchemy.create_engine(DNS)
    Session = sessionmaker(bind=engine)
    session = Session()
    words_data = [
        ('green', 'зелёный'),
        ('blue', 'голубой'),
        ('brown', 'коричневый'),
        ('black', 'чёрный'),
        ('yellow', 'жёлтый'),
        ('she', 'она'),
        ('he', 'он'),
        ('dog', 'собака'),
        ('cat', 'кошка'),
        ('sky', 'небо'),
        ('table', 'стол'),
        ('flower', 'цветок'),
        ('house', 'дом'),
        ('road', 'дорога'),
        ('door', 'дверь'),
        ('window', 'окно'),
        ('world', 'мир'),
        ('mouse', 'мышь'),
        ('winter', 'зима'),
        ('sun', 'солнце'),
        ('step', 'шаг'),
        ('cup', 'чашка'),
        ('wild', 'дикий'),
        ('mistake', 'ошибка'),
        ('mirror', 'зеркало'),
        ('song', 'песня'),
        ('tiger', 'тигр'),
        ('light', 'свет'),
        ('gray', 'серый'),
        ('rose', 'роза'),
        ('building', 'здание'),
        ('office', 'офис'),
        ('way', 'путь'),
        ('strip', 'полоса'),
        ('slide', 'скользить'),
        ('tea', 'чай'),
        ('sea', 'море'),
        ('bus', 'автобус'),
        ('memory', 'память'),
        ('time', 'время'),
        ('chair', 'стул'),
        ('floor', 'пол'),
        ('seal', 'печать'),
        ('ceiling', 'потолок'),
        ('wall', 'стена'),
        ('phone', 'телефон'),
        ('roof', 'крыша'),
        ('they', 'они'),
        ('it', 'это'),
        ('we', 'мы'),
        ('can', 'мочь'),
        ('you', 'ты'),
        ('her', 'eё'),
        ('your', 'твоё'),
        ('me', 'мне'),
        ('their', 'их'),
        ('his', 'его')
    ]

    create_tables(engine)

    for word, translate in words_data:
        words = Words(word=word, translate=translate)
        session.add(words)
        session.commit()


    session.close()



