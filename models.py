from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Ship(Base):
    __tablename__ = "ships"

    # Core Identifiers
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, unique=True, index=True) 
    name = Column(String, index=True)
    
    # Classification
    rarity = Column(String) # e.g., "Super Rare", "Ultra Rare"
    faction = Column(String) # e.g., "Eagle Union", "Sakura Empire"
    hull_type = Column(String) # e.g., "CV", "BB", "DD"
    is_research = Column(Boolean, default=False) # Is it a PR/DR ship?
    icon_url = Column(String, nullable=True) # Image CDN Link (Connecting to your Cloudflare R2 bucket later)

    # --- NEW: The Relationships ---
    # A ship has one specific set of base stats
    stats = relationship("ShipBaseStats", back_populates="ship", uselist=False)
    # A ship can appear in your collection (1-to-many, to account for duplicate copies)
    collection_entries = relationship("MyCollection", back_populates="ship")

# --- NEW TABLE: Static Game Data ---
class ShipBaseStats(Base):
    __tablename__ = "ship_base_stats"

    id = Column(Integer, primary_key=True, index=True)
    ship_id = Column(Integer, ForeignKey("ships.id")) 
    
    # Core Combat Stats
    health = Column(Integer)
    firepower = Column(Integer)
    torpedo = Column(Integer)
    aviation = Column(Integer)
    anti_air = Column(Integer)
    reload = Column(Integer)
    evasion = Column(Integer)
    
    # Mechanics & Utility
    armor_type = Column(String) # Light, Medium, Heavy
    speed = Column(Integer)
    accuracy = Column(Integer)
    luck = Column(Integer)
    anti_sub = Column(Integer)
    oil_cost = Column(Integer)

    # The Python bridge back to the Ship table
    ship = relationship("Ship", back_populates="stats")

# --- NEW TABLE: Dynamic Player Data ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    # A user can have many ships in their dock
    collection = relationship("MyCollection", back_populates="owner")
    
class Equipment(Base):
    __tablename__ = "equipment"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String) # Main Gun, Torpedo, AA Gun, Plane, Aux
    rarity = Column(String)
    icon_url = Column(String, nullable=True)

class MyCollection(Base):
    __tablename__ = "my_collection"
    id = Column(Integer, primary_key=True, index=True)
    ship_id = Column(Integer, ForeignKey("ships.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    level = Column(Integer, default=1)
    is_oathed = Column(Boolean, default=False)
    affection = Column(Integer, default=50)
    
    bonus_hp = Column(Integer, default=0)
    bonus_fp = Column(Integer, default=0)
    bonus_aa = Column(Integer, default=0)
    bonus_avi = Column(Integer, default=0)
    bonus_trp = Column(Integer, default=0)
    bonus_rld = Column(Integer, default=0)
    
    # Relationships
    ship = relationship("Ship")
    user = relationship("User", back_populates="collection")

    # --- THE NEW GEAR SLOTS ---
    # These store the ID of a piece of equipment from the 'equipment' table
    slot_1 = Column(Integer, ForeignKey("equipment.id"), nullable=True)
    slot_2 = Column(Integer, ForeignKey("equipment.id"), nullable=True)
    slot_3 = Column(Integer, ForeignKey("equipment.id"), nullable=True)
    slot_4 = Column(Integer, ForeignKey("equipment.id"), nullable=True)
    slot_5 = Column(Integer, ForeignKey("equipment.id"), nullable=True)

    ship = relationship("Ship")
    owner = relationship("User", back_populates="collection")
    # Relationships to see what gear is equipped
    eq1 = relationship("Equipment", foreign_keys=[slot_1])
    eq2 = relationship("Equipment", foreign_keys=[slot_2])
    eq3 = relationship("Equipment", foreign_keys=[slot_3])
    eq4 = relationship("Equipment", foreign_keys=[slot_4])
    eq5 = relationship("Equipment", foreign_keys=[slot_5])