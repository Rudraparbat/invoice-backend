from fastapi import APIRouter

from src.schema import TruckInvoiceRequest
from src.services import InvoiceOperationServices
router = APIRouter()

@router.post("/generate-invoice")
async def generate_invoice(body : TruckInvoiceRequest) :
    return await InvoiceOperationServices.generate_invoice(body)