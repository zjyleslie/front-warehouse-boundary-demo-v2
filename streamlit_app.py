"""前置仓无人化方案竞争力边界交互演示。"""

from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SCHEME_ORDER = ["纯人工", "人机协作", "现场零人（探索边界）"]
COLORS = {
    "纯人工": "#17365D",
    "人机协作": "#C77938",
    "现场零人（探索边界）": "#4C9A73",
}


st.set_page_config(
    page_title="前置仓无人化竞争力边界",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {--ink:#142033;--muted:#657084;--navy:#17365d;--orange:#c77938;
           --green:#4c9a73;--canvas:#f5f4f0;--surface:#fffefa;--line:#dfe3e8;}
    .stApp{background:var(--canvas);color:var(--ink)}
    [data-testid="stHeader"]{background:rgba(245,244,240,.88)}
    [data-testid="stToolbar"],#MainMenu,footer{visibility:hidden}
    [data-testid="stSidebar"]{background:#eeede9;border-right:1px solid #d9d8d3}
    [data-testid="collapsedControl"],[data-testid="stSidebarCollapsedControl"]{
        display:flex!important;visibility:visible!important;opacity:1!important;
        position:fixed!important;top:.65rem!important;left:.65rem!important;z-index:999999!important;
        background:#fffefa!important;border:1px solid #d9d8d3!important;border-radius:8px!important;
        box-shadow:0 2px 10px rgba(20,32,51,.12)!important
    }
    .block-container{padding:1.35rem clamp(1rem,3vw,2.7rem) 3rem;max-width:1280px}
    h1,h2,h3{color:var(--ink);letter-spacing:-.02em}
    .hero{background:var(--surface);border:1px solid rgba(20,32,51,.09);border-radius:16px;
          padding:1.8rem 2rem;margin-bottom:1rem;box-shadow:0 6px 24px rgba(24,38,58,.035)}
    .hero small{color:var(--navy);font-weight:700;letter-spacing:.08em}
    .hero h1{margin:.4rem 0;font-size:clamp(1.8rem,3vw,2.45rem)}
    .hero p{margin:0;color:var(--muted);max-width:850px}
    .answer-strip{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:.8rem 0 1rem}
    .answer-strip>div{background:var(--surface);border:1px solid rgba(20,32,51,.09);
                      border-radius:12px;padding:14px 15px}
    .answer-strip small{display:block;color:var(--muted);font-size:.76rem;margin-bottom:.3rem}
    .answer-strip strong{font-size:1.25rem}
    .verdict{background:var(--navy);color:white;border-radius:12px;padding:15px 17px;
             line-height:1.65;margin-bottom:1rem}
    .notice{background:#fff6e8;border:1px solid rgba(199,121,56,.25);border-radius:10px;
            padding:10px 12px;color:#6f4d2b;margin:.5rem 0 1rem}
    .info{background:#edf2f7;border:1px solid rgba(23,54,93,.14);border-radius:10px;
          padding:10px 12px;color:#33465f;margin:.5rem 0 1rem}
    .flow{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:.7rem 0 1rem}
    .flow>div{background:var(--surface);border:1px solid rgba(20,32,51,.09);border-radius:10px;
              padding:12px;text-align:center}
    .flow span{display:block;color:var(--muted);font-size:.78rem}
    .flow strong{font-size:1.35rem}
    div[data-testid="stMetric"]{background:var(--surface);border:1px solid rgba(20,32,51,.09);
                                border-radius:12px;padding:12px 14px}
    [data-testid="stDataFrame"],[data-testid="stVegaLiteChart"]{background:var(--surface);
          border:1px solid rgba(20,32,51,.08);border-radius:10px;padding:.28rem}
    @media(max-width:800px){.answer-strip{grid-template-columns:1fr}.flow{grid-template-columns:repeat(2,1fr)}}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_data() -> dict[str, pd.DataFrame]:
    files = {
        "cost": "scenario_cost_results.csv",
        "surface": "decision_surface.csv",
        "win": "win_probability.csv",
        "performance": "baseline_performance.csv",
        "replay": "process_replay_sample.csv",
        "daily": "daily_order_summary.csv",
        "evidence": "parameter_evidence.csv",
        "audit": "model_audit.csv",
        "refined_threshold": "refined_h1_threshold.csv",
        "refined_validation": "refined_selected_validation.csv",
        "threshold_bootstrap": "refined_threshold_bootstrap.csv",
    }
    return {key: pd.read_csv(DATA / filename) for key, filename in files.items()}


def scheme_scale() -> alt.Scale:
    return alt.Scale(domain=SCHEME_ORDER, range=[COLORS[s] for s in SCHEME_ORDER])


def money(value: float) -> str:
    return f"{value / 10000:.2f} 万元"


data = load_data()
cost = data["cost"]

with st.sidebar:
    st.markdown("### 情景控制台")
    scenario = st.selectbox("成本情景", ["基准", "乐观", "保守"], index=0)
    volumes = sorted(
        cost.loc[cost["scenario"].eq(scenario), "daily_orders"].astype(int).unique().tolist()
    )
    default_volume = 154 if 154 in volumes else volumes[0]
    daily_orders = st.select_slider("日订单量（单/日）", options=volumes, value=default_volume)
    if scenario == "基准":
        st.caption("基准情景增加了552和553单两个细化需求点。")
    else:
        st.caption("乐观和保守情景沿用原需求网格。")
    st.divider()
    st.markdown("**仿真判定标准**")
    st.caption("P95完成时间不高于30分钟，超时率不高于5%，资源利用率不高于85%。")

daily = data["daily"]
total_records = int(daily["order_count"].sum())
complete = daily[daily["is_complete_day"].astype(str).str.lower().isin(["true", "1"])]
complete_records = int(complete["order_count"].sum())

st.markdown(
    """
    <section class="hero">
      <small>应用统计学课程论文</small>
      <h1>前置仓无人化方案竞争力边界</h1>
      <p>使用课题组提供的订单级记录，结合离散事件仿真和年等值成本模型评估三类方案。</p>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="answer-strip">
      <div><small>订单样本</small><strong>32个日期 · {total_records:,}笔</strong></div>
      <div><small>完整日样本</small><strong>31日 · {complete_records:,}笔</strong></div>
      <div><small>模型门槛95%范围</small><strong>543至553单/日</strong></div>
    </div>
    <div class="verdict">
      扩大复验后，350至450单/日内没有稳定切换。保守判定下，552单/日时纯人工成本最低，553单/日时现场零人成本最低。中心门槛为552至553单/日，Bootstrap 95%范围为543至553单/日。
    </div>
    """,
    unsafe_allow_html=True,
)


st.header("1　基准结果")
baseline = cost[(cost["scenario"].eq("基准")) & (cost["daily_orders"].eq(154))].copy()
baseline["年等值成本（万元）"] = baseline["annual_total_cost"] / 10000
baseline["scheme"] = pd.Categorical(baseline["scheme"], categories=SCHEME_ORDER, ordered=True)
baseline = baseline.sort_values("scheme")

left, right = st.columns([1.12, 1], gap="large")
with left:
    bars = (
        alt.Chart(baseline)
        .mark_bar(size=30, cornerRadiusEnd=5)
        .encode(
            y=alt.Y("scheme:N", sort=SCHEME_ORDER, title=None),
            x=alt.X("年等值成本（万元）:Q", title="年等值成本（万元/年）"),
            color=alt.Color("scheme:N", scale=scheme_scale(), legend=None),
            tooltip=[
                alt.Tooltip("scheme:N", title="方案"),
                alt.Tooltip("年等值成本（万元）:Q", title="年成本", format=".2f"),
                alt.Tooltip("unit_cost_per_order:Q", title="单位成本（元/单）", format=".2f"),
            ],
        )
        .properties(height=250)
    )
    labels = bars.mark_text(align="left", baseline="middle", dx=6, color="#142033").encode(
        text=alt.Text("年等值成本（万元）:Q", format=".2f")
    )
    st.altair_chart((bars + labels).configure_view(stroke=None), width="stretch")
with right:
    perf = data["performance"].copy()
    perf["scheme"] = pd.Categorical(perf["scheme"], categories=SCHEME_ORDER, ordered=True)
    perf = perf.sort_values("scheme")
    show = perf[["scheme", "p95_cycle_minutes", "mean_wait_minutes", "throughput_per_hour", "mean_max_utilization"]].copy()
    show.columns = ["方案", "P95完成时间", "平均等待", "吞吐量", "关键资源利用率"]
    show["P95完成时间"] = show["P95完成时间"].map(lambda x: f"{x:.2f}分钟")
    show["平均等待"] = show["平均等待"].map(lambda x: f"{x:.3f}分钟")
    show["吞吐量"] = show["吞吐量"].map(lambda x: f"{x:.2f}单/小时")
    show["关键资源利用率"] = show["关键资源利用率"].map(lambda x: f"{100*x:.1f}%")
    st.dataframe(show, hide_index=True, width="stretch")
    st.markdown(
        '<div class="info">运行指标使用固定配置下的30次共同随机数实验。成本结果使用容量筛查后的最低成本可行配置。</div>',
        unsafe_allow_html=True,
    )


st.header("2　需求变化与成本边界")
curve = cost[cost["scenario"].eq(scenario)].copy()
curve["单位成本（元/单）"] = curve["unit_cost_per_order"]
line = (
    alt.Chart(curve)
    .mark_line(point=alt.OverlayMarkDef(size=35), strokeWidth=2.3)
    .encode(
        x=alt.X("daily_orders:Q", title="日订单量（单/日）"),
        y=alt.Y("单位成本（元/单）:Q", title="单位成本（元/单）", scale=alt.Scale(zero=False)),
        color=alt.Color("scheme:N", scale=scheme_scale(), title=None, legend=alt.Legend(orient="top")),
        tooltip=[
            alt.Tooltip("scheme:N", title="方案"),
            alt.Tooltip("daily_orders:Q", title="日订单量"),
            alt.Tooltip("单位成本（元/单）:Q", title="单位成本", format=".2f"),
        ],
    )
)
rule = alt.Chart(pd.DataFrame({"x": [daily_orders]})).mark_rule(color="#142033", strokeDash=[5, 4]).encode(x="x:Q")
if scenario == "基准":
    band = alt.Chart(pd.DataFrame({"x1": [543], "x2": [553]})).mark_rect(color="#C77938", opacity=.10).encode(x="x1:Q", x2="x2:Q")
    chart = band + line + rule
    chart_caption = "浅橙色区域为门槛估计的Bootstrap 95%范围。黑色虚线为当前选择的需求点。"
else:
    chart = line + rule
    chart_caption = "黑色虚线为当前选择的需求点。细化门槛范围仅对应基准情景。"
st.altair_chart(chart.properties(height=365).configure_view(stroke=None), width="stretch")
st.caption(chart_caption)

current = cost[(cost["scenario"].eq(scenario)) & (cost["daily_orders"].eq(daily_orders))].copy()
current = current.sort_values("annual_total_cost")
winner = current.iloc[0]
second = current.iloc[1]
margin = (second["annual_total_cost"] - winner["annual_total_cost"]) / second["annual_total_cost"]
c1, c2, c3 = st.columns(3)
c1.metric("当前最低成本方案", str(winner["scheme"]).replace("（探索边界）", ""))
c2.metric("最低年等值成本", money(float(winner["annual_total_cost"])))
c3.metric("与第二名差距", money(float(second["annual_total_cost"] - winner["annual_total_cost"])), delta=f"{margin:.1%}", delta_color="off")

result = current[["scheme", "config_id", "human_workers", "robot_count", "workstations", "annual_total_cost", "unit_cost_per_order", "p95_cycle_minutes", "capacity_success_rate"]].copy()
result.columns = ["方案", "配置", "人工数", "机器人", "工作站", "年等值成本", "单位成本", "P95完成时间", "复验成功率"]
result["年等值成本"] = result["年等值成本"].map(lambda x: f"{x/10000:.2f}万元")
result["单位成本"] = result["单位成本"].map(lambda x: f"{x:.2f}元/单")
result["P95完成时间"] = result["P95完成时间"].map(lambda x: f"{x:.2f}分钟")
result["复验成功率"] = result["复验成功率"].map(lambda x: f"{100*x:.1f}%")
st.dataframe(result, hide_index=True, width="stretch")
if margin < .05:
    st.markdown('<div class="notice">当前接近成本边界，方案排序对参数变化较敏感。建议结合敏感性结果和现场数据评估。</div>', unsafe_allow_html=True)


st.header("3　细化容量门槛")
refined = data["refined_threshold"].copy()
refined["单调拟合成功率"] = 100 * refined["isotonic_success_rate"]
refined["Wilson下限"] = 100 * refined["isotonic_wilson_ci95_low"]
threshold_base = alt.Chart(refined).encode(
    x=alt.X("daily_orders:Q", title="日订单量（单/日）", scale=alt.Scale(domain=[530, 580])),
)
threshold_band = alt.Chart(pd.DataFrame({"x1": [543], "x2": [553]})).mark_rect(
    color="#C77938", opacity=.10
).encode(x="x1:Q", x2="x2:Q")
threshold_rule = alt.Chart(pd.DataFrame({"y": [95]})).mark_rule(
    color="#C77938", strokeDash=[6, 4]
).encode(y="y:Q")
threshold_line = threshold_base.mark_line(color="#17365D", strokeWidth=2.5).encode(
    y=alt.Y("Wilson下限:Q", title="Wilson 95%区间下限（%）", scale=alt.Scale(zero=False)),
)
threshold_points = threshold_base.mark_circle(color="#17365D", size=38).encode(
    y="Wilson下限:Q",
    tooltip=[
        alt.Tooltip("daily_orders:Q", title="日订单量"),
        alt.Tooltip("单调拟合成功率:Q", title="单调拟合成功率（%）", format=".2f"),
        alt.Tooltip("Wilson下限:Q", title="Wilson下限（%）", format=".2f"),
    ],
)
st.altair_chart(
    (threshold_band + threshold_rule + threshold_line + threshold_points)
    .properties(height=330)
    .configure_view(stroke=None),
    width="stretch",
)

row_552 = refined.loc[refined["daily_orders"].eq(552)].iloc[0]
row_553 = refined.loc[refined["daily_orders"].eq(553)].iloc[0]
t1, t2, t3 = st.columns(3)
t1.metric("552单/日", "纯人工仍最低", f"Wilson下限 {row_552['Wilson下限']:.2f}%", delta_color="off")
t2.metric("553单/日", "现场零人最低", f"Wilson下限 {row_553['Wilson下限']:.2f}%", delta_color="off")
t3.metric("门槛95%范围", "543至553单/日", "2,000次Bootstrap", delta_color="off")
st.markdown(
    '<div class="info">350至450单/日逐单运行500次后，1名人工配置的最低Wilson下限为97.41%。530至580单/日逐单运行1,000次后，中心门槛定位在552至553单/日。</div>',
    unsafe_allow_html=True,
)


st.header("4　工资与需求共同变化")
surface = data["surface"]
orders_show = [100, 154, 250, 350, 450, 550, 552, 553, 750, 950, 1200, 1600]
wages_show = [4000, 4500, 5000, 5500, 6000, 7000, 8000, 9000]
surface = surface[surface["daily_orders"].isin(orders_show) & surface["wage_monthly"].isin(wages_show)].copy()
surface["方案简称"] = surface["scheme_key"].map({"manual": "人工", "collaborative": "协作", "unmanned": "零人"})
surface_base = alt.Chart(surface).encode(
    x=alt.X("daily_orders:O", title="日订单量（单/日）", sort=orders_show),
    y=alt.Y("wage_monthly:O", title="月工资（元/人）", sort=list(reversed(wages_show))),
)
heat = (
    surface_base.mark_rect(cornerRadius=2)
    .encode(
        color=alt.Color("scheme:N", scale=scheme_scale(), title="最低成本方案"),
        tooltip=["daily_orders:O", "wage_monthly:O", alt.Tooltip("scheme:N", title="最低成本方案")],
    )
)
text_layer = surface_base.mark_text(fontSize=11, fontWeight=600).encode(
    text="方案简称:N",
    color=alt.value("white"),
)
st.altair_chart((heat + text_layer).properties(height=350).configure_view(stroke=None), width="stretch")
st.caption("基准成本参数下的离散决策表。552和553单为细化需求点，每个色块对应一个工资和需求组合。")


st.header("5　订单级仿真过程回放")
st.markdown('<div class="info">本部分回放第二阶段保存的一次订单级仿真结果，可按方案和时间查看订单状态。</div>', unsafe_allow_html=True)
replay = data["replay"].copy()
replay["scheme"] = replay["scheme"].replace({"现场零人": "现场零人（探索边界）"})
r1, r2 = st.columns([1, 2])
with r1:
    replay_scheme = st.selectbox("回放方案", SCHEME_ORDER, index=1)
with r2:
    minute = st.slider("一天中的时间（分钟）", 0, 1440, 720, 15, format="%d")
one = replay[replay["scheme"].eq(replay_scheme)].copy()
arrived = one["arrival_minute"].le(minute)
completed = one["completion_minute"].le(minute)
picking = arrived & one["pick_start_minute"].le(minute) & one["pick_end_minute"].gt(minute)
packing = arrived & one["pack_start_minute"].le(minute) & one["completion_minute"].gt(minute)
waiting = arrived & ~completed & ~picking & ~packing
snapshot = {
    "已到达": int(arrived.sum()),
    "等待": int(waiting.sum()),
    "拣选或搬运中": int(picking.sum()),
    "工作站处理中": int(packing.sum()),
    "已完成": int(completed.sum()),
}
st.markdown(
    '<div class="flow">' + ''.join(f'<div><span>{k}</span><strong>{v}</strong></div>' for k, v in snapshot.items()) + '</div>',
    unsafe_allow_html=True,
)
st.caption("回放样本包含模拟订单编号和事件时间，已去除商品名称、原始订单号和个人信息。")


st.header("6　稳健性与参数依据")
win = data["win"]
focus = win[(win["daily_orders"].isin([154, 550])) & (win["scheme_key"].isin(["collaborative", "unmanned"]))].copy()
focus["情景"] = focus["daily_orders"].astype(str) + "单/日 · " + focus["scheme"].str.replace("（探索边界）", "", regex=False)
focus["成本胜出频率"] = focus["cost_win_probability"].map(lambda x: f"{100*x:.1f}%")
st.dataframe(focus[["情景", "成本胜出频率"]], hide_index=True, width="stretch")
st.markdown(
    """
    <div class="notice">
    5,000次参数传播用于统计设定区间内各方案的成本胜出频率。订单记录由课题组提供。设备价格、寿命、维护、停机和自动拣件能力按研究假设设定。
    </div>
    """,
    unsafe_allow_html=True,
)
with st.expander("查看参数依据"):
    st.dataframe(data["evidence"], hide_index=True, width="stretch")

st.caption("版本日期：2026-11-16　｜　已纳入逐单复验与门槛细化结果")
