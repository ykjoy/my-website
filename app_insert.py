"""
MyStore Analytics
소상공인을 위한 음반 매출 인사이트 대시보드
실행: streamlit run app.py
"""
import sqlite3, os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as gobj

st.set_page_config(page_title="MyStore Analytics", layout="wide", initial_sidebar_state="collapsed")

DB_PATH   = "chinook.db"
BLUE      = "#1D8FF2"
BLUE_DARK = "#0D5DB5"
GRAY      = "#6B7280"
SUCCESS   = "#10B981"
WARNING   = "#F59E0B"
DANGER    = "#EF4444"
PURPLE    = "#7C3AED"
PALETTE   = [BLUE, PURPLE, WARNING, SUCCESS, DANGER, "#06B6D4", "#EC4899", "#84CC16", "#F97316", "#6366F1"]
PFONT     = dict(family="Pretendard, Noto Sans KR, Malgun Gothic, sans-serif", size=12)

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
[data-testid="stAppViewContainer"]{background:linear-gradient(160deg,#EBF4FF 0%,#DBEAFE 40%,#F0F9FF 100%);font-family:'Pretendard','Noto Sans KR',sans-serif;}
[data-testid="stHeader"]{background:transparent;}[data-testid="stSidebar"]{display:none;}
.hero{background:linear-gradient(135deg,#1D8FF2 0%,#0D5DB5 100%);border-radius:28px;padding:40px 48px;color:white;box-shadow:0 8px 32px rgba(29,143,242,.25);margin-bottom:28px;}
.hero h1{font-size:2rem;font-weight:800;margin:0 0 6px;letter-spacing:-0.5px;}.hero p{font-size:.95rem;opacity:.85;margin:0;}
.tag-label{font-size:.85rem;font-weight:700;color:#1D3557;margin-bottom:8px;margin-top:4px;}
.insight-card{background:white;border-radius:20px;padding:24px 26px;box-shadow:0 3px 18px rgba(29,143,242,.09);border-left:5px solid #1D8FF2;margin-bottom:12px;}
.insight-card h3{font-size:1.05rem;font-weight:700;color:#1D3557;margin:0 0 6px;}.insight-card p{font-size:.82rem;color:#6B7280;margin:0;}
.kpi{background:white;border-radius:18px;padding:20px 22px;box-shadow:0 2px 14px rgba(29,143,242,.08);}
.kpi .lbl{font-size:.75rem;color:#6B7280;font-weight:500;margin-bottom:4px;}.kpi .val{font-size:1.65rem;font-weight:800;color:#1D3557;line-height:1;}.kpi .dlt{font-size:.75rem;margin-top:5px;font-weight:600;}
.up{color:#10B981;}.down{color:#EF4444;}.flat{color:#6B7280;}
.sec{font-size:1rem;font-weight:700;color:#1D3557;border-left:4px solid #1D8FF2;padding-left:10px;margin:24px 0 12px;}
.conclusion{background:linear-gradient(135deg,#EBF4FF,#DBEAFE);border-radius:16px;padding:20px 24px;border-left:5px solid #1D8FF2;margin-top:20px;}
.conclusion h4{font-size:.95rem;font-weight:700;color:#0D5DB5;margin:0 0 8px;}.conclusion p{font-size:.85rem;color:#1D3557;margin:0;line-height:1.7;}
.back>button{background:white!important;color:#1D8FF2!important;border:2px solid #1D8FF2!important;border-radius:12px!important;font-weight:600!important;font-size:.85rem!important;}
.stButton>button{border-radius:14px;font-family:'Pretendard',sans-serif;font-weight:600;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#1D8FF2,#0D5DB5)!important;color:white!important;}
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "home"

def go(p):
    st.session_state.page = p
    st.rerun()

@st.cache_data(show_spinner=False)
def load():
    if not os.path.exists(DB_PATH): return None
    conn = sqlite3.connect(DB_PATH)
    try:
        inv = pd.read_sql("""
            SELECT i.InvoiceId, i.CustomerId, i.InvoiceDate,
                   i.BillingCountry AS Country, i.Total,
                   c.FirstName||' '||c.LastName AS CustomerName,
                   e.FirstName||' '||e.LastName AS SalesRep
            FROM invoices i
            LEFT JOIN customers c ON i.CustomerId=c.CustomerId
            LEFT JOIN employees e ON c.SupportRepId=e.EmployeeId
        """, conn)
        inv["InvoiceDate"] = pd.to_datetime(inv["InvoiceDate"])
        inv["Year"] = inv["InvoiceDate"].dt.year
        inv["Month"] = inv["InvoiceDate"].dt.month
        inv["YM"] = inv["InvoiceDate"].dt.to_period("M").astype(str)
        items = pd.read_sql("""
            SELECT ii.InvoiceId, ii.Quantity, (ii.UnitPrice*ii.Quantity) AS LineTotal,
                   t.Name AS Track, g.Name AS Genre, al.Title AS Album, ar.Name AS Artist,
                   i.BillingCountry AS Country, i.InvoiceDate, i.Total
            FROM invoice_items ii
            JOIN tracks t ON ii.TrackId=t.TrackId JOIN genres g ON t.GenreId=g.GenreId
            JOIN albums al ON t.AlbumId=al.AlbumId JOIN artists ar ON al.ArtistId=ar.ArtistId
            JOIN invoices i ON ii.InvoiceId=i.InvoiceId
        """, conn)
        items["InvoiceDate"] = pd.to_datetime(items["InvoiceDate"])
        items["Year"] = items["InvoiceDate"].dt.year
        items["Month"] = items["InvoiceDate"].dt.month
        return {"inv": inv, "items": items}
    finally:
        conn.close()

def fmt(v): return f"${v:,.2f}"
def kpi(label, value, delta="", cls="flat"):
    st.markdown(f'<div class="kpi"><div class="lbl">{label}</div><div class="val">{value}</div><div class="dlt {cls}">{delta}</div></div>', unsafe_allow_html=True)
def sec(t): st.markdown(f'<div class="sec">{t}</div>', unsafe_allow_html=True)
def sfig(fig, h=380):
    fig.update_layout(font=PFONT, height=h, margin=dict(l=10,r=10,t=40,b=10), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig
def conclusion(title, body):
    st.markdown(f'<div class="conclusion"><h4>인사이트: {title}</h4><p>{body}</p></div>', unsafe_allow_html=True)
def back():
    st.markdown('<div class="back">', unsafe_allow_html=True)
    if st.button("← 홈으로"): go("home")
    st.markdown('</div>', unsafe_allow_html=True)

def page_home():
    st.markdown('<div class="hero"><h1>MyStore Analytics</h1><p>내 음반 가게, 데이터로 더 스마트하게 — 분석부터 예측까지</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="tag-label">어떤 분석이 필요하신가요? (복수 선택 가능)</div>', unsafe_allow_html=True)
    tags = st.multiselect(label="태그", options=["지역","장르","아티스트","시즌","예측","영업사원"],
                          default=[], placeholder="태그를 선택하면 추천 포트폴리오가 나타납니다", label_visibility="collapsed")
    ALL_CARDS = ["where","what","when","salesrep","loyalty","season"]
    show = {k: False for k in ALL_CARDS}
    if not tags:
        show = {k: True for k in ALL_CARDS}
    else:
        if "지역" in tags or "장르" in tags: show["where"] = True
        if "아티스트" in tags: show["what"] = True; show["loyalty"] = True
        if "시즌" in tags or "예측" in tags: show["when"] = True; show["season"] = True
        if "영업사원" in tags: show["salesrep"] = True
    card_info = {
        "where":    ("어디에 팔까?",       "국가 × 장르 교차 분석으로 지역별 납품 전략을 도출합니다.",         "insight_where"),
        "what":     ("무엇을 팔까?",        "아티스트별 매출·판매량·지역 분포로 발주 우선순위를 파악합니다.",    "insight_what"),
        "when":     ("언제 팔까?",          "월별 시즌 패턴과 선형회귀 예측으로 프로모션 타이밍을 제안합니다.", "insight_when"),
        "salesrep": ("영업사원 포트폴리오", "장르 집중도·매출 안정성·고객 다양성을 비교 분석합니다.",           "insight_salesrep"),
        "loyalty":  ("아티스트 충성도",     "반복 구매 비율로 국가별 아티스트 팬덤 강도를 측정합니다.",         "insight_loyalty"),
        "season":   ("장르 시즌 패턴",      "계절성 지수(SI)와 변동계수(CV)로 시즌 효과를 분석합니다.",         "insight_season"),
    }
    active = [k for k in ALL_CARDS if show[k]]
    if active:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="tag-label">추천 포트폴리오</div>', unsafe_allow_html=True)
        for row_start in range(0, len(active), 3):
            row_keys = active[row_start:row_start+3]
            grid = st.columns(len(row_keys), gap="large")
            for col, key in zip(grid, row_keys):
                title, desc, page_key = card_info[key]
                with col:
                    st.markdown(f'<div class="insight-card"><h3>{title}</h3><p>{desc}</p></div>', unsafe_allow_html=True)
                    if st.button("분석 보기", key=f"btn_{key}"): go(page_key)
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="tag-label">운영 도구</div>', unsafe_allow_html=True)
    oc1, oc2 = st.columns(2, gap="large")
    with oc1:
        st.markdown('<div class="insight-card" style="border-left-color:#7C3AED;"><h3>고객 관리</h3><p>고객 조회 · 추가 · 수정 · 삭제</p></div>', unsafe_allow_html=True)
        if st.button("바로가기", key="btn_customer"): go("customer")
    with oc2:
        st.markdown('<div class="insight-card" style="border-left-color:#10B981;"><h3>사원 현황</h3><p>직원 정보 및 담당 매출 성과</p></div>', unsafe_allow_html=True)
        if st.button("바로가기", key="btn_employee"): go("employee")
    st.markdown(f'<p style="text-align:center;color:{GRAY};font-size:.75rem;margin-top:32px;">Chinook Music Store · 2009–2013</p>', unsafe_allow_html=True)

def page_where(data):
    back()
    st.markdown('<div style="font-size:1.6rem;font-weight:800;color:#1D3557;">어디에 팔까?</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#6B7280;font-size:.85rem;margin-bottom:20px;">국가 x 장르 교차 분석 - 지역별 납품 전략</div>', unsafe_allow_html=True)
    items = data["items"]
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1: sel_years = st.slider("연도 범위", 2009, 2013, (2009, 2013), key="where_year")
    with col_f2: sel_country = st.multiselect("국가 필터", sorted(items["Country"].dropna().unique()), default=[], placeholder="전체 국가", key="where_country")
    with col_f3: sel_genre = st.multiselect("장르 필터", sorted(items["Genre"].dropna().unique()), default=[], placeholder="전체 장르", key="where_genre")
    fi = items[(items["Year"] >= sel_years[0]) & (items["Year"] <= sel_years[1])]
    if sel_country: fi = fi[fi["Country"].isin(sel_country)]
    if sel_genre:   fi = fi[fi["Genre"].isin(sel_genre)]
    year_label = f"{sel_years[0]}-{sel_years[1]}년"
    if fi.empty: st.warning("선택한 조건에 해당하는 데이터가 없습니다."); return
    st.caption(f"현재 조회 기간: {year_label}")
    cross = fi.groupby(["Country","Genre"])["LineTotal"].sum().reset_index()
    pivot = cross.pivot(index="Country", columns="Genre", values="LineTotal").fillna(0)
    sec("국가 x 장르 매출 히트맵")
    fig_h = gobj.Figure(gobj.Heatmap(z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale="Blues", hovertemplate="<b>%{y}</b><br>%{x}<br>$%{z:,.2f}<extra></extra>", colorbar=dict(title="매출 ($)")))
    fig_h.update_layout(title="국가별 장르 매출 히트맵", xaxis=dict(tickangle=-40), yaxis=dict(autorange="reversed"))
    st.plotly_chart(sfig(fig_h, 480), use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        sec("국가별 매출 Top 10")
        cr = fi.groupby("Country")["LineTotal"].sum().reset_index().sort_values("LineTotal", ascending=False).head(10)
        fig_c = px.bar(cr.sort_values("LineTotal"), x="LineTotal", y="Country", orientation="h",
                       color="LineTotal", color_continuous_scale="Blues",
                       text=cr.sort_values("LineTotal")["LineTotal"].apply(lambda v: f"${v:,.0f}"),
                       labels={"LineTotal":"매출 ($)","Country":""})
        fig_c.update_traces(textposition="outside"); fig_c.update_layout(coloraxis_showscale=False)
        st.plotly_chart(sfig(fig_c, 380), use_container_width=True)
    with col2:
        sec("장르별 국가 분포 (Top 5 장르)")
        top5g = fi.groupby("Genre")["LineTotal"].sum().nlargest(5).index.tolist()
        gdf = fi[fi["Genre"].isin(top5g)].groupby(["Genre","Country"])["LineTotal"].sum().reset_index()
        fig_s = px.sunburst(gdf, path=["Genre","Country"], values="LineTotal", color="LineTotal", color_continuous_scale="Blues")
        fig_s.update_layout(title="장르 -> 국가 분포")
        st.plotly_chart(sfig(fig_s, 380), use_container_width=True)
    sec("국가별 베스트 장르 요약")
    best = cross.loc[cross.groupby("Country")["LineTotal"].idxmax()].sort_values("LineTotal", ascending=False).copy()
    best.columns = ["국가","베스트 장르","매출"]; best["매출"] = best["매출"].apply(fmt)
    st.dataframe(best, use_container_width=True, height=300, hide_index=True)
    cr2 = fi.groupby("Country")["LineTotal"].sum().reset_index().sort_values("LineTotal", ascending=False)
    top_country = cr2.iloc[0]["Country"] if not cr2.empty else "-"
    top_genre_overall = fi.groupby("Genre")["LineTotal"].sum().idxmax() if not fi.empty else "-"
    conclusion("지역별 납품 전략",
        f"조회 기간 {year_label} 기준, 매출 1위 국가는 <b>{top_country}</b>이며, "
        f"전체적으로 <b>{top_genre_overall}</b> 장르가 가장 높은 매출을 기록했습니다. "
        f"히트맵에서 각 국가의 선호 장르가 뚜렷하게 구분되므로 <b>국가별 맞춤 장르 납품 전략</b>이 효과적입니다.")

def page_what(data):
    back()
    st.markdown('<div style="font-size:1.6rem;font-weight:800;color:#1D3557;">무엇을 팔까?</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#6B7280;font-size:.85rem;margin-bottom:20px;">아티스트 성과 분석 - 발주 우선순위</div>', unsafe_allow_html=True)
    items = data["items"]
    col_f1, col_f2 = st.columns(2)
    with col_f1: sel_years = st.slider("연도 범위", 2009, 2013, (2009, 2013), key="what_year")
    with col_f2: sel_country = st.multiselect("국가 필터", sorted(items["Country"].dropna().unique()), default=[], placeholder="전체 국가", key="what_country")
    fi = items[(items["Year"] >= sel_years[0]) & (items["Year"] <= sel_years[1])]
    if sel_country: fi = fi[fi["Country"].isin(sel_country)]
    year_label = f"{sel_years[0]}-{sel_years[1]}년"
    if fi.empty: st.warning("선택한 조건에 해당하는 데이터가 없습니다."); return
    st.caption(f"현재 조회 기간: {year_label}")
    ar = fi.groupby("Artist").agg(매출=("LineTotal","sum"), 판매량=("Quantity","sum"), 국가수=("Country","nunique")).reset_index().sort_values("매출", ascending=False)
    sec("핵심 지표")
    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi("전체 아티스트 수", f"{len(ar):,}팀")
    with k2: kpi("1위 아티스트", ar.iloc[0]["Artist"], f"매출 {fmt(ar.iloc[0]['매출'])}", "up")
    with k3: kpi("총 판매량", f"{ar['판매량'].sum():,}곡")
    with k4: kpi("평균 아티스트 매출", fmt(ar["매출"].mean()))
    col1, col2 = st.columns([3,2])
    with col1:
        sec("아티스트별 매출 Top 15")
        top15 = ar.head(15).sort_values("매출")
        fig_a = px.bar(top15, x="매출", y="Artist", orientation="h", color="매출", color_continuous_scale="Blues",
                       text=top15["매출"].apply(lambda v: f"${v:,.0f}"), labels={"매출":"매출 ($)","Artist":""})
        fig_a.update_traces(textposition="outside"); fig_a.update_layout(coloraxis_showscale=False)
        st.plotly_chart(sfig(fig_a, 500), use_container_width=True)
    with col2:
        sec("매출 vs 판매량 분포")
        fig_sc = px.scatter(ar.head(30), x="판매량", y="매출", size="매출", color="국가수",
                            hover_name="Artist", color_continuous_scale="Blues", size_max=40,
                            labels={"판매량":"판매량 (곡)","매출":"매출 ($)","국가수":"판매 국가 수"})
        fig_sc.update_layout(title="상위 30 아티스트")
        st.plotly_chart(sfig(fig_sc, 500), use_container_width=True)
    sec("아티스트별 국가 매출 분포 (Top 10)")
    top10_artists = ar.head(10)["Artist"].tolist()
    ac = fi[fi["Artist"].isin(top10_artists)].groupby(["Artist","Country"])["LineTotal"].sum().reset_index()
    piv = ac.pivot(index="Artist", columns="Country", values="LineTotal").fillna(0)
    fig_ah = gobj.Figure(gobj.Heatmap(z=piv.values, x=piv.columns.tolist(), y=piv.index.tolist(),
        colorscale="Purples", hovertemplate="<b>%{y}</b><br>%{x}<br>$%{z:,.2f}<extra></extra>"))
    fig_ah.update_layout(title="아티스트 x 국가 매출", xaxis=dict(tickangle=-40))
    st.plotly_chart(sfig(fig_ah, 420), use_container_width=True)
    sec("Top 5 아티스트 연도별 매출 추이")
    top5a = ar.head(5)["Artist"].tolist()
    tr = fi[fi["Artist"].isin(top5a)].groupby(["Year","Artist"])["LineTotal"].sum().reset_index()
    fig_tr = px.line(tr, x="Year", y="LineTotal", color="Artist", markers=True,
                     color_discrete_sequence=PALETTE, labels={"LineTotal":"매출 ($)","Year":"연도"})
    fig_tr.update_layout(xaxis=dict(dtick=1), hovermode="x unified")
    st.plotly_chart(sfig(fig_tr, 360), use_container_width=True)
    top1 = ar.iloc[0]["Artist"]
    top1_df = fi[fi["Artist"]==top1].groupby("Country")["LineTotal"].sum()
    top1_countries = top1_df.idxmax() if not top1_df.empty else "-"
    conclusion("발주 우선순위 전략",
        f"조회 기간 {year_label} 기준, 매출 1위 아티스트는 <b>{top1}</b>으로 특히 <b>{top1_countries}</b>에서 강세를 보입니다. "
        f"매출과 판매량이 모두 높은 아티스트를 우선 발주하고, 국가별 히트맵을 참고해 <b>아티스트별 타겟 국가 납품 전략</b>을 수립하세요.")

def page_when(data):
    back()
    st.markdown('<div style="font-size:1.6rem;font-weight:800;color:#1D3557;">언제 팔까?</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#6B7280;font-size:.85rem;margin-bottom:20px;">시즌 패턴 분석 + 2014년 매출 예측</div>', unsafe_allow_html=True)
    inv = data["inv"]
    monthly = inv.groupby("Month")["Total"].mean().reset_index()
    monthly["월"] = monthly["Month"].apply(lambda m: f"{m}월")
    monthly_max = monthly["Total"].max(); monthly_min = monthly["Total"].min()
    sec("월별 매출 패턴 (2009-2013 평균)")
    fig_m = gobj.Figure()
    fig_m.add_trace(gobj.Bar(x=monthly["월"], y=monthly["Total"],
        marker=dict(color=[WARNING if v==monthly_max else (DANGER if v==monthly_min else BLUE) for v in monthly["Total"]], opacity=0.85),
        text=monthly["Total"].apply(lambda v: f"${v:,.0f}"), textposition="outside"))
    fig_m.update_layout(title="월별 평균 매출 (노란색=성수기 / 빨간색=비수기)")
    st.plotly_chart(sfig(fig_m, 360), use_container_width=True)
    peak_month = monthly.loc[monthly["Total"].idxmax(), "월"]
    trough_month = monthly.loc[monthly["Total"].idxmin(), "월"]
    k1, k2, k3 = st.columns(3)
    with k1: kpi("성수기", peak_month, "평균 매출 최고", "up")
    with k2: kpi("비수기", trough_month, "평균 매출 최저", "down")
    with k3: kpi("성비수기 차이", fmt(monthly_max-monthly_min), "프로모션 여지", "flat")
    sec("연도 x 월 매출 히트맵")
    hm = inv.groupby(["Year","Month"])["Total"].sum().reset_index()
    piv = hm.pivot(index="Year", columns="Month", values="Total").fillna(0)
    for m in range(1,13):
        if m not in piv.columns: piv[m] = 0
    piv = piv[sorted(piv.columns)]
    fig_hm = gobj.Figure(gobj.Heatmap(z=piv.values, x=[f"{m}월" for m in piv.columns], y=piv.index,
        colorscale="Blues", text=[[f"${v:.0f}" if v>0 else "" for v in row] for row in piv.values],
        texttemplate="%{text}", hovertemplate="<b>%{y}년 %{x}</b><br>$%{z:,.2f}<extra></extra>"))
    fig_hm.update_layout(yaxis=dict(dtick=1))
    st.plotly_chart(sfig(fig_hm, 300), use_container_width=True)
    sec("연도별 매출 추이 및 2014년 예측")
    yearly = inv.groupby("Year")["Total"].sum().reset_index()
    X = yearly["Year"].values.astype(float); Y = yearly["Total"].values.astype(float)
    coeffs = np.polyfit(X, Y, 1); poly = np.poly1d(coeffs)
    X_ext = np.append(X, [2014]); pred14 = float(poly(2014))
    fig_p = gobj.Figure()
    fig_p.add_trace(gobj.Scatter(x=X, y=Y, mode="lines+markers", name="실제 매출", line=dict(color=BLUE, width=3), marker=dict(size=10)))
    fig_p.add_trace(gobj.Scatter(x=X_ext, y=poly(X_ext), mode="lines", name="추세선", line=dict(color="#90C8FF", width=2, dash="dash")))
    fig_p.add_trace(gobj.Scatter(x=[2014], y=[pred14], mode="markers+text", name="2014 예측",
        marker=dict(color=WARNING, size=16, symbol="star"),
        text=[f"예측: {fmt(pred14)}"], textposition="top center", textfont=dict(size=13, color=WARNING)))
    fig_p.update_layout(title="연도별 매출 및 2014년 예측",
        xaxis=dict(title="연도", dtick=1, range=[2008.5,2014.5]),
        yaxis=dict(title="매출 ($)"), hovermode="x unified", legend=dict(orientation="h", y=1.12))
    st.plotly_chart(sfig(fig_p, 400), use_container_width=True)
    ss_res = np.sum((Y - poly(X))**2); ss_tot = np.sum((Y - np.mean(Y))**2)
    r2 = 1 - ss_res/ss_tot if ss_tot != 0 else 0; slope = float(coeffs[0])
    k1, k2, k3 = st.columns(3)
    with k1: kpi("2014 예측 매출", fmt(pred14), "증가 예측" if pred14>Y[-1] else "감소 예측", "up" if pred14>Y[-1] else "down")
    with k2: kpi("연간 매출 변화량", fmt(abs(slope)), "증가" if slope>0 else "감소 추세", "up" if slope>0 else "down")
    with k3: kpi("모델 적합도 R2", f"{r2:.3f}", "1에 가까울수록 신뢰도 높음", "flat")
    st.info("데이터가 5년치(2009-2013)로 제한되어 예측 오차가 있을 수 있습니다.")
    conclusion("프로모션 타이밍 전략",
        f"월별 분석 결과 <b>{peak_month}</b>이 성수기, <b>{trough_month}</b>이 비수기입니다. "
        f"성수기 전월에 신규 음반 입고와 마케팅을 집중하고, 비수기에는 할인 프로모션으로 매출 하락을 방어하세요. "
        f"2014년 예측 매출은 <b>{fmt(pred14)}</b>입니다.")

def page_salesrep(data):
    back()
    st.markdown('<div style="font-size:1.6rem;font-weight:800;color:#1D3557;">영업사원 포트폴리오 분석</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#6B7280;font-size:.85rem;margin-bottom:20px;">장르 집중도 · 매출 안정성 · 고객 다양성을 비교 분석합니다.</div>', unsafe_allow_html=True)
    inv = data["inv"]
    sel_years = st.slider("연도 범위", 2009, 2013, (2009, 2013), key="sr_year")
    inv_f = inv[(inv["Year"] >= sel_years[0]) & (inv["Year"] <= sel_years[1])]
    year_label = f"{sel_years[0]}-{sel_years[1]}년"
    if inv_f.empty: st.warning("해당 조건에 데이터가 없습니다."); return
    st.caption(f"현재 조회 기간: {year_label}")
    reps = inv_f[inv_f["SalesRep"].notna()]["SalesRep"].unique().tolist()
    rep_total = inv_f[inv_f["SalesRep"].notna()].groupby("SalesRep").agg(
        매출=("Total","sum"), 주문수=("InvoiceId","count"), 고객수=("CustomerId","nunique"), 담당국가수=("Country","nunique"),
    ).reset_index().sort_values("매출", ascending=False)
    sec("영업사원별 총 성과")
    cols = st.columns(len(rep_total))
    for col, row in zip(cols, rep_total.itertuples()):
        with col: kpi(row.SalesRep, fmt(row.매출), f"{row.주문수}건 · {row.고객수}명 · {row.담당국가수}개국")
    st.markdown("<br>", unsafe_allow_html=True)
    sec("장르 포트폴리오 레이더")
    conn = sqlite3.connect(DB_PATH)
    sr_genre = pd.read_sql("""
        SELECT e.FirstName||' '||e.LastName AS SalesRep, g.Name AS Genre,
               SUM(ii.UnitPrice*ii.Quantity) AS Rev
        FROM invoices i JOIN customers c ON i.CustomerId=c.CustomerId
        JOIN employees e ON c.SupportRepId=e.EmployeeId
        JOIN invoice_items ii ON i.InvoiceId=ii.InvoiceId
        JOIN tracks t ON ii.TrackId=t.TrackId JOIN genres g ON t.GenreId=g.GenreId
        GROUP BY SalesRep, Genre
    """, conn); conn.close()
    sr_genre_pct = sr_genre.copy()
    sr_genre_pct["비중"] = sr_genre_pct.groupby("SalesRep")["Rev"].transform(lambda x: x/x.sum()*100)
    top_genres = sr_genre.groupby("Genre")["Rev"].sum().nlargest(8).index.tolist()
    radar_data = sr_genre_pct[sr_genre_pct["Genre"].isin(top_genres)]
    fig_radar = gobj.Figure()
    for i, rep in enumerate(reps):
        df_rep = radar_data[radar_data["SalesRep"]==rep]
        vals = [float(df_rep[df_rep["Genre"]==g]["비중"].values[0]) if g in df_rep["Genre"].values else 0.0 for g in top_genres]
        vals_closed = vals + [vals[0]]; theta_closed = top_genres + [top_genres[0]]
        fig_radar.add_trace(gobj.Scatterpolar(r=vals_closed, theta=theta_closed, fill="toself", name=rep,
            line=dict(color=PALETTE[i], width=2), fillcolor=PALETTE[i], opacity=0.25))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,50])), showlegend=True,
        title="장르별 매출 비중 (%)", height=420, font=PFONT, margin=dict(l=60,r=60,t=60,b=40), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_radar, use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        sec("월별 매출 안정성 (CV - 낮을수록 안정적)")
        monthly_rep = inv_f[inv_f["SalesRep"].notna()].groupby(["SalesRep","YM"])["Total"].sum().reset_index()
        cv_rep = monthly_rep.groupby("SalesRep")["Total"].agg(
            lambda x: round(x.std()/x.mean()*100,1) if x.mean()>0 else 0).reset_index()
        cv_rep.columns = ["SalesRep","CV(%)"]
        cv_rep = cv_rep.sort_values("CV(%)")
        fig_cv = px.bar(cv_rep, x="SalesRep", y="CV(%)", color="SalesRep", color_discrete_sequence=PALETTE,
                        text=cv_rep["CV(%)"].apply(lambda v: f"{v:.1f}%"), labels={"SalesRep":"영업사원","CV(%)":"변동계수 CV (%)"},
                        title="CV 낮을수록 매출이 일정함")
        fig_cv.update_traces(textposition="outside"); fig_cv.update_layout(showlegend=False)
        st.plotly_chart(sfig(fig_cv, 340), use_container_width=True)
    with col2:
        sec("월별 매출 추이")
        fig_ml = px.line(monthly_rep.sort_values("YM"), x="YM", y="Total", color="SalesRep",
                         markers=True, color_discrete_sequence=PALETTE,
                         labels={"Total":"매출 ($)","YM":"연-월","SalesRep":"담당자"})
        fig_ml.update_layout(hovermode="x unified", xaxis=dict(tickangle=-45))
        st.plotly_chart(sfig(fig_ml, 340), use_container_width=True)
    sec("담당 고객 국가 분포")
    country_dist = inv_f[inv_f["SalesRep"].notna()].groupby(["SalesRep","Country"])["Total"].sum().reset_index()
    fig_sun = px.sunburst(country_dist, path=["SalesRep","Country"], values="Total", color="Total",
                          color_continuous_scale="Blues", title="영업사원 -> 담당 국가 매출 구성")
    st.plotly_chart(sfig(fig_sun, 420), use_container_width=True)
    best_rep = rep_total.iloc[0]["SalesRep"]; best_rev = rep_total.iloc[0]["매출"]
    stable_rep = cv_rep.iloc[0]["SalesRep"]; stable_cv = cv_rep.iloc[0]["CV(%)"]
    rep_top_genre = sr_genre.groupby("SalesRep").apply(lambda x: x.loc[x["Rev"].idxmax(),"Genre"]).reset_index()
    rep_top_genre.columns = ["SalesRep","주력장르"]
    genre_str = ", ".join([f"{r.SalesRep}({r.주력장르})" for r in rep_top_genre.itertuples()])
    conclusion("영업사원 포트폴리오 분석",
        f"조회 기간 {year_label} 기준, 총 매출 1위는 <b>{best_rep}</b> ({fmt(best_rev)})입니다. "
        f"레이더 차트에서 3인 모두 Rock 중심 포트폴리오를 보이나 세부 장르 비중에 차이가 있습니다. "
        f"영업사원별 주력 장르: <b>{genre_str}</b>. "
        f"월별 매출 안정성(CV) 기준으로 <b>{stable_rep}</b>의 매출이 가장 안정적 (CV: {stable_cv:.1f}%)입니다.")

def page_loyalty(data):
    back()
    st.markdown('<div style="font-size:1.6rem;font-weight:800;color:#1D3557;">아티스트 충성도</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#6B7280;font-size:.85rem;margin-bottom:20px;">반복 구매 비율로 국가별 아티스트 팬덤 강도를 측정합니다.</div>', unsafe_allow_html=True)
    st.info("충성도 = 동일 아티스트를 서로 다른 시점(Invoice)에서 2회 이상 구매한 고객 비율 (%) · 최소 고객 2명 이상 아티스트만 집계")
    col_f1, col_f2 = st.columns(2)
    with col_f1: sel_years = st.slider("연도 범위", 2009, 2013, (2009, 2013), key="loy_year")
    with col_f2:
        items = data["items"]
        sel_country = st.multiselect("국가 필터", sorted(items["Country"].dropna().unique()), default=[], placeholder="전체 국가", key="loy_country")
    year_label = f"{sel_years[0]}-{sel_years[1]}년"
    st.caption(f"현재 조회 기간: {year_label}")
    conn = sqlite3.connect(DB_PATH)
    raw = pd.read_sql("""
        SELECT ar.Name AS Artist, i.BillingCountry AS Country,
               i.CustomerId, COUNT(DISTINCT i.InvoiceId) AS InvoiceCount
        FROM invoice_items ii
        JOIN tracks t ON ii.TrackId=t.TrackId JOIN albums al ON t.AlbumId=al.AlbumId
        JOIN artists ar ON al.ArtistId=ar.ArtistId JOIN invoices i ON ii.InvoiceId=i.InvoiceId
        WHERE CAST(strftime('%Y', i.InvoiceDate) AS INTEGER) BETWEEN ? AND ?
        GROUP BY ar.Name, i.BillingCountry, i.CustomerId
    """, conn, params=(sel_years[0], sel_years[1])); conn.close()
    if sel_country: raw = raw[raw["Country"].isin(sel_country)]
    if raw.empty: st.warning("해당 조건에 데이터가 없습니다."); return
    total_g  = raw.groupby(["Artist","Country"])["CustomerId"].count().reset_index(name="total")
    repeat_g = raw[raw["InvoiceCount"] >= 2].groupby(["Artist","Country"])["CustomerId"].count().reset_index(name="repeat")
    loyalty  = total_g.merge(repeat_g, on=["Artist","Country"], how="left")
    loyalty["repeat"] = loyalty["repeat"].fillna(0)
    loyalty["충성도(%)"] = (loyalty["repeat"] / loyalty["total"] * 100).round(1)
    loyalty_valid = loyalty[loyalty["total"] >= 2].sort_values("충성도(%)", ascending=False)
    artist_loy = loyalty_valid.groupby("Artist").agg(
        평균충성도=("충성도(%)","mean"), 총고객수=("total","sum"), 데이터국가수=("Country","count"),
    ).reset_index().sort_values("평균충성도", ascending=False)
    sec("핵심 지표")
    k1, k2, k3 = st.columns(3)
    top1_row = artist_loy.iloc[0] if not artist_loy.empty else None
    with k1: kpi("분석 대상 아티스트", f"{len(artist_loy):,}팀", "(고객 2명 이상)")
    with k2: kpi("충성도 1위", top1_row["Artist"] if top1_row is not None else "-",
                 f"{top1_row['평균충성도']:.1f}%" if top1_row is not None else "", "up")
    with k3:
        high_loyalty = len(artist_loy[artist_loy["평균충성도"] > 0])
        kpi("충성 구매 발생 아티스트", f"{high_loyalty:,}팀", f"전체의 {high_loyalty/len(artist_loy)*100:.0f}%" if len(artist_loy)>0 else "")
    col1, col2 = st.columns(2)
    with col1:
        sec("아티스트별 평균 충성도 Top 15")
        top15 = artist_loy[artist_loy["평균충성도"] > 0].head(15).sort_values("평균충성도")
        if top15.empty: st.info("충성 구매가 발생한 아티스트가 없습니다.")
        else:
            fig_l = px.bar(top15, x="평균충성도", y="Artist", orientation="h",
                           color="평균충성도", color_continuous_scale="Blues",
                           text=top15["평균충성도"].apply(lambda v: f"{v:.1f}%"),
                           labels={"평균충성도":"충성도 (%)","Artist":""})
            fig_l.update_traces(textposition="outside"); fig_l.update_layout(coloraxis_showscale=False, xaxis=dict(range=[0,60]))
            st.plotly_chart(sfig(fig_l, 480), use_container_width=True)
    with col2:
        sec("충성도 vs 총 고객수")
        plot_df = artist_loy[artist_loy["평균충성도"] > 0].head(40)
        if not plot_df.empty:
            fig_sc = px.scatter(plot_df, x="총고객수", y="평균충성도", hover_name="Artist", size="총고객수",
                                color="평균충성도", color_continuous_scale="Blues", size_max=30,
                                labels={"총고객수":"총 고객수","평균충성도":"충성도 (%)"})
            fig_sc.update_layout(title="충성도 > 0 아티스트")
            st.plotly_chart(sfig(fig_sc, 480), use_container_width=True)
    sec("국가별 아티스트 충성도 히트맵")
    top_artists = artist_loy[artist_loy["평균충성도"] > 0].head(12)["Artist"].tolist()
    if top_artists:
        loy_heat = loyalty_valid[loyalty_valid["Artist"].isin(top_artists)]
        piv_l = loy_heat.pivot_table(index="Artist", columns="Country", values="충성도(%)", aggfunc="mean").fillna(0)
        fig_lh = gobj.Figure(gobj.Heatmap(z=piv_l.values, x=piv_l.columns.tolist(), y=piv_l.index.tolist(),
            colorscale="YlOrRd", hovertemplate="<b>%{y}</b><br>%{x}<br>충성도: %{z:.1f}%<extra></extra>",
            colorbar=dict(title="충성도 (%)")))
        fig_lh.update_layout(title="국가별 아티스트 충성도 (0% = 반복구매 없음)", xaxis=dict(tickangle=-40))
        st.plotly_chart(sfig(fig_lh, 400), use_container_width=True)
    sec("국가별 충성도 요약")
    country_loy = loyalty_valid.groupby("Country").agg(
        평균충성도=("충성도(%)","mean"), 충성아티스트수=("Artist","count"),
    ).reset_index().sort_values("평균충성도", ascending=False)
    st.dataframe(country_loy, use_container_width=True, height=300, hide_index=True)
    if not artist_loy.empty and not country_loy.empty:
        top_artist = artist_loy.iloc[0]["Artist"]; top_artist_loy = artist_loy.iloc[0]["평균충성도"]
        top_country = country_loy.iloc[0]["Country"]; top_country_loy = country_loy.iloc[0]["평균충성도"]
        low_countries = country_loy[country_loy["평균충성도"] == 0]["Country"].tolist()
        low_str = ", ".join(low_countries[:3]) if low_countries else "없음"
        pct_loyal = len(artist_loy[artist_loy["평균충성도"]>0]) / len(artist_loy) * 100
        conclusion("아티스트 충성도 전략",
            f"조회 기간 {year_label} 기준, 충성 구매가 발생한 아티스트는 전체의 <b>{pct_loyal:.0f}%</b>입니다. "
            f"충성도 1위는 <b>{top_artist} ({top_artist_loy:.1f}%)</b>이며, "
            f"국가별로는 <b>{top_country}</b>에서 평균 충성도가 가장 높습니다 ({top_country_loy:.1f}%). "
            f"반면 <b>{low_str}</b> 등에서는 반복 구매가 관찰되지 않아 충성도 파악이 어렵습니다. "
            f"충성도가 높은 아티스트는 해당 국가 집중 납품 전략이 효과적입니다.")

def page_season(data):
    back()
    st.markdown('<div style="font-size:1.6rem;font-weight:800;color:#1D3557;">장르 시즌 패턴</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#6B7280;font-size:.85rem;margin-bottom:20px;">계절성 지수(SI)와 변동계수(CV)로 장르별 시즌 효과를 측정합니다.</div>', unsafe_allow_html=True)
    st.info("계절성 지수(SI) = 해당 월 매출 / 전체 월 평균 매출  |  SI > 1.2 성수기  SI < 0.8 비수기  |  변동계수(CV) 높을수록 시즌 편차 큼")
    items = data["items"]
    col_f1, col_f2 = st.columns(2)
    with col_f1: sel_years = st.slider("연도 범위", 2009, 2013, (2009, 2013), key="sea_year")
    with col_f2: sel_genres = st.multiselect("장르 선택", sorted(items["Genre"].dropna().unique()), default=[], placeholder="전체 장르", key="sea_genre")
    fi = items[(items["Year"] >= sel_years[0]) & (items["Year"] <= sel_years[1])]
    if sel_genres: fi = fi[fi["Genre"].isin(sel_genres)]
    year_label = f"{sel_years[0]}-{sel_years[1]}년"
    st.caption(f"현재 조회 기간: {year_label}")
    if fi.empty: st.warning("해당 조건에 데이터가 없습니다."); return
    gm = fi.groupby(["Genre","Month"])["LineTotal"].sum().reset_index()
    genre_avg = gm.groupby("Genre")["LineTotal"].transform("mean")
    gm["SI"] = (gm["LineTotal"] / genre_avg).round(2)
    cv_df = gm.groupby("Genre")["LineTotal"].agg(
        lambda x: round(x.std()/x.mean()*100, 1) if x.mean()>0 else 0).reset_index()
    cv_df.columns = ["Genre","CV(%)"]; cv_df = cv_df.sort_values("CV(%)", ascending=False)
    si_piv = gm.pivot_table(index="Genre", columns="Month", values="SI", aggfunc="mean").fillna(0)
    for m in range(1,13):
        if m not in si_piv.columns: si_piv[m] = 0
    si_piv = si_piv[sorted(si_piv.columns)]
    sec("시즌 영향 큰 장르 Top 3 (CV 기준)")
    top3_cv = cv_df.head(3)
    kcols = st.columns(3)
    for col, row in zip(kcols, top3_cv.itertuples()):
        peak_month = int(si_piv.loc[row.Genre].idxmax()) if row.Genre in si_piv.index else 0
        with col: kpi(row.Genre, f"CV {row._2:.1f}%", f"성수기 {peak_month}월", "up")
    st.markdown("<br>", unsafe_allow_html=True)
    sec("장르별 계절성 지수(SI) 히트맵")
    fig_si = gobj.Figure(gobj.Heatmap(z=si_piv.values,
        x=[f"{m}월" for m in si_piv.columns], y=si_piv.index.tolist(),
        colorscale="RdBu_r", zmid=1.0,
        hovertemplate="<b>%{y}</b><br>%{x}<br>SI: %{z:.2f}<extra></extra>",
        colorbar=dict(title="SI")))
    fig_si.update_layout(title="빨강=성수기(SI>1.2) · 파랑=비수기(SI<0.8)", yaxis=dict(autorange="reversed"))
    st.plotly_chart(sfig(fig_si, 520), use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        sec("장르별 변동계수(CV) - 시즌 민감도")
        fig_cv = px.bar(cv_df.sort_values("CV(%)"), x="CV(%)", y="Genre", orientation="h",
                        color="CV(%)", color_continuous_scale="Reds",
                        text=cv_df.sort_values("CV(%)")["CV(%)"].apply(lambda v: f"{v:.1f}%"),
                        labels={"CV(%)":"변동계수 CV (%)","Genre":""})
        fig_cv.update_traces(textposition="outside"); fig_cv.update_layout(coloraxis_showscale=False, title="CV 높을수록 시즌 영향 큼")
        st.plotly_chart(sfig(fig_cv, 480), use_container_width=True)
    with col2:
        sec("Top 6 장르 월별 매출 추이")
        top6g = fi.groupby("Genre")["LineTotal"].sum().nlargest(6).index.tolist()
        trend = fi[fi["Genre"].isin(top6g)].groupby(["Month","Genre"])["LineTotal"].sum().reset_index()
        trend["월"] = trend["Month"].apply(lambda m: f"{m}월")
        fig_line = px.line(trend, x="월", y="LineTotal", color="Genre", markers=True,
                           color_discrete_sequence=PALETTE, labels={"LineTotal":"매출 ($)","Genre":"장르"})
        fig_line.update_layout(hovermode="x unified")
        st.plotly_chart(sfig(fig_line, 480), use_container_width=True)
    sec("장르별 성수기 · 비수기 · 시즌 민감도 요약")
    summary = []
    for genre in si_piv.index:
        row_si = si_piv.loc[genre]
        cv_val = cv_df[cv_df["Genre"]==genre]["CV(%)"].values
        cv_v = cv_val[0] if len(cv_val)>0 else 0
        summary.append({"장르": genre, "성수기": f"{int(row_si.idxmax())}월 (SI {row_si.max():.2f})",
            "비수기": f"{int(row_si.idxmin())}월 (SI {row_si.min():.2f})", "CV(%)": f"{cv_v:.1f}%",
            "시즌 민감도": "높음" if cv_v>=70 else ("중간" if cv_v>=40 else "낮음")})
    df_sum = pd.DataFrame(summary).sort_values("CV(%)", ascending=False)
    st.dataframe(df_sum, use_container_width=True, height=380, hide_index=True)
    high_cv = cv_df[cv_df["CV(%)"]>=70]["Genre"].tolist()
    low_cv  = cv_df[cv_df["CV(%)"]<40]["Genre"].tolist()
    top_cv_genre = cv_df.iloc[0]["Genre"]; top_cv_val = cv_df.iloc[0]["CV(%)"]
    peak_m_top = int(si_piv.loc[top_cv_genre].idxmax()) if top_cv_genre in si_piv.index else 0
    conclusion("장르 시즌 패턴 전략",
        f"조회 기간 {year_label} 기준, CV 분석 결과 <b>{'·'.join(high_cv) if high_cv else '없음'}</b> 장르는 시즌 편차가 크며, "
        f"특히 <b>{top_cv_genre}</b>의 성수기는 <b>{peak_m_top}월</b> (CV {top_cv_val:.1f}%)입니다. "
        f"반면 <b>{'·'.join(low_cv[:3]) if low_cv else '없음'}</b> 장르는 연중 매출이 안정적(CV 40% 미만)입니다. "
        f"시즌 민감도가 높은 장르는 성수기 전월 재고 확보, 안정 장르는 연중 균등 발주 전략이 적합합니다.")

def page_customer():
    back()
    st.markdown('<div style="font-size:1.6rem;font-weight:800;color:#1D3557;margin-bottom:4px;">고객 관리</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#6B7280;font-size:.85rem;margin-bottom:20px;">고객 정보를 조회하고 추가 · 수정 · 삭제합니다.</div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["목록 조회","정보 수정","신규 추가","고객 삭제"])
    with tab1:
        conn = sqlite3.connect(DB_PATH)
        df_c = pd.read_sql("""
            SELECT c.CustomerId AS ID, c.FirstName AS 이름, c.LastName AS 성,
                   c.Company AS 회사, c.Country AS 국가, c.City AS 도시,
                   c.Email AS 이메일, c.Phone AS 전화번호,
                   e.FirstName||' '||e.LastName AS 담당직원
            FROM customers c LEFT JOIN employees e ON c.SupportRepId=e.EmployeeId ORDER BY c.CustomerId
        """, conn); conn.close()
        sc1, sc2 = st.columns([3,1])
        with sc1: kw = st.text_input("검색 (이름/이메일/회사)", placeholder="검색어 입력...")
        with sc2:
            ctry_list = ["전체"] + sorted(df_c["국가"].dropna().unique().tolist())
            sel_ctry  = st.selectbox("국가", ctry_list)
        filtered = df_c.copy()
        if kw: filtered = filtered[filtered["이름"].str.contains(kw,case=False,na=False)|filtered["성"].str.contains(kw,case=False,na=False)|filtered["이메일"].str.contains(kw,case=False,na=False)|filtered["회사"].str.contains(kw,case=False,na=False)]
        if sel_ctry != "전체": filtered = filtered[filtered["국가"]==sel_ctry]
        st.dataframe(filtered, use_container_width=True, height=480, hide_index=True)
        st.caption(f"{len(filtered)}명 / 전체 {len(df_c)}명")
    with tab2:
        conn = sqlite3.connect(DB_PATH)
        df_list = pd.read_sql("SELECT CustomerId, FirstName||' '||LastName AS Name FROM customers ORDER BY CustomerId", conn); conn.close()
        options = {f"[{r.CustomerId}] {r.Name}": r.CustomerId for r in df_list.itertuples()}
        sel_id  = options[st.selectbox("수정할 고객", list(options.keys()))]
        conn = sqlite3.connect(DB_PATH)
        row = pd.read_sql("SELECT * FROM customers WHERE CustomerId=?", conn, params=(sel_id,)).iloc[0]; conn.close()
        c1, c2 = st.columns(2)
        with c1:
            nf=st.text_input("이름 *",value=row["FirstName"] or ""); nco=st.text_input("회사",value=row["Company"] or "")
            nci=st.text_input("도시",value=row["City"] or ""); nct=st.text_input("국가",value=row["Country"] or "")
            nph=st.text_input("전화번호",value=row["Phone"] or "")
        with c2:
            nl=st.text_input("성 *",value=row["LastName"] or ""); nad=st.text_input("주소",value=row["Address"] or "")
            nst=st.text_input("주/도",value=row["State"] or ""); npo=st.text_input("우편번호",value=row["PostalCode"] or "")
            nem=st.text_input("이메일 *",value=row["Email"] or "")
        if st.button("저장", type="primary", key="upd"):
            if not nf.strip() or not nl.strip() or not nem.strip(): st.error("이름, 성, 이메일은 필수입니다.")
            else:
                try:
                    conn=sqlite3.connect(DB_PATH)
                    conn.execute("UPDATE customers SET FirstName=?,LastName=?,Company=?,Address=?,City=?,State=?,Country=?,PostalCode=?,Phone=?,Email=? WHERE CustomerId=?",
                                 (nf,nl,nco or None,nad or None,nci or None,nst or None,nct or None,npo or None,nph or None,nem,sel_id))
                    conn.commit(); conn.close(); st.success("수정 완료!"); st.cache_data.clear()
                except Exception as e: st.error(f"오류: {e}")
    with tab3:
        st.info("이름, 성, 이메일은 필수입니다.")
        c1, c2 = st.columns(2)
        with c1:
            af=st.text_input("이름 *",placeholder="예: 민준",key="af"); aco=st.text_input("회사",placeholder="(주)마이스토어",key="aco")
            aci=st.text_input("도시",placeholder="Seoul",key="aci"); act=st.text_input("국가",placeholder="South Korea",key="act")
            aph=st.text_input("전화번호",placeholder="+82-10-0000-0000",key="aph")
        with c2:
            al=st.text_input("성 *",placeholder="예: 김",key="al"); aad=st.text_input("주소",placeholder="강남구 테헤란로 123",key="aad")
            ast_=st.text_input("주/도",placeholder="Seoul",key="ast"); apo=st.text_input("우편번호",placeholder="06234",key="apo")
            aem=st.text_input("이메일 *",placeholder="minjun@example.com",key="aem")
        conn=sqlite3.connect(DB_PATH)
        df_emp=pd.read_sql("SELECT EmployeeId, FirstName||' '||LastName AS Name FROM employees ORDER BY EmployeeId",conn); conn.close()
        emp_opts={"없음":None}; emp_opts.update({f"[{r.EmployeeId}] {r.Name}":r.EmployeeId for r in df_emp.itertuples()})
        sel_emp=emp_opts[st.selectbox("담당 직원",list(emp_opts.keys()),key="sel_emp")]
        if st.button("고객 추가",type="primary",key="add"):
            if not af.strip() or not al.strip() or not aem.strip(): st.error("이름, 성, 이메일은 필수입니다.")
            else:
                try:
                    conn=sqlite3.connect(DB_PATH)
                    conn.execute("INSERT INTO customers (FirstName,LastName,Company,Address,City,State,Country,PostalCode,Phone,Fax,Email,SupportRepId) VALUES (?,?,?,?,?,?,?,?,?,NULL,?,?)",
                                 (af,al,aco or None,aad or None,aci or None,ast_ or None,act or None,apo or None,aph or None,aem,sel_emp))
                    conn.commit()
                    new_id=conn.execute("SELECT last_insert_rowid()").fetchone()[0]; conn.close()
                    st.success(f"추가 완료! 고객 ID: {new_id}"); st.balloons(); st.cache_data.clear()
                except Exception as e: st.error(f"오류: {e}")
    with tab4:
        st.warning("삭제된 정보는 복구할 수 없습니다.")
        conn=sqlite3.connect(DB_PATH)
        df_del=pd.read_sql("SELECT CustomerId, FirstName||' '||LastName AS Name, Email, Country FROM customers ORDER BY CustomerId",conn); conn.close()
        ds=st.text_input("삭제할 고객 검색",key="ds")
        fd=df_del.copy()
        if ds: fd=fd[fd["Name"].str.contains(ds,case=False,na=False)|fd["Email"].str.contains(ds,case=False,na=False)]
        if not fd.empty:
            del_opts={f"[{r.CustomerId}] {r.Name} ({r.Email})":r.CustomerId for r in fd.itertuples()}
            sel_del_id=del_opts[st.selectbox("삭제할 고객",list(del_opts.keys()),key="dsel")]
            conn=sqlite3.connect(DB_PATH)
            dr=pd.read_sql("SELECT * FROM customers WHERE CustomerId=?",conn,params=(sel_del_id,)).iloc[0]
            pc=pd.read_sql("SELECT COUNT(*) AS cnt FROM invoices WHERE CustomerId=?",conn,params=(sel_del_id,)).iloc[0]["cnt"]
            conn.close()
            with st.expander("선택된 고객 정보", expanded=True):
                dc1,dc2=st.columns(2)
                with dc1: st.write(f"**이름:** {dr['FirstName']} {dr['LastName']}"); st.write(f"**이메일:** {dr['Email']}")
                with dc2:
                    st.write(f"**국가:** {dr['Country'] or '-'}")
                    st.error(f"구매 이력 {pc}건") if pc>0 else st.success("구매 이력 없음")
            confirm=st.checkbox("위 고객을 삭제하겠습니다.")
            if st.button("삭제 실행",type="primary",key="del",disabled=not confirm):
                try:
                    conn=sqlite3.connect(DB_PATH)
                    if pc>0:
                        conn.execute("DELETE FROM invoice_items WHERE InvoiceId IN (SELECT InvoiceId FROM invoices WHERE CustomerId=?)",(sel_del_id,))
                        conn.execute("DELETE FROM invoices WHERE CustomerId=?",(sel_del_id,))
                    conn.execute("DELETE FROM customers WHERE CustomerId=?",(sel_del_id,))
                    conn.commit(); conn.close(); st.success("삭제 완료!"); st.cache_data.clear()
                except Exception as e: st.error(f"오류: {e}")

def page_employee(data):
    back()
    st.markdown('<div style="font-size:1.6rem;font-weight:800;color:#1D3557;margin-bottom:4px;">사원 현황</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#6B7280;font-size:.85rem;margin-bottom:20px;">직원 정보 및 성과를 조회합니다.</div>', unsafe_allow_html=True)
    conn=sqlite3.connect(DB_PATH)
    df_emp=pd.read_sql("""
        SELECT e.EmployeeId AS ID, e.FirstName||' '||e.LastName AS 이름, e.Title AS 직책,
               e.HireDate AS 입사일, e.City AS 도시, e.Country AS 국가, e.Email AS 이메일,
               m.FirstName||' '||m.LastName AS 상급자
        FROM employees e LEFT JOIN employees m ON e.ReportsTo=m.EmployeeId ORDER BY e.EmployeeId
    """,conn); conn.close()
    sec("직원 목록")
    st.dataframe(df_emp, use_container_width=True, height=320, hide_index=True)
    sec("담당자별 성과")
    inv=data["inv"]
    rep=inv[inv["SalesRep"].notna()].groupby("SalesRep").agg(
        매출=("Total","sum"),주문수=("InvoiceId","count"),고객수=("CustomerId","nunique"),
    ).reset_index().sort_values("매출",ascending=False)
    cols=st.columns(len(rep))
    for col,row in zip(cols,rep.itertuples()):
        with col: kpi(row.SalesRep,fmt(row.매출),f"{row.주문수}건 · {row.고객수}명")
    st.markdown("<br>",unsafe_allow_html=True)
    fig=px.bar(rep,x="SalesRep",y="매출",color="SalesRep",color_discrete_sequence=PALETTE,
               text=rep["매출"].apply(fmt),labels={"SalesRep":"담당자","매출":"매출 ($)"},title="담당자별 매출")
    fig.update_traces(textposition="outside"); fig.update_layout(showlegend=False)
    st.plotly_chart(sfig(fig,340),use_container_width=True)

def main():
    with st.spinner("데이터 로딩 중..."):
        data = load()
    if data is None:
        st.error(f"DB 파일을 찾을 수 없습니다: `{DB_PATH}`")
        st.info("app.py와 같은 폴더에 chinook.db를 두고 다시 실행하세요.")
        st.stop()
    p = st.session_state.page
    if   p == "home":             page_home()
    elif p == "insight_where":    page_where(data)
    elif p == "insight_what":     page_what(data)
    elif p == "insight_when":     page_when(data)
    elif p == "insight_salesrep": page_salesrep(data)
    elif p == "insight_loyalty":  page_loyalty(data)
    elif p == "insight_season":   page_season(data)
    elif p == "customer":         page_customer()
    elif p == "employee":         page_employee(data)
    st.markdown(f'<p style="text-align:center;color:{GRAY};font-size:.72rem;margin-top:24px;">MyStore Analytics · Chinook Music Store · Built with Streamlit</p>', unsafe_allow_html=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"오류: {e}")
        st.exception(e)
