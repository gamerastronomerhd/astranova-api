from pydantic import BaseModel
from typing import Optional, List, Dict

# 1. SHIP SCHEMAS
class ShipCreate(BaseModel):
    game_id: str
    name: str
    rarity: str
    faction: str
    hull_type: str
    is_research: bool = False
    icon_url: Optional[str] = None

class ShipStatsCreate(BaseModel):
    health: int
    firepower: int
    torpedo: int
    aviation: int
    anti_air: int
    reload: int
    evasion: int
    armor_type: str
    speed: int
    accuracy: int
    luck: int
    anti_sub: int
    oil_cost: int
    
    hp_120: int | None = 0
    fp_120: int | None = 0
    aa_120: int | None = 0
    avi_120: int | None = 0
    trp_120: int | None = 0
    reload_120: int | None = 0
    evasion_120: int | None = 0
    accuracy_120: int | None = 0
    anti_sub_120: int | None = 0

class ShipStats(ShipStatsCreate):
    id: int
    ship_id: int
    class Config:
        from_attributes = True

class ShipResponse(ShipCreate):
    id: int
    stats: Optional[ShipStats] = None 
    class Config:
        from_attributes = True

class ShipIconUpdate(BaseModel):
    icon_url: str

# 2. EQUIPMENT SCHEMAS
class EquipmentBase(BaseModel):
    name: str
    category: str
    rarity: str
    icon_url: Optional[str] = None

class EquipmentCreate(EquipmentBase):
    pass

class EquipmentResponse(EquipmentBase):
    id: int
    class Config:
        from_attributes = True

# 3. COLLECTION SCHEMAS
class CollectionCreate(BaseModel):
    ship_id: int
    level: int = 1
    is_oathed: bool = False
    affection: int = 50
    
    bonus_hp: int = 0
    bonus_fp: int = 0
    bonus_aa: int = 0
    bonus_avi: int = 0
    bonus_trp: int = 0
    bonus_rld: int = 0

class CollectionResponse(BaseModel):
    id: int
    ship_id: int
    level: int
    is_oathed: bool
    affection: int
    ship: ShipResponse
    
    bonus_hp: int = 0
    bonus_fp: int = 0
    bonus_aa: int = 0
    bonus_avi: int = 0
    bonus_trp: int = 0
    bonus_rld: int = 0
    
    # --- THE CRITICAL FIX ---
    # This must exist here to show up on your dashboard!
    calculated_stats: Optional[Dict[str, int]] = None 
    
    # Gear Slots
    eq1: Optional[EquipmentResponse] = None
    eq2: Optional[EquipmentResponse] = None
    eq3: Optional[EquipmentResponse] = None
    eq4: Optional[EquipmentResponse] = None
    eq5: Optional[EquipmentResponse] = None

    class Config:
        from_attributes = True

# 4. USER SCHEMAS
class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    class Config:
        from_attributes = True