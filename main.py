from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models
import schemas
from database import engine, SessionLocal
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

# --- SECURITY CONFIG ---
# It will look for a secure cloud variable, but fall back to the string for local testing
import os
SECRET_KEY = os.getenv("SECRET_KEY", "SUPER_SECRET_ASTRA_NOVA_KEY")
ALGORITHM = "HS256" # <-- Make sure this is still here!
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- THE DATABASE CONNECTION MANAGER ---
# This opens a conversation with PostgreSQL for a single request, then safely closes it.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Helper Function: Create the VIP Pass ---
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- THE ID SCANNER ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        # 1. Decode the VIP Pass
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        
        # 2. If no ID is found, reject them
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid Authentication Token")
            
        # 3. Double-check the user still exists in the database
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
            
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

def get_password_hash(password):
    return pwd_context.hash(password)

# Physically create the tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AstraNova API",
    description="Backend engine for the GamerAstronomer completionist database.",
    version="1.2.1"
)

class UserCreate(BaseModel):
    username: str
    password: str

@app.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Commander name already registered.")
    
    # Hash the password and create the user
    hashed_password = pwd_context.hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": f"Welcome to AstraNova, Commander {new_user.username}! You can now log in."}

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    # Verify user exists and password hash matches
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username, "id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}
    
# --- THE CORS BRIDGE ---
# This allows your local HTML files to talk to the API without the browser blocking it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- EXISTING STATUS ROUTE ---
@app.get("/")
def root_status():
    return {"status": "online", "project": "AstraNova"}

# --- NEW: THE POST REQUEST ---
@app.post("/ships/", response_model=schemas.ShipResponse)
def create_ship(ship: schemas.ShipCreate, db: Session = Depends(get_db)):
    # 1. Translate the incoming API data (Pydantic) into a Database row (SQLAlchemy)
    db_ship = models.Ship(
        game_id=ship.game_id,
        name=ship.name,
        rarity=ship.rarity,
        faction=ship.faction,
        hull_type=ship.hull_type,
        is_research=ship.is_research,
        icon_url=ship.icon_url
    )
    
    # 2. Stage the new ship in the database session
    db.add(db_ship)
    
    # 3. Commit (permanently save) the transaction to PostgreSQL
    db.commit()
    
    # 4. Refresh the data so PostgreSQL assigns it a physical ID number, then return it to the user
    db.refresh(db_ship)
    return db_ship
 
# --- THE GET REQUEST ---
# We added response_model here to force FastAPI to use the new "Join" schema
@app.get("/ships/", response_model=list[schemas.ShipResponse])
def read_ships(db: Session = Depends(get_db)):
    # Tell SQLAlchemy to query the Ship table and return all rows
    ships = db.query(models.Ship).all()
    return ships

# --- NEW: PATCH Route to Update the Image ---
@app.patch("/ships/{ship_id}/icon/", response_model=schemas.ShipResponse)
def update_ship_icon(ship_id: int, icon_data: schemas.ShipIconUpdate, db: Session = Depends(get_db)):
    # 1. Find the specific ship in the database
    db_ship = db.query(models.Ship).filter(models.Ship.id == ship_id).first()
    
    # 2. Overwrite the old "null" value with the new Cloudflare URL
    db_ship.icon_url = icon_data.icon_url
    
    # 3. Save the changes
    db.commit()
    db.refresh(db_ship)
    return db_ship

# --- POST Route for Relational Data ---
@app.post("/ships/{ship_id}/stats/")
def add_ship_stats(ship_id: int, stats: schemas.ShipStatsCreate, db: Session = Depends(get_db)):
    # 1. Translate the incoming stats into a Database row, tagging it with the specific ship_id
    db_stats = models.ShipBaseStats(
        ship_id=ship_id, # This is the anchor linking it to Enterprise!
        health=stats.health,
        firepower=stats.firepower,
        torpedo=stats.torpedo,
        aviation=stats.aviation,
        anti_air=stats.anti_air,
        reload=stats.reload,
        evasion=stats.evasion,
        armor_type=stats.armor_type,
        speed=stats.speed,
        accuracy=stats.accuracy,
        luck=stats.luck,
        anti_sub=stats.anti_sub,
        oil_cost=stats.oil_cost
    )
    # 2. Save it to PostgreSQL
    db.add(db_stats)
    db.commit()
    db.refresh(db_stats)
    return db_stats

# --- ADD A BRAND NEW SHIP TO YOUR DOCK ---
@app.post("/collection/", response_model=schemas.CollectionResponse)
def add_to_collection(
    item: schemas.CollectionCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    db_item = models.MyCollection(
        ship_id=item.ship_id,
        user_id=current_user.id,
        level=item.level,
        is_oathed=item.is_oathed,
        affection=item.affection,
        # Save the initial bonuses (usually 0 when first added)
        bonus_hp=item.bonus_hp,
        bonus_fp=item.bonus_fp,
        bonus_aa=item.bonus_aa,
        bonus_avi=item.bonus_avi,
        bonus_trp=item.bonus_trp,
        bonus_rld=item.bonus_rld
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# --- NEW: UPDATE AN EXISTING SHIP IN YOUR DOCK (THE PATCH ROUTE) ---
@app.patch("/collection/{collection_id}", response_model=schemas.CollectionResponse)
def update_collection_item(
    collection_id: int,
    item_update: schemas.CollectionCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Find the exact ship in the user's dock
    db_item = db.query(models.MyCollection).filter(
        models.MyCollection.id == collection_id,
        models.MyCollection.user_id == current_user.id
    ).first()

    if not db_item:
        raise HTTPException(status_code=404, detail="Ship not found in your dock")

    # Update all parameters
    db_item.level = item_update.level
    db_item.affection = item_update.affection
    db_item.is_oathed = item_update.is_oathed
    db_item.bonus_hp = item_update.bonus_hp
    db_item.bonus_fp = item_update.bonus_fp
    db_item.bonus_aa = item_update.bonus_aa
    db_item.bonus_avi = item_update.bonus_avi
    db_item.bonus_trp = item_update.bonus_trp
    db_item.bonus_rld = item_update.bonus_rld

    db.commit()
    db.refresh(db_item)
    return db_item

# --- GET YOUR ENTIRE DOCK ---
@app.get("/collection/me", response_model=list[schemas.CollectionResponse])
def get_my_collection(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # We completely removed the old "calculate_real_stats" loop here!
    # The database just sends the raw info, and your JavaScript engine handles all the complex math perfectly.
    items = db.query(models.MyCollection).filter(models.MyCollection.user_id == current_user.id).all()
    return items

# --- RETIRE A SHIP ---
@app.delete("/collection/{collection_id}")
def retire_ship(
    collection_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    db_item = db.query(models.MyCollection).filter(
        models.MyCollection.id == collection_id, 
        models.MyCollection.user_id == current_user.id
    ).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Ship not found")
        
    db.delete(db_item)
    db.commit()
    return {"message": "Ship retired from dock"}