from sqlalchemy.orm import Session
from app.models.film import Film, FilmCategory, Category
from app.schemas.film import FilmCreate, FilmUpdate

def get_film(db: Session, film_id: int):
    """
    Retrieve a single film by its ID.
    """
    return db.query(Film).filter(Film.film_id == film_id).first()

def get_films(db: Session, skip: int = 0, limit: int = 100, title_query: str = None):
    """
    Retrieve a list of films with pagination and optional search by title.
    """
    query = db.query(Film)
    if title_query:
        query = query.filter(Film.title.ilike(f"%{title_query}%"))
    return query.offset(skip).limit(limit).all()

def create_film(db: Session, film_in: FilmCreate):
    """
    Create a new film and associate it with any provided category IDs.
    """
    # Extract categories and create film object
    film_data = film_in.model_dump(exclude={"category_ids"})
    db_film = Film(**film_data)
    
    db.add(db_film)
    db.flush()  # Flush to populate db_film.film_id
    
    # Associate categories
    if film_in.category_ids:
        for cat_id in film_in.category_ids:
            category_exists = db.query(Category).filter(Category.category_id == cat_id).first()
            if category_exists:
                db_fc = FilmCategory(film_id=db_film.film_id, category_id=cat_id)
                db.add(db_fc)
                
    db.commit()
    db.refresh(db_film)
    return db_film

def update_film(db: Session, film_id: int, film_in: FilmUpdate):
    """
    Update a film's information and refresh its category associations.
    """
    db_film = get_film(db, film_id)
    if not db_film:
        return None
    
    # Apply standard column updates
    update_data = film_in.model_dump(exclude_unset=True, exclude={"category_ids"})
    for key, value in update_data.items():
        setattr(db_film, key, value)
        
    # Re-associate categories if specified
    if film_in.category_ids is not None:
        # Clear existing category mappings
        db.query(FilmCategory).filter(FilmCategory.film_id == film_id).delete()
        # Add new mappings
        for cat_id in film_in.category_ids:
            category_exists = db.query(Category).filter(Category.category_id == cat_id).first()
            if category_exists:
                db_fc = FilmCategory(film_id=film_id, category_id=cat_id)
                db.add(db_fc)
                
    db.commit()
    db.refresh(db_film)
    return db_film

def delete_film(db: Session, film_id: int):
    """
    Delete a film by its ID.
    """
    db_film = get_film(db, film_id)
    if not db_film:
        return None
    db.delete(db_film)
    db.commit()
    return db_film
