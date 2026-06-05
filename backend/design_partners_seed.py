"""JADE OS · Design Partners — seed list of target accounts for the
mid-market+enterprise logistics / supply-chain push.

Pre-populated with:
  • 8 national logistics carriers / 3PLs (XPO, Saia, Heartland, CHR, Schneider,
    Werner, JB Hunt, Old Dominion)
  • 42 MSP / Twin Cities-area regional 3PLs, brokers, freight ops
"""
from typing import List, Dict

SEED_ACCOUNTS: List[Dict] = [
    # ============ NATIONAL · TIER-1 ============
    {"company": "XPO Logistics", "vertical": "logistics_national", "size": "30000+", "city": "Greenwich, CT", "tier": "enterprise", "pilot_value_usd": 25000, "ai_readiness": "high", "notes": "LTL leader. Public. Asked about AI ops at last FreightWaves conf."},
    {"company": "Saia LTL Freight", "vertical": "logistics_national", "size": "10000+", "city": "Johns Creek, GA", "tier": "enterprise", "pilot_value_usd": 25000, "ai_readiness": "high", "notes": "Saia president on record about driver shortage tech-spend."},
    {"company": "Heartland Express", "vertical": "freight_national", "size": "3500+", "city": "North Liberty, IA", "tier": "enterprise", "pilot_value_usd": 25000, "ai_readiness": "med", "notes": "Iowa-based, dry van. Strong MSP corridor presence."},
    {"company": "C.H. Robinson", "vertical": "freight_brokerage", "size": "15000+", "city": "Eden Prairie, MN", "tier": "enterprise", "pilot_value_usd": 25000, "ai_readiness": "high", "notes": "HQ in MSP. Largest broker in N. America. Already building internal AI."},
    {"company": "Schneider National", "vertical": "freight_national", "size": "18000+", "city": "Green Bay, WI", "tier": "enterprise", "pilot_value_usd": 25000, "ai_readiness": "high", "notes": "Mentioned in V3 promo's BOL extraction beat."},
    {"company": "Werner Enterprises", "vertical": "freight_national", "size": "13000+", "city": "Omaha, NE", "tier": "enterprise", "pilot_value_usd": 25000, "ai_readiness": "med", "notes": "Public. Reefer + dry van. Tech-adjacent."},
    {"company": "J.B. Hunt Transport", "vertical": "freight_national", "size": "30000+", "city": "Lowell, AR", "tier": "enterprise", "pilot_value_usd": 25000, "ai_readiness": "high", "notes": "Intermodal leader. Has internal automation team."},
    {"company": "Old Dominion Freight Line", "vertical": "logistics_national", "size": "23000+", "city": "Thomasville, NC", "tier": "enterprise", "pilot_value_usd": 25000, "ai_readiness": "med", "notes": "Premium LTL. Process-driven culture."},

    # ============ MSP / TWIN CITIES REGIONAL ============
    {"company": "Anderson Trucking Service (ATS)", "vertical": "freight_specialized", "size": "1500+", "city": "St. Cloud, MN", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "med", "notes": "Specialized heavy haul. Family-owned. Network in."},
    {"company": "DART Network", "vertical": "logistics_regional", "size": "1000+", "city": "Eagan, MN", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "med", "notes": "Refrigerated + dry. MSP HQ."},
    {"company": "Murphy Warehouse", "vertical": "logistics_regional", "size": "500+", "city": "Minneapolis, MN", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "low", "notes": "100+ year warehousing & 3PL. Family."},
    {"company": "Carlile Logistics", "vertical": "logistics_regional", "size": "300+", "city": "Eagan, MN", "tier": "operator", "pilot_value_usd": 3000, "ai_readiness": "med", "notes": "Asset-light brokerage. AI-curious."},
    {"company": "Dohrn Transfer Co.", "vertical": "logistics_regional", "size": "1200+", "city": "Rock Island, IL", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "low", "notes": "Mid-west LTL. Adjacent market."},
    {"company": "Quality Distribution Services", "vertical": "logistics_regional", "size": "200+", "city": "Brooklyn Park, MN", "tier": "operator", "pilot_value_usd": 3000, "ai_readiness": "low", "notes": "Local distribution. Strong intro candidate."},
    {"company": "Roehl Transport", "vertical": "freight_national", "size": "2500+", "city": "Marshfield, WI", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "med", "notes": "Reefer + dry. Twin Cities lanes."},
    {"company": "Bay & Bay Transportation", "vertical": "freight_regional", "size": "800+", "city": "Rosemount, MN", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "med", "notes": "MSP local. Long-running."},
    {"company": "Halvor Lines", "vertical": "freight_specialized", "size": "300+", "city": "Superior, WI", "tier": "operator", "pilot_value_usd": 3000, "ai_readiness": "low", "notes": "Heavy haul. Network candidate."},
    {"company": "Don's Carrier Service", "vertical": "freight_regional", "size": "75", "city": "Albertville, MN", "tier": "operator", "pilot_value_usd": 3000, "ai_readiness": "low", "notes": "Smaller, hands-on. Likely first signers."},
    {"company": "Premier Bulk Systems", "vertical": "freight_specialized", "size": "150", "city": "Sauk Centre, MN", "tier": "operator", "pilot_value_usd": 3000, "ai_readiness": "low", "notes": "Bulk hauler. Niche."},
    {"company": "ProTrans International", "vertical": "logistics_regional", "size": "1100+", "city": "Indianapolis, IN", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "med", "notes": "Auto-supply chain. Mid-west."},
    {"company": "Northland Pet Foods Logistics", "vertical": "logistics_regional", "size": "120", "city": "Inver Grove Heights, MN", "tier": "operator", "pilot_value_usd": 3000, "ai_readiness": "low", "notes": "Specialty cold-chain. MSP."},
    {"company": "Twin Modal Inc.", "vertical": "freight_brokerage", "size": "85", "city": "Minneapolis, MN", "tier": "operator", "pilot_value_usd": 3000, "ai_readiness": "med", "notes": "Intermodal broker. Operator-led."},
    {"company": "Liberty Linehaul", "vertical": "freight_regional", "size": "120", "city": "Roseville, MN", "tier": "operator", "pilot_value_usd": 3000, "ai_readiness": "low", "notes": "Family-run. Network warm."},
    {"company": "Performance Team", "vertical": "logistics_regional", "size": "5000+", "city": "Bloomington, MN", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "med", "notes": "Maersk-owned 3PL. Real budget."},
    {"company": "Sentinel Transportation", "vertical": "freight_specialized", "size": "400", "city": "Lakeville, MN", "tier": "operator", "pilot_value_usd": 3000, "ai_readiness": "low", "notes": "Tanker. Specialized."},
    {"company": "GlobalTranz", "vertical": "freight_brokerage", "size": "1000+", "city": "Scottsdale, AZ", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "high", "notes": "TMS-adjacent. AI-curious. Worldwide."},
    {"company": "Coyote Logistics", "vertical": "freight_brokerage", "size": "3000+", "city": "Chicago, IL", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "high", "notes": "Owned by UPS. Mid-west presence."},
    {"company": "Echo Global Logistics", "vertical": "freight_brokerage", "size": "2500+", "city": "Chicago, IL", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "high", "notes": "Tech-forward. Likely competitor in some lanes."},
    {"company": "Convoy (post-acquisition)", "vertical": "freight_brokerage", "size": "500", "city": "Seattle, WA", "tier": "operator", "pilot_value_usd": 3000, "ai_readiness": "high", "notes": "Asset of Flexport now. Reach to ex-team."},
    {"company": "Uber Freight", "vertical": "freight_brokerage", "size": "1500+", "city": "Chicago, IL", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "high", "notes": "Tech-native broker."},
    {"company": "Loadsmart", "vertical": "freight_brokerage", "size": "350", "city": "Chicago, IL", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "high", "notes": "AI-first. Competitor or partner."},
    {"company": "Mode Transportation", "vertical": "freight_brokerage", "size": "650", "city": "Memphis, TN", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "med", "notes": "Mode is owned by York Capital."},
    {"company": "Allen Lund Company", "vertical": "freight_brokerage", "size": "650", "city": "La Cañada Flintridge, CA", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "med", "notes": "Produce + dry van. Mid-west office."},
    {"company": "MoLo Solutions", "vertical": "freight_brokerage", "size": "600", "city": "Chicago, IL", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "med", "notes": "Family-owned. Acquired by ArcBest."},
    {"company": "Roadrunner Transportation", "vertical": "freight_national", "size": "2000+", "city": "Downers Grove, IL", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "low", "notes": "LTL. Turnaround mode — good AI cost-savings pitch."},
    {"company": "TFI International", "vertical": "freight_national", "size": "25000+", "city": "Montreal, QC (US ops)", "tier": "enterprise", "pilot_value_usd": 25000, "ai_readiness": "med", "notes": "Owns TForce Freight. North America-wide."},
    {"company": "Yellow Corp · DBA YRC", "vertical": "freight_national", "size": "2000+ post-restruct", "city": "Overland Park, KS", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "low", "notes": "Restructuring. Skip unless re-emergence."},
    {"company": "ArcBest Corporation", "vertical": "logistics_national", "size": "14000+", "city": "Fort Smith, AR", "tier": "enterprise", "pilot_value_usd": 25000, "ai_readiness": "med", "notes": "ABF Freight parent. Diversified."},
    {"company": "Estes Express Lines", "vertical": "logistics_national", "size": "20000+", "city": "Richmond, VA", "tier": "enterprise", "pilot_value_usd": 25000, "ai_readiness": "med", "notes": "Family-owned LTL giant. Process-rich."},
    {"company": "Forward Air", "vertical": "logistics_national", "size": "5000+", "city": "Greeneville, TN", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "med", "notes": "Expedited freight. Public."},
    {"company": "Landstar System", "vertical": "freight_brokerage", "size": "8000+ agents", "city": "Jacksonville, FL", "tier": "enterprise", "pilot_value_usd": 25000, "ai_readiness": "high", "notes": "Agent-based brokerage. Each agent is a JADE prospect."},
    {"company": "Hub Group", "vertical": "logistics_national", "size": "5500+", "city": "Oak Brook, IL", "tier": "enterprise", "pilot_value_usd": 25000, "ai_readiness": "high", "notes": "Intermodal + brokerage. Tech budget."},
    {"company": "K & B Transportation", "vertical": "freight_regional", "size": "700", "city": "South Sioux City, NE", "tier": "operator", "pilot_value_usd": 3000, "ai_readiness": "low", "notes": "Reefer mid-west. Founder-led."},
    {"company": "USA Truck (Schneider sub)", "vertical": "freight_national", "size": "2500+", "city": "Van Buren, AR", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "med", "notes": "Schneider acquired. Internal AI projects."},
    {"company": "RXO", "vertical": "freight_brokerage", "size": "8000+", "city": "Charlotte, NC", "tier": "enterprise", "pilot_value_usd": 25000, "ai_readiness": "high", "notes": "Spun out of XPO. Asset-light broker."},
    {"company": "GXO Logistics", "vertical": "logistics_national", "size": "120000+", "city": "Greenwich, CT", "tier": "enterprise", "pilot_value_usd": 25000, "ai_readiness": "high", "notes": "World's biggest pure-play 3PL. Spun from XPO."},
    {"company": "Knight-Swift Transportation", "vertical": "freight_national", "size": "30000+", "city": "Phoenix, AZ", "tier": "enterprise", "pilot_value_usd": 25000, "ai_readiness": "high", "notes": "Largest US TL. Process leader."},
    {"company": "U.S. Xpress (Knight-Swift)", "vertical": "freight_national", "size": "8000+", "city": "Chattanooga, TN", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "med", "notes": "Now part of Knight-Swift."},
    {"company": "Marten Transport", "vertical": "freight_specialized", "size": "4500+", "city": "Mondovi, WI", "tier": "fleet", "pilot_value_usd": 10000, "ai_readiness": "med", "notes": "Reefer specialist. Public."},
    {"company": "USA Logistics (MN)", "vertical": "logistics_regional", "size": "80", "city": "Burnsville, MN", "tier": "operator", "pilot_value_usd": 3000, "ai_readiness": "low", "notes": "MSP local 3PL. Strong intro."},
    {"company": "Empire Express Inc", "vertical": "freight_regional", "size": "200", "city": "Memphis, TN", "tier": "operator", "pilot_value_usd": 3000, "ai_readiness": "low", "notes": "Mid-south carrier."},
    {"company": "Boyle Transportation", "vertical": "freight_specialized", "size": "180", "city": "Billerica, MA", "tier": "operator", "pilot_value_usd": 3000, "ai_readiness": "med", "notes": "Pharma & defense. High-trust niche."},
]
