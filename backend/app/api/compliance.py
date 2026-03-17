from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserProgress, LearningModule

router = APIRouter()

FRAMEWORKS = {
    "cyber_essentials": {
        "name": "Cyber Essentials",
        "icon": "GB",
        "colour": "blue",
        "description": "UK government-backed scheme protecting against common cyber threats",
        "modules": ["phishing-awareness","password-security","device-security","safe-browsing","network-security-basics","email-security-and-anti-phishing","mobile-device-security-essentials","understanding-vulnerability-management"]
    },
    "gdpr": {
        "name": "UK GDPR",
        "icon": "lock",
        "colour": "purple",
        "description": "UK General Data Protection Regulation compliance",
        "modules": ["understanding-data-protection-and-gdpr","data-handling-gdpr","understanding-identity-and-access-management","cloud-security-best-practices","secure-software-development-practices"]
    },
    "dora": {
        "name": "DORA",
        "icon": "bank",
        "colour": "orange",
        "description": "Digital Operational Resilience Act for financial entities",
        "modules": ["understanding-dora-compliance-for-financial-services","incident-response-planning-essentials","business-continuity-and-disaster-recovery-essentials","understanding-vulnerability-management","understanding-supply-chain-security","introduction-to-threat-hunting-techniques","dark-web-monitoring-and-threat-intelligence"]
    },
    "fca": {
        "name": "FCA Cyber Resilience",
        "icon": "shield",
        "colour": "green",
        "description": "FCA operational resilience and cyber requirements",
        "modules": ["understanding-fca-cyber-resilience-requirements","understanding-dora-compliance-for-financial-services","incident-response-planning-essentials","business-continuity-and-disaster-recovery-essentials","understanding-identity-and-access-management","introduction-to-security-operations-centre"]
    },
    "nis2": {
        "name": "NIS2 Directive",
        "icon": "EU",
        "colour": "yellow",
        "description": "Network and Information Security Directive 2",
        "modules": ["incident-response-planning-essentials","understanding-vulnerability-management","network-security-basics","understanding-supply-chain-security","business-continuity-and-disaster-recovery-essentials","cloud-security-best-practices","introduction-to-security-operations-centre","cryptography-essentials"]
    }
}

@router.get("/status")
async def get_compliance_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Get all completed modules for user
    completed = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.status == "completed"
    ).all()
    completed_module_ids = {p.module_id for p in completed}

    # Get all modules
    all_modules = db.query(LearningModule).all()
    slug_to_id = {m.slug: m.id for m in all_modules}
    slug_to_title = {m.slug: m.title for m in all_modules}

    result = []
    for fw_id, fw in FRAMEWORKS.items():
        fw_modules = fw["modules"]
        completed_fw = []
        pending_fw = []
        for slug in fw_modules:
            module_id = slug_to_id.get(slug)
            title = slug_to_title.get(slug, slug)
            if module_id and module_id in completed_module_ids:
                completed_fw.append({"slug": slug, "title": title, "completed": True})
            else:
                pending_fw.append({"slug": slug, "title": title, "completed": False})

        total = len(fw_modules)
        done = len(completed_fw)
        percent = round((done / total) * 100) if total > 0 else 0

        status = "compliant" if percent == 100 else "in_progress" if percent > 0 else "not_started"

        result.append({
            "id": fw_id,
            "name": fw["name"],
            "icon": fw["icon"],
            "colour": fw["colour"],
            "description": fw["description"],
            "percent": percent,
            "completed": done,
            "total": total,
            "status": status,
            "modules": completed_fw + pending_fw,
        })

    overall = round(sum(f["percent"] for f in result) / len(result)) if result else 0
    return {"frameworks": result, "overall_compliance": overall}
