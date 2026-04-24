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
    icon_url = Column(String, nullable=True) # Image CDN Link

    # Relationships
    stats = relationship("ShipBaseStats", back_populates="ship", uselist=False)
    collection_entries = relationship("MyCollection", back_populates="ship")
    skins = relationship("ShipSkin", back_populates="ship")

class ShipBaseStats(Base):
    __tablename__ = "ship_base_stats"

    id = Column(Integer, primary_key=True, index=True)
    ship_id = Column(Integer, ForeignKey("ships.id"), unique=True)
    
    health = Column(Integer)
    firepower = Column(Integer)
    torpedo = Column(Integer)
    aviation = Column(Integer)
    anti_air = Column(Integer)
    reload = Column(Integer)
    evasion = Column(Integer)
    armor_type = Column(String)
    speed = Column(Integer)
    accuracy = Column(Integer)
    luck = Column(Integer)
    anti_sub = Column(Integer)
    oil_cost = Column(Integer)

    # 120 COLUMNS
    hp_120 = Column(Integer, default=0)
    fp_120 = Column(Integer, default=0)
    aa_120 = Column(Integer, default=0)
    avi_120 = Column(Integer, default=0)
    trp_120 = Column(Integer, default=0)
    reload_120 = Column(Integer, default=0)
    evasion_120 = Column(Integer, default=0)
    accuracy_120 = Column(Integer, default=0)
    anti_sub_120 = Column(Integer, default=0)

    # --- NEW: 3-TIER FLEET TECH COLUMNS ---
    get_stat = Column(String, nullable=True)
    get_value = Column(Integer, default=0)
    mlb_stat = Column(String, nullable=True)
    mlb_value = Column(Integer, default=0)
    lv120_stat = Column(String, nullable=True)
    lv120_value = Column(Integer, default=0)

    ship = relationship("Ship", back_populates="stats")

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
    
    # THE NEW GEAR SLOTS
    slot_1 = Column(Integer, ForeignKey("equipment.id"), nullable=True)
    slot_2 = Column(Integer, ForeignKey("equipment.id"), nullable=True)
    slot_3 = Column(Integer, ForeignKey("equipment.id"), nullable=True)
    slot_4 = Column(Integer, ForeignKey("equipment.id"), nullable=True)
    slot_5 = Column(Integer, ForeignKey("equipment.id"), nullable=True)

    # --- CLEANED UP RELATIONSHIPS ---
    ship = relationship("Ship", back_populates="collection_entries")
    owner = relationship("User", back_populates="collection")
    
    eq1 = relationship("Equipment", foreign_keys=[slot_1])
    eq2 = relationship("Equipment", foreign_keys=[slot_2])
    eq3 = relationship("Equipment", foreign_keys=[slot_3])
    eq4 = relationship("Equipment", foreign_keys=[slot_4])
    eq5 = relationship("Equipment", foreign_keys=[slot_5])
    
class ShipSkin(Base):
    __tablename__ = "ship_skins"
    id = Column(Integer, primary_key=True, index=True)
    ship_id = Column(Integer, ForeignKey("ships.id"))
    name = Column(String) # e.g., "Default", "Beachside Vacation", "L2D"
    painting_url = Column(String)

    # This links it back to the main ship
    ship = relationship("Ship", back_populates="skins")