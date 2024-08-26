from flask import Flask, request, jsonify, render_template
import random
from shapely.geometry import Point
import geopandas as gpd

app = Flask(__name__)

# 대한민국 영역 Shapefile 경로
shapefile_path = "./sig.shp"

# DBF 파일의 인코딩을 확인한 후 올바른 인코딩을 사용하세요 (예: 'euc-kr')
encoding = 'euc-kr'

# Shapefile 읽어오기
gdf = gpd.read_file(shapefile_path, encoding=encoding)

# 좌표계(CRS) 설정
if gdf.crs is None:
    gdf.set_crs(epsg=5179, inplace=True)

# EPSG:4326으로 좌표계 변환
gdf = gdf.to_crs(epsg=4326)

# 시/도 맵핑
sigungu_map = {
    '11': "서울특별시",
    '26': "부산광역시",
    '27': "대구광역시",
    '28': "인천광역시",
    '29': "광주광역시",
    '30': "대전광역시",
    '31': "울산광역시",
    '41': "경기도",
    '43': "충청북도",
    '44': "충청남도",
    '45': "전라북도",
    '46': "전라남도",
    '47': "경상북도",
    '48': "경상남도",
    '50': "제주도",
    '51': "강원도"
}

@app.route('/')
def index():
    return render_template('index.html', sigungu_map=sigungu_map)

@app.route('/generate', methods=['POST'])
def generate():
    excluded_codes = request.json.get('excluded_codes', [])

    # 유효한 코드만 필터링
    excluded_codes = [code for code in excluded_codes if code in sigungu_map]

    # 모든 시/도 코드와 제외된 시/도 코드의 집합을 생성
    all_codes = set(sigungu_map.keys())
    remaining_codes = all_codes - set(excluded_codes)

    if not remaining_codes:
        return jsonify({"message": "여행 가능한 구역이 없습니다.", "regions": []})

    # 제외된 포인트를 저장할 리스트
    excluded_points = []
    selected_points = set()  # 선택된 포인트를 저장할 집합

    # 랜덤 포인트 생성 함수
    def generate_random_point_within_korea():
        within_korea = False
        point = None
        attempts = 0
        max_attempts = 100

        while not within_korea and attempts < max_attempts:
            attempts += 1
            latitude = round(random.uniform(33.091, 38.614), 3)
            longitude = round(random.uniform(124.511, 131.874), 3)
            point = Point(longitude, latitude)
            for index, row in gdf.iterrows():
                polygon = row['geometry']
                if point.within(polygon):
                    sig_cd = row['SIG_CD']
                    region = row['SIG_KOR_NM']
                    sigungu = sigungu_map.get(sig_cd[:2], "")
                    if sigungu and sig_cd[:2] in excluded_codes:
                        excluded_points.append(f"{sigungu} {region}")
                    elif sigungu and sig_cd[:2] not in excluded_codes:
                        full_region = f"{sigungu} {region}" if sigungu else region
                        return point, sig_cd, full_region
        return None, None, None

    # 랜덤한 지역을 20개까지 찾기 위해 반복
    while len(selected_points) < 20:
        point, sig_cd, full_region = generate_random_point_within_korea()
        if point and full_region:
            selected_points.add(full_region)

    if selected_points:
        return jsonify({"message": "당첨 지역:", "regions": list(selected_points)})
    else:
        return jsonify({"message": "당첨 지역을 찾을 수 없습니다.", "regions": []})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

