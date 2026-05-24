from flask import Blueprint, request, jsonify
from app import db
from app.models import User, PointLog, Item, Purchase, ServiceRequest, WhisperLink, Notice, ApiKey, Collection, Document
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import json
from datetime import datetime

main = Blueprint('main', __name__)

# ── 회원가입 ──
@main.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': '이미 존재하는 이름입니다'}), 400

    user = User(
        username=data['username'],
        password_hash=generate_password_hash(data['password']),
        email=data.get('email'),
        role='student'
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': '회원가입 완료'}), 201

# ── 로그인 ──
@main.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': '이름 또는 비밀번호가 틀렸습니다'}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({'token': token, 'role': user.role, 'username': user.username})

# ── 내 정보 조회 ──
@main.route('/api/me', methods=['GET'])
@jwt_required()
def me():
    user = User.query.get(int(get_jwt_identity()))
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'point_balance': user.point_balance,
        'role': user.role
    })

# ── 포인트 지급/차감 (운영자만) ──
@main.route('/api/admin/points', methods=['POST'])
@jwt_required()
def adjust_points():
    admin = User.query.get(int(get_jwt_identity()))
    if admin.role != 'admin':
        return jsonify({'error': '권한 없음'}), 403

    data = request.json
    if not data.get('reason', '').strip():
        return jsonify({'error': '사유는 필수입니다'}), 400

    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'error': '사용자 없음'}), 404

    new_balance = user.point_balance + data['amount']
    if new_balance < 0:
        return jsonify({'error': '포인트가 부족합니다'}), 400

    user.point_balance = new_balance
    log = PointLog(
        user_id=user.id,
        admin_id=admin.id,
        amount=data['amount'],
        type='grant' if data['amount'] > 0 else 'deduct',
        reason=data['reason']
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({'new_balance': new_balance})

# ── 상품 목록 조회 ──
@main.route('/api/items', methods=['GET'])
@jwt_required()
def get_items():
    items = Item.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': i.id, 'name': i.name,
        'description': i.description,
        'price': i.price, 'stock': i.stock
    } for i in items])

# ── 상품 추가 (운영자만) ──
@main.route('/api/admin/items', methods=['POST'])
@jwt_required()
def add_item():
    admin = User.query.get(int(get_jwt_identity()))
    if admin.role != 'admin':
        return jsonify({'error': '권한 없음'}), 403

    data = request.json
    item = Item(
        name=data['name'],
        description=data.get('description'),
        price=data['price'],
        stock=data['stock']
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'message': '상품 추가 완료', 'id': item.id}), 201

# ── 제작 요청 ──
@main.route('/api/requests', methods=['POST'])
@jwt_required()
def create_request():
    user_id = int(get_jwt_identity())
    data = request.json
    unique_code = f"REQ-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

    req = ServiceRequest(
        user_id=user_id,
        unique_code=unique_code,
        title=data['title'],
        description=data.get('description')
    )
    db.session.add(req)
    db.session.commit()
    return jsonify({'message': '요청 완료', 'unique_code': unique_code}), 201

# ── 귓속말 링크 생성 (운영자만) ──
@main.route('/api/admin/whisper', methods=['POST'])
@jwt_required()
def create_whisper():
    admin = User.query.get(int(get_jwt_identity()))
    if admin.role != 'admin':
        return jsonify({'error': '권한 없음'}), 403

    data = request.json
    token = str(uuid.uuid4())
    whisper = WhisperLink(
        token=token,
        admin_id=admin.id,
        user_id=data['user_id'],
        message=data['message']
    )
    db.session.add(whisper)
    db.session.commit()
    return jsonify({'url': f"/whisper?token={token}"})

# ── 귓속말 읽기 ──
@main.route('/api/whisper/<token>', methods=['GET'])
@jwt_required()
def read_whisper(token):
    link = WhisperLink.query.filter_by(token=token).first()
    if not link:
        return jsonify({'error': '유효하지 않은 링크'}), 404

    link.is_read = True
    db.session.commit()
    return jsonify({'message': link.message})

# ── 공지사항 등록 (운영자만) ──
@main.route('/api/admin/notices', methods=['POST'])
@jwt_required()
def create_notice():
    admin = User.query.get(int(get_jwt_identity()))
    if admin.role != 'admin':
        return jsonify({'error': '권한 없음'}), 403

    data = request.json
    notice = Notice(
        admin_id=admin.id,
        title=data['title'],
        content=data['content'],
        is_pinned=data.get('is_pinned', False)
    )
    db.session.add(notice)
    db.session.commit()
    return jsonify({'message': '공지 등록 완료'}), 201

