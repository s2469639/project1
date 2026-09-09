무역 분석 대시보드 
사이드바에 국가 선택(셀렉트 박스), 무역액등급 선택(대,중,소) / 필터
baci_85_sample.csv 사용 -> columns: i,j,k,t,v 참고
country_codes_sample.csv 사용 -> columns: j,country_name 참고
한글 지원 (폰트 = title: '온글잎 윤탱체', 기타 본문: NanumGothic.ttf)
디자인: 메인 컬러 = 파스텔 초록, 부드럽고 가시성 좋은 파일. 내부 표 디자인은 심플.
현재 파일 경로: C:\Users\user\Desktop\project1
streamlit run data_country.py
경로 작성시 상대경로 pathlib 사용 

파일명: 'data_country.py'

1. 오른쪽 화면 st.title('무역 분석 대시보드')

2. baci_85_sample.csv 파일의 결측치

3. 총거래건수      총 수출액(미국 달러)

4. 국가*연도 수출액 히트맵(상위 8개국) 무역액 등급 분포

5. 상위 5개국 * 무역액 등급 교차표 
    원본건수        정규화비율