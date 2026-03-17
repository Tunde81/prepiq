from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.user import LearningModule, Lesson
import zipfile
import io
import re

router = APIRouter()

def parse_imsmanifest(xml_content: str) -> dict:
    from lxml import etree
    try:
        root = etree.fromstring(xml_content.encode())
        ns = {
            'imscp': 'http://www.imsproject.org/xsd/imscp_rootv1p1p2',
            'adlcp': 'http://www.adlnet.org/xsd/adlcp_rootv1p2',
        }
        # Try to get title
        title = "Imported Course"
        title_el = root.find('.//{http://www.imsproject.org/xsd/imscp_rootv1p1p2}title')
        if title_el is None:
            title_el = root.find('.//title')
        if title_el is not None and title_el.text:
            title = title_el.text.strip()

        # Get items (lessons)
        items = []
        for item in root.iter('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}item'):
            item_title = item.find('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}title')
            if item_title is None:
                item_title = item.find('title')
            ref = item.get('identifierref', '')
            if item_title is not None and item_title.text and ref:
                items.append({
                    'title': item_title.text.strip(),
                    'ref': ref,
                })

        # Get resources
        resources = {}
        for res in root.iter('{http://www.imsproject.org/xsd/imscp_rootv1p1p2}resource'):
            res_id = res.get('identifier', '')
            href = res.get('href', '')
            if res_id and href:
                resources[res_id] = href

        return {'title': title, 'items': items, 'resources': resources}
    except Exception as e:
        # Fallback: try without namespace
        try:
            root = etree.fromstring(xml_content.encode())
            title_el = root.find('.//title')
            title = title_el.text.strip() if title_el is not None and title_el.text else "Imported Course"
            items = []
            for item in root.iter('item'):
                item_title = item.find('title')
                ref = item.get('identifierref', '')
                if item_title is not None and item_title.text and ref:
                    items.append({'title': item_title.text.strip(), 'ref': ref})
            resources = {}
            for res in root.iter('resource'):
                res_id = res.get('identifier', '')
                href = res.get('href', '')
                if res_id and href:
                    resources[res_id] = href
            return {'title': title, 'items': items, 'resources': resources}
        except:
            return {'title': 'Imported Course', 'items': [], 'resources': {}}


def extract_text_from_html(html_content: str) -> str:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove scripts and styles
    for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
        tag.decompose()
    text = soup.get_text(separator='\n', strip=True)
    # Clean up excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text[:5000]  # Limit content size


@router.post("/scorm")
async def import_scorm(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    if not file.filename.endswith('.zip'):
        raise HTTPException(400, "Please upload a SCORM .zip file")

    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(400, "File too large (max 50MB)")

    try:
        zf = zipfile.ZipFile(io.BytesIO(contents))
    except Exception:
        raise HTTPException(400, "Invalid zip file")

    # Find imsmanifest.xml
    manifest_path = None
    for name in zf.namelist():
        if name.endswith('imsmanifest.xml'):
            manifest_path = name
            break

    if not manifest_path:
        raise HTTPException(400, "No imsmanifest.xml found - not a valid SCORM package")

    manifest_xml = zf.read(manifest_path).decode('utf-8', errors='ignore')
    parsed = parse_imsmanifest(manifest_xml)

    title = parsed['title']
    slug = re.sub(r'[^a-z0-9-]', '', title.lower().replace(' ', '-'))[:80]

    # Check for duplicate slug
    existing = db.query(LearningModule).filter(LearningModule.slug == slug).first()
    if existing:
        slug = slug + '-imported'

    # Create module
    module = LearningModule(
        title=title,
        slug=slug,
        description=f"Imported from SCORM package: {file.filename}",
        category='technical',
        difficulty='intermediate',
        duration_minutes=30,
        order_index=0,
        is_published=False,
    )
    db.add(module)
    db.flush()

    # Create lessons from items
    lessons_created = 0
    base_dir = manifest_path.replace('imsmanifest.xml', '')

    if parsed['items']:
        for i, item in enumerate(parsed['items']):
            ref = item['ref']
            href = parsed['resources'].get(ref, '')
            content_text = f"## {item['title']}\n\nContent from SCORM package."

            if href:
                file_path = base_dir + href if base_dir else href
                # Try to find the file
                for zname in zf.namelist():
                    if zname.endswith(href) or zname == file_path:
                        try:
                            raw = zf.read(zname).decode('utf-8', errors='ignore')
                            extracted = extract_text_from_html(raw)
                            if extracted and len(extracted) > 50:
                                content_text = f"## {item['title']}\n\n{extracted}"
                        except:
                            pass
                        break

            lesson = Lesson(
                module_id=module.id,
                title=item['title'],
                content=content_text,
                order_index=i + 1,
            )
            db.add(lesson)
            lessons_created += 1
    else:
        # No items found - create one lesson per HTML file
        html_files = [n for n in zf.namelist() if n.endswith('.html') or n.endswith('.htm')]
        for i, html_file in enumerate(html_files[:10]):
            try:
                raw = zf.read(html_file).decode('utf-8', errors='ignore')
                extracted = extract_text_from_html(raw)
                lesson_title = html_file.split('/')[-1].replace('.html', '').replace('-', ' ').replace('_', ' ').title()
                lesson = Lesson(
                    module_id=module.id,
                    title=lesson_title,
                    content=f"## {lesson_title}\n\n{extracted}" if extracted else f"## {lesson_title}\n\nNo content extracted.",
                    order_index=i + 1,
                )
                db.add(lesson)
                lessons_created += 1
            except:
                continue

    db.commit()

    return {
        "message": "SCORM package imported successfully",
        "module_id": module.id,
        "module_title": title,
        "slug": slug,
        "lessons_created": lessons_created,
        "published": False,
    }
