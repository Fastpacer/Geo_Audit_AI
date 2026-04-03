# backend/app/routes/audit.py
from fastapi import APIRouter, HTTPException
from app.models.schemas import AuditRequest, AuditResponse
from app.services.scraper import scrape_page
from app.services.schema_generator import generate_schema
from app.services.geo_analyzer import geo_analyze

router = APIRouter()

@router.post("/audit", response_model=AuditResponse)
async def audit_url(request: AuditRequest):
    try:
        # Convert Pydantic Url to string
        url_str = str(request.url)
        
        # Extract content
        scraped_data = await scrape_page(url_str)
        
        # Generate schema (sync function)
        schema = generate_schema(scraped_data, url_str)
        
        # GEO analysis (sync function)
        geo_analysis = geo_analyze(scraped_data)
        
        # Build response
        response = {
            "url": scraped_data.get("url", url_str),
            "title": scraped_data.get("title", ""),
            "meta_description": scraped_data.get("meta_description", ""),
            "headings": scraped_data.get("headings", []),
            "content": scraped_data.get("content", ""),
            "image": scraped_data.get("image", ""),
            "og_image": scraped_data.get("og_image", ""),
            "confidence_score": scraped_data.get("confidence_score", 0),
            "signal_strength": scraped_data.get("signal_strength", {
                "source": "unknown",
                "method": "unknown", 
                "tier": "unknown",
                "platform": "unknown"
            }),
            "is_dynamic": scraped_data.get("is_dynamic", False),
            "is_inferred": scraped_data.get("is_inferred", False),
            "json_ld": schema,
            "geo_analysis": geo_analysis
        }
        
        return response

    except Exception as e:
        import traceback
        print(f"ERROR in audit: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))