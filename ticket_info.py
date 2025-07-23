from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class TicketInfo:
    """
    Data model representing a patient's delivery ticket information.

    Attributes:
        PatientFirstName (str): Patient's first name.
        PatientLastName (str): Patient's last name.
        AccountNum (int): Patient's account number.
        StreetAddress (str): Street address for delivery.
        City (str): City of the address.
        State (str): State of the address.
        Zip (str): ZIP code.
        Date (str): Date of service or order.
        Telephone (str): Contact phone number.
        EmailAddress (Optional[str]): Email address, if available.
        Units (List[int]): List of unit quantities per item.
        HCodes (List[str]): List of HCPCS codes.
        CodeDescriptions (List[str]): Human-readable descriptions of each code.
        ICodes (List[str]): Internal or inventory codes (optional additional identifiers).
    """
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
    
