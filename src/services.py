import json
from fastapi import HTTPException
from pathlib import Path
from fastapi.responses import StreamingResponse
import jinja2
from weasyprint import HTML
from src.schema import TruckInvoiceRequest
from fastapi.responses import StreamingResponse
from weasyprint import HTML
import qrcode
from io import BytesIO
from PIL import Image
import base64
from datetime import datetime, timedelta
import uuid

templates = jinja2.Environment(
    loader=jinja2.FileSystemLoader("templates"),
    autoescape=True
)


class InvoiceOperationServices :
    
    @staticmethod
    async def generate_qr_data(token: str , request) -> str:
        now = datetime.utcnow()
        expiry = now + timedelta(hours=2)
        qr_data = {
            "day": now.strftime("%A"),  # Monday
            "date": now.strftime("%Y-%m-%d"),  # 2026-01-04
            "time": now.strftime("%H:%M"),  # 17:06
            "expired_time": expiry.strftime("%Y-%m-%d %H:%M"),  # 2026-01-04 19:06
            "sl_no": request.sl_no,
            "car_number": request.car_number,
            "wheels": request.wheels,
            "cargo_type": request.cargo_type,
            "cft": request.cft,
            "expiry_ts": int(expiry.timestamp() * 1000)  # JS timestamp
        }
        
        return json.dumps(qr_data)  # String for QR
    
    # TODO :- Finish this 
    @staticmethod
    async def generate_qr_data_for_online(token : str , request) -> dict :
        now = datetime.utcnow()
        expiry = now + timedelta(hours=2)
        # url generation


    
    @staticmethod 
    async def generate_invoice(request : TruckInvoiceRequest) :
        try :
            
            # Generate unique token for QR (2-hour expiry)
            token = str(uuid.uuid4())
            qr_data = await InvoiceOperationServices.generate_qr_data(token , request)
            
            # Generate QR as base64
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()
            

            # Render template - pass raw data only
            template = templates.get_template("invoice.html")
            html_content = template.render(
                sl_no=request.sl_no,
                date_time=request.date_time, 
                car_number=request.car_number,
                wheels=request.wheels,
                cargo_type=request.cargo_type,
                cft=request.cft,
                qr_base64=qr_base64,
                token=token[:8]
            )
    
            # Generate PDF
            html = HTML(string=html_content)
            pdf_bytes = html.write_pdf()
            
            filename = f"invoice-{request.car_number.replace(' ', '')}-{token[:8]}.pdf"
            return StreamingResponse(
                BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        except Exception as e :
            raise HTTPException(400 , detail=str(e))