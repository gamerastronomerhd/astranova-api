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

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
@app.post("/ships/")
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
@app.patch("/ships/{ship_id}/icon/")
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

# Change the POST route to this:
@app.post("/collection/", response_model=schemas.CollectionResponse)
def add_to_collection(
    item: schemas.CollectionCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user) # The Scanner
):
    db_item = models.MyCollection(
        ship_id=item.ship_id,
        user_id=current_user.id, # Uses the ID from the Token!
        level=item.level,
        is_oathed=item.is_oathed,
        affection=item.affection
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/collection/me", response_model=list[schemas.CollectionResponse])
def get_my_collection(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    items = db.query(models.MyCollection).filter(models.MyCollection.user_id == current_user.id).all()
    
    for item in items:
        # We find the physical base stats for this ship
        base = db.query(models.ShipBaseStats).filter(models.ShipBaseStats.ship_id == item.ship_id).first()
        if base:
            # We call the math function we wrote earlier
            item.calculated_stats = calculate_real_stats(base, item.level, item.affection, item.is_oathed)
        else:
            # If no stats found, show base 100 so it's not 0
            item.calculated_stats = {"hp": 100, "fp": 10, "aa": 10}
            
    return items
    
@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed = get_password_hash(user.password) # Scramble it!
    db_user = models.User(username=user.username, hashed_password=hashed)
    # ... rest of the save logic
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
    
@app.post("/equipment/", response_model=schemas.EquipmentResponse)
def create_equipment(item: schemas.EquipmentCreate, db: Session = Depends(get_db)):
    db_item = models.Equipment(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/equipment/", response_model=list[schemas.EquipmentResponse])
def get_all_equipment(db: Session = Depends(get_db)):
    equipment = db.query(models.Equipment).all()
    return equipment

@app.patch("/collection/{collection_id}/equip/{slot_num}")
def equip_gear(
    collection_id: int, 
    slot_num: int, 
    equipment_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Verify the ship is in YOUR dock
    db_item = db.query(models.MyCollection).filter(
        models.MyCollection.id == collection_id, 
        models.MyCollection.user_id == current_user.id
    ).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Ship not found in your dock.")

    # 2. Verify the Equipment actually exists in the Global Armory
    gear = db.query(models.Equipment).filter(models.Equipment.id == equipment_id).first()
    if not gear:
        raise HTTPException(status_code=404, detail="Equipment not found in database.")

    # 3. The "Smart" Guardrails (Category Checking)
    # Simplified Azur Lane logic for the database
    valid = True
    error_msg = ""

    if slot_num == 1 and gear.category not in ["Main Gun", "Fighter", "Submarine Torpedo"]:
        valid = False
        error_msg = f"Slot 1 requires a Main Gun or Fighter. You tried to equip a {gear.category}."
        
    elif slot_num == 2 and gear.category not in ["Torpedo", "Dive Bomber", "Secondary Gun"]:
        valid = False
        error_msg = f"Slot 2 requires a Torpedo, Dive Bomber, or Secondary. You tried to equip a {gear.category}."
        
    elif slot_num == 3 and gear.category not in ["Anti-Air Gun", "Torpedo Bomber"]:
        valid = False
        error_msg = f"Slot 3 requires an AA Gun or Torpedo Bomber. You tried to equip a {gear.category}."
        
    elif slot_num in [4, 5] and gear.category != "Auxiliary":
        valid = False
        error_msg = f"Slots 4 and 5 are strictly for Auxiliary gear. You tried to equip a {gear.category}."

    if not valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # 4. If it passes all tests, physically bolt it onto the ship!
    setattr(db_item, f"slot_{slot_num}", equipment_id)
    
    db.commit()
    return {"message": f"Successfully equipped {gear.name} into Slot {slot_num}!"}
    
def calculate_real_stats(base_stats, level, affection, is_oathed):
    # Simplified Azur Lane growth (1% increase per level for this example)
    growth_factor = 1 + (level - 1) * 0.02 
    
    # Affection Bonus logic
    bonus = 1.0
    if is_oathed:
        bonus = 1.12 # 12% boost for Oathed
    elif affection >= 100:
        bonus = 1.06 # 6% boost for Love
        
    calculated = {
        "hp": int(base_stats.health * growth_factor * bonus),
        "fp": int(base_stats.firepower * growth_factor * bonus),
        "aa": int(base_stats.anti_air * growth_factor * bonus),
        # Add more stats here as needed!
    }
    return calculated
    
@app.delete("/collection/{collection_id}")
def retire_ship(
    collection_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # Only delete if it belongs to the logged-in user
    db_item = db.query(models.MyCollection).filter(
        models.MyCollection.id == collection_id, 
        models.MyCollection.user_id == current_user.id
    ).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Ship not found")
        
    db.delete(db_item)
    db.commit()
    return {"message": "Ship retired from dock"}