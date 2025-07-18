from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class TicketInfo:
    PatientFirstName: str
    PatientLastName: str
    AccountNum: int
    StreetAddress: str
    City: str
    State: str
    Zip: str
    Date: str
    Telephone: str
    EmailAddress: Optional[str] = None
    Units: List[int] = field(default_factory=list)
    HCodes: List[str] = field(default_factory=list)
    CodeDescriptions: List[str] = field(default_factory=list)
    ICodes: List[str] = field(default_factory=list)
    
