from enum import Enum

class TripStatusType(Enum) :
    FIRST_TRIP = "first trip"
    SECOND_TRIP = "second trip"
    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace("_", " ").title()) for key in cls]
    
class PaymentMethodType(Enum) :
    UPI = "upi"
    CASH = "cash"
    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace("_", " ").title()) for key in cls]
    

class PayMentStatus(Enum) :
    PAID = "paid"
    PENDING = "pending"
    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace("_", " ").title()) for key in cls]

