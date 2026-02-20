from sqlalchemy import text

def refresh_statistics(db: Session):
    db.execute(text("REFRESH MATERIALIZED VIEW card_stats;"))
    db.commit()