# ── 공지사항 목록 ──
@main.route('/api/notices', methods=['GET'])
@jwt_required()
def get_notices():
    notices = Notice.query.order_by(Notice.is_pinned.desc(), Notice.created_at.desc()).all()
    return jsonify([{
        'id': n.id, 'title': n.title,
        'content': n.content, 'is_pinned': n.is_pinned,
        'created_at': n.created_at.isoformat()
    } for n in notices])
# ── API 키 발급 ──
@main.route('/api/apikey/generate', methods=['POST'])
@jwt_required()
def generate_api_key():
    user_id = int(get_jwt_identity())
    
    # 기존 키 비활성화
    existing = ApiKey.query.filter_by(user_id=user_id, is_active=True).first()
    if existing:
        existing.is_active = False
        db.session.commit()

    # 새 키 생성
    new_key = 'AIZAMA-' + str(uuid.uuid4()).replace('-', '').upper()[:32]
    api_key = ApiKey(user_id=user_id, key=new_key)
    db.session.add(api_key)
    db.session.commit()

    return jsonify({'api_key': new_key})

# ── API 키 조회 ──
@main.route('/api/apikey', methods=['GET'])
@jwt_required()
def get_api_key():
    user_id = int(get_jwt_identity())
    key = ApiKey.query.filter_by(user_id=user_id, is_active=True).first()
    if not key:
        return jsonify({'error': 'API 키 없음'}), 404
    return jsonify({'api_key': key.key})
import json

# ── API 키 인증 헬퍼 ──
def get_api_key_from_header():
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return None
    return ApiKey.query.filter_by(key=api_key, is_active=True).first()

# ── 컬렉션 전체 조회 ──
@main.route('/api/db/<collection_name>', methods=['GET'])
def db_get(collection_name):
    key = get_api_key_from_header()
    if not key:
        return jsonify({'error': 'API 키 없음'}), 401

    collection = Collection.query.filter_by(
        name=collection_name, api_key_id=key.id
    ).first()

    if not collection:
        return jsonify([])

    docs = Document.query.filter_by(collection_id=collection.id).all()
    return jsonify([{
        'id': d.doc_id,
        'data': json.loads(d.data),
        'created_at': d.created_at.isoformat()
    } for d in docs])

# ── 문서 저장 ──
@main.route('/api/db/<collection_name>', methods=['POST'])
def db_set(collection_name):
    key = get_api_key_from_header()
    if not key:
        return jsonify({'error': 'API 키 없음'}), 401

    data = request.json

    # 컬렉션 없으면 자동 생성
    collection = Collection.query.filter_by(
        name=collection_name, api_key_id=key.id
    ).first()
    if not collection:
        collection = Collection(name=collection_name, api_key_id=key.id)
        db.session.add(collection)
        db.session.flush()

    doc_id = str(uuid.uuid4())[:8].upper()
    doc = Document(
        collection_id=collection.id,
        doc_id=doc_id,
        data=json.dumps(data, ensure_ascii=False)
    )
    db.session.add(doc)
    db.session.commit()

    return jsonify({'id': doc_id, 'data': data}), 201

# ── 문서 수정 ──
@main.route('/api/db/<collection_name>/<doc_id>', methods=['PUT'])
def db_update(collection_name, doc_id):
    key = get_api_key_from_header()
    if not key:
        return jsonify({'error': 'API 키 없음'}), 401

    collection = Collection.query.filter_by(
        name=collection_name, api_key_id=key.id
    ).first()
    if not collection:
        return jsonify({'error': '컬렉션 없음'}), 404

    doc = Document.query.filter_by(
        collection_id=collection.id, doc_id=doc_id
    ).first()
    if not doc:
        return jsonify({'error': '문서 없음'}), 404

    doc.data = json.dumps(request.json, ensure_ascii=False)
    db.session.commit()
    return jsonify({'id': doc_id, 'data': request.json})

# ── 문서 삭제 ──
@main.route('/api/db/<collection_name>/<doc_id>', methods=['DELETE'])
def db_delete(collection_name, doc_id):
    key = get_api_key_from_header()
    if not key:
        return jsonify({'error': 'API 키 없음'}), 401

    collection = Collection.query.filter_by(
        name=collection_name, api_key_id=key.id
    ).first()
    if not collection:
        return jsonify({'error': '컬렉션 없음'}), 404

    doc = Document.query.filter_by(
        collection_id=collection.id, doc_id=doc_id
    ).first()
    if not doc:
        return jsonify({'error': '문서 없음'}), 404

    db.session.delete(doc)
    db.session.commit()
    return jsonify({'message': '삭제 완료'})