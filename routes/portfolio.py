"""Public portfolio catalog and individual work pages."""
from flask import Blueprint, abort, render_template

portfolio_bp = Blueprint('portfolio', __name__)

WORKS = [
    dict(slug='mcdonalds-sns-concept', category='social', label='SNS · FOOD CONCEPT', status='비공식 콘셉트',
         image='showcase/mcdonalds-sns-concept.png', project='순금이 AI 작업실 · 자체 콘셉트',
         title='맥도날드 SNS · 한 입의 즐거움.',
         description='우리 홈페이지 SNS 기능으로 만든, 빨강 배경과 버거 중심의 비공식 콘셉트 홍보물입니다.',
         format='SNS 홍보 이미지 · 1080×1350',
         overview='맥도날드를 주제로 순금이 AI 작업실의 제작 스타일을 보여주는 자체 프로젝트입니다. 홈페이지 SNS 기능에 업종과 제작 브리프, 이미지 스타일을 입력해 문구와 이미지를 생성했습니다. 공식 의뢰·협업·캠페인이 아니며, 음식은 실제 판매 메뉴 사진이 아닌 AI 생성 이미지입니다.',
         approach='구도·색감·빛·음식 질감·타이포그래피 기준을 조합했습니다. 짙은 빨강 배경과 크게 배치한 버거, 짧은 흰색 제목을 중심으로 구성했습니다. 첫 결과의 글자 중복을 확인한 뒤, 글자 없는 사진층과 한글 조판을 분리하도록 입력을 수정했습니다. 최종 결과는 홈페이지에서 생성한 원본 그대로 공개합니다.',
         caption='맥도날드, 한 입에 번지는 가장 선명한 즐거움 🍔\n부드러운 참깨빵과 진한 패티, 녹아드는 치즈의 조화가 보는 순간부터 식욕을 깨워요.\n한 컷만으로도 버거의 맛있는 존재감을 또렷하게 전하는 인스타그램 콘셉트입니다.\n한 입의 즐거움을 담은 버거 무드가 필요하다면 맥도날드 관련 콘셉트도 함께 이야기해보세요.\n※ 본 캡션은 순금이 AI 작업실의 비공식 콘셉트이며 공식 의뢰·협업이 아닙니다.\n#맥도날드 #버거사진 #푸드스타일링 #푸드콘텐츠 #인스타감성 #버거콘셉트 #음식사진 #SNS콘텐츠 #한입의즐거움'),
    dict(slug='running-form-report', category='report', label='REPORT · RUNNING COACH', status='디자인 샘플',
         image='showcase/sungeum-running-report-studio.png',
         title='달리기를 한눈에, 러닝폼 리포트.',
         description='점수와 자세, 다음 러닝의 포인트를 한 장에 정리한 리포트 디자인입니다.',
         format='러닝 분석 리포트 · PNG',
         overview='순금이 러닝코치의 저장·공유 리포트를 작업실 홈페이지와 같은 스타일로 제작했습니다. 이 작업물의 점수와 각도는 디자인을 보여주기 위한 예시이며, 실제 이용자의 영상 분석 결과가 아닙니다. 분석 장면 역시 직접 그린 예시 일러스트입니다.',
         approach='흰 배경과 검정 글자, 청보라 강조색을 사용했습니다. 종합 점수, 자세 시각화와 착지 확대, 핵심 수치, 코칭 한마디를 차례로 배치했습니다. 실제 서비스에서는 이용자의 분석 장면과 결과가 들어가며, 같은 이미지를 다운로드하고 생성 기록에 저장합니다.'),
    dict(slug='7days-massage-sns', category='social', label='SNS · LOCAL BUSINESS', status='실제 게시',
         image='showcase/7days-massage-pattaya-sns.png', project="7day’s massage",
         title='7day’s massage · SNS 홍보',
         description='파타야 마사지샵을 위해 만든, 편안한 휴식 분위기의 SNS 홍보 이미지입니다.',
         format='SNS 홍보 이미지',
         overview='7day’s massage의 인스타그램 홍보를 위해 제작한 작업물입니다. 여행과 쇼핑 중 잠시 쉬어가는 장면을 AI 이미지로 표현했습니다.',
         approach='따뜻한 나무색과 자연광, 초록 식물을 활용해 편안한 분위기를 구성했습니다. 매장 이름이 먼저 읽히도록 중앙에 배치했습니다.',
         caption='파타야 터미널21에서 많이 걷고 난 뒤,\n잠시 편안하게 쉬어가세요. 🌿\n\n쇼핑과 관광으로 쌓인 피로를 가볍게 풀고 나면\n남은 여행 일정도 한층 여유로워집니다.'),
    dict(slug='conversion-ad', category='social', label='AD · VISUAL DIRECTION', status='자체 프로젝트',
         image='showcase/project-freedom-conversion-ad-v1.png',
         title='눈길에서, 다음 행동으로.',
         description='선명한 색과 큰 제목으로 콘텐츠 제작 기능을 소개하는 광고 디자인입니다.',
         format='디지털 광고 이미지',
         overview='한 번의 입력으로 여러 종류의 홍보물을 만들 수 있다는 메시지를 담았습니다. SNS, 광고, 블로그, 포스터 예시를 한 화면에 보여줍니다.',
         approach='파랑과 노랑의 대비로 주요 메시지를 강조하고, 하단에 제작 예시를 나란히 배치했습니다.'),
    dict(slug='brand-poster', category='brand', label='BRAND · POSTER', status='자체 프로젝트',
         image='showcase/project-freedom-poster-v4.png',
         title='한눈에 읽히는, 브랜드의 목소리.',
         description='검정과 빨강, 큰 글자로 정리한 Project Freedom AI의 브랜드 홍보 포스터입니다.',
         format='브랜드 포스터',
         overview='여러 홍보물 제작 기능을 한곳에서 이용할 수 있다는 메시지를 전달하는 브랜드 포스터입니다.',
         approach='어두운 바탕 위에 큰 제목을 배치하고, 네 가지 제작 분야를 구분했습니다. 빨간 면과 흰 글자로 읽는 순서를 만들었습니다.'),
    dict(slug='ai-studio-website', category='web', label='WEB · UI', status='자체 프로젝트',
         image='showcase/ai-studio-homepage-v4.png',
         title='작업물이 먼저 보이는 홈페이지.',
         description='실제 결과물과 AI 도구를 둘러볼 수 있도록 구성한 순금이의 AI 작업실입니다.',
         format='반응형 홈페이지',
         overview='어떤 콘텐츠를 만드는 곳인지 첫 화면에서 알 수 있도록 작업물을 앞에 배치한 홈페이지 시안입니다.',
         approach='흰 배경과 검정 글자를 중심으로 작업물, 제작 과정, AI 도구를 구분했습니다. 데스크톱과 모바일 크기에 맞춰 카드 배열을 조정했습니다.'),
]


@portfolio_bp.get('/works/<slug>')
def detail(slug):
    work = next((item for item in WORKS if item['slug'] == slug), None)
    if work is None:
        abort(404)
    return render_template('work_detail.html', work=work,
                           related=[item for item in WORKS if item['slug'] != slug])
