@app.get("/stats/top-cards")
def get_top_cards(db: Session = Depends(get_db)):
    # This query is lightning fast because the math is already done!
    return db.query(CardStats).order_by(CardStats.appearance_count.desc()).limit(10).all()