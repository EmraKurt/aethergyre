import ijson
import uuid
import datetime
import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.core.config import settings
# Database Configuration
# REPLACE WITH YOUR ACTUAL DATABASE URL



# Assuming your models are in 'card.py'
from app.db.models import  OracleCard, Expansion, Card, CardImage

# --- CONFIGURATION ---
DATABASE_URL = settings.DATABASE_URL
JSON_FILE = r"C:\Users\hogen\Downloads\default-cards.json"

# We use a very conservative limit to ensure it works on all environments
MAX_PARAMS_PER_QUERY = 1000 
INTERNAL_BATCH_SIZE = 100 # How many cards to hold in RAM before sending to DB

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def parse_date(date_str):
    if not date_str: return None
    try: return datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except: return None

def upsert_rows(session, model, rows):
    """
    Inserts rows into the DB using small chunks to avoid parameter limits.
    """
    if not rows:
        return

    num_columns = len(rows[0].keys())
    # Calculate how many rows we can fit in one query without hitting MAX_PARAMS
    chunk_size = max(1, MAX_PARAMS_PER_QUERY // num_columns)
    
    table = model.__table__
    
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i : i + chunk_size]
        
        # Build the INSERT ... ON CONFLICT DO NOTHING statement
        stmt = pg_insert(table).values(chunk)
        
        # Use the Primary Key for conflict detection
        # For Expansion/Card it's 'id', for OracleCard it's 'oracle_id'
        pk_column = "oracle_id" if model == OracleCard else "id"
        
        on_conflict_stmt = stmt.on_conflict_do_nothing(index_elements=[pk_column])
        session.execute(on_conflict_stmt)

def flush_all(session, sets, oracles, cards, images):
    try:
        if sets:
            upsert_rows(session, Expansion, sets)
            sets.clear()
        
        if oracles:
            upsert_rows(session, OracleCard, oracles)
            oracles.clear()
            
        if cards:
            upsert_rows(session, Card, cards)
            cards.clear()
            
        if images:
            # Images don't have a PK in your model, so we use bulk_insert_mappings
            # in very small chunks.
            for i in range(0, len(images), 100):
                session.bulk_insert_mappings(CardImage, images[i : i + 100])
            images.clear()
            
        session.commit()
    except Exception:
        session.rollback()
        raise

def run_ingest():
    session = SessionLocal()
    
    # Track what we've seen in this session to avoid redundant processing
    seen_oracles = set()
    seen_sets = set()
    
    # Optional: Pre-load existing IDs if you want to skip what's already in DB
    # seen_oracles.update(r[0] for r in session.query(OracleCard.oracle_id).all())
    # seen_sets.update(r[0] for r in session.query(Expansion.id).all())

    set_buffer, oracle_buffer, card_buffer, image_buffer = [], [], [], []
    count = 0

    print(f"Opening {JSON_FILE}...")
    try:
        with open(JSON_FILE, 'rb') as f:
            # 'item' is the prefix for objects in the main array
            objects = ijson.items(f, 'item')
            
            for item in objects:
                # Essential IDs
                s_id = item.get('set_id')
                o_id = item.get('oracle_id')
                c_id = item.get('id')
                
                if not all([s_id, o_id, c_id]):
                    continue

                # 1. Set / Expansion
                if s_id not in seen_sets:
                    set_buffer.append({
                        "id": uuid.UUID(s_id),
                        "code": item.get('set'),
                        "name": item.get('set_name'),
                        "card_count": item.get('card_count', 0),
                        "released_at": parse_date(item.get('released_at')),
                        "set_type": item.get('set_type'),
                        "icon": item.get('icon_svg_uri')
                    })
                    seen_sets.add(s_id)

                # 2. Oracle Card
                if o_id not in seen_oracles:
                    oracle_buffer.append({
                        "oracle_id": uuid.UUID(o_id),
                        "name": item.get('name'),
                        "oracle_text": item.get('oracle_text'),
                        "type_line": item.get('type_line'),
                        "power": item.get('power'),
                        "toughness": item.get('toughness'),
                        "color": item.get('colors', []),
                        "cmc": float(item.get('cmc', 0)) if item.get('cmc') is not None else 0.0,
                        "mana_cost": item.get('mana_cost'),
                        "produced_mana": item.get('produced_mana', []),
                        "keywords": item.get('keywords', []),
                        "color_identity": item.get('color_identity', []),
                        "loyalty": item.get('loyalty')
                    })
                    seen_oracles.add(o_id)

                # 3. Card Printing
                card_uuid = uuid.UUID(c_id)
                card_buffer.append({
                    "id": card_uuid,
                    "oracle_id": uuid.UUID(o_id),
                    "set_id": uuid.UUID(s_id),
                    "collection_number": item.get('collector_number'),
                    "rarity": item.get('rarity'),
                    "flavor_text": item.get('flavor_text'),
                    "artist": item.get('artist'),
                    "release_date": parse_date(item.get('released_at')),
                    "layout": item.get('layout'),
                    "card_back_id": uuid.UUID(item['card_back_id']) if item.get('card_back_id') else None
                })

                # 4. Images
                uris = item.get('image_uris')
                if not uris and 'card_faces' in item:
                    faces = item.get('card_faces')
                    if faces and 'image_uris' in faces[0]:
                        uris = faces[0]['image_uris']
                
                if uris:
                    for size, url in uris.items():
                        if size in ['small', 'normal', 'large', 'png', 'art_crop', 'border_crop']:
                            image_buffer.append({"card_id": card_uuid, "size": size, "path": url})

                count += 1
                if count % INTERNAL_BATCH_SIZE == 0:
                    flush_all(session, set_buffer, oracle_buffer, card_buffer, image_buffer)
                    print(f"Processed {count} items...")

            # Final flush
            flush_all(session, set_buffer, oracle_buffer, card_buffer, image_buffer)
            print(f"Done! Total: {count}")

    except Exception as e:
        print(f"FAILED AT CARD: {item.get('name')} from set: {item.get('set_name')}")
        print(f"Card ID: {item.get('id')}")
        print(f"Error Details: {str(e)}")

 
    finally:
        session.close()

if __name__ == "__main__":
    run_ingest()