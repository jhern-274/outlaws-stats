import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

DATA_FILE = Path(__file__).parent / "data" / "games.json"
STAT_COLS = ["AB", "1B", "2B", "3B", "HR_OTF", "HR_ITP", "R", "RBI", "K"]

st.set_page_config(page_title="Outlaws Stats", page_icon="🤠", layout="wide")

CSS = """
<style>
.hero {
  padding: 28px 32px;
  border-radius: 16px;
  background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 40%, #6b1a1a 100%);
  color: #fff;
  margin-bottom: 8px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.25);
  text-align: center;
}
.hero h1 {
  font-size: 44px; margin: 0; font-weight: 800; letter-spacing: -1px;
  font-family: -apple-system, "Segoe UI", sans-serif;
}
.hero .sub { opacity: 0.82; font-size: 15px; margin-top: 8px; }
.hero .badges { margin-top: 14px; display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; }
.badge {
  display: inline-block; padding: 5px 14px;
  background: rgba(212,175,55,0.18); color: #f4d774;
  border: 1px solid rgba(212,175,55,0.4);
  border-radius: 999px; font-weight: 700; font-size: 13px;
}
.badge.red { background: rgba(220,80,80,0.18); color: #ff8a8a; border-color: rgba(220,80,80,0.4); }
.badge.green { background: rgba(80,200,120,0.18); color: #8ee8a8; border-color: rgba(80,200,120,0.4); }
.leader-card {
  border: 1px solid rgba(150,150,170,0.18);
  border-radius: 12px; padding: 16px 18px;
  background: rgba(255,255,255,0.02);
  height: 100%;
}
.leader-card h4 {
  margin: 0 0 12px 0; font-size: 12px; letter-spacing: 1px;
  text-transform: uppercase; opacity: 0.65; font-weight: 700;
}
.leader-row {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 5px 0; font-size: 15px;
}
.leader-row .rank {
  display: inline-block; width: 22px; text-align: center;
  font-weight: 800; margin-right: 8px;
}
.leader-row.r1 .rank { color: #d4af37; }
.leader-row.r2 .rank { color: #c0c0c0; }
.leader-row.r3 .rank { color: #cd7f32; }
.leader-row .name { flex: 1; font-weight: 500; }
.leader-row .val { font-family: ui-monospace, "SF Mono", Consolas, monospace; opacity: 0.95; font-weight: 600; }
.recap {
  border-left: 4px solid #d4af37;
  background: rgba(212,175,55,0.06);
  padding: 14px 18px; border-radius: 6px; margin: 8px 0 24px 0;
}
.recap .title { font-size: 13px; opacity: 0.7; text-transform: uppercase; letter-spacing: 1px; }
.recap .score { font-size: 22px; font-weight: 800; margin: 4px 0; }
.recap .star { font-size: 14px; opacity: 0.9; }
.hr-dot {
  display: inline-block; width: 18px; height: 18px;
  border-radius: 50%; margin-right: 5px; vertical-align: middle;
  box-shadow: inset 0 -2px 4px rgba(0,0,0,0.15);
}
.hr-otf { background: #c8102e; border: 2px solid #8a0a1f; }
.hr-itp { background: transparent; border: 2px solid #1d3a6e; box-shadow: none; }
.hr-row {
  display: flex; align-items: center; padding: 10px 4px;
  border-bottom: 1px solid rgba(150,150,170,0.12);
}
.hr-row:last-child { border-bottom: none; }
.hr-name { flex: 0 0 140px; font-weight: 600; font-size: 15px; }
.hr-markers { flex: 1; }
.hr-count {
  opacity: 0.7; font-size: 13px;
  font-family: ui-monospace, "SF Mono", Consolas, monospace;
}
.hr-legend { margin-bottom: 10px; font-size: 13px; opacity: 0.85; }
.hr-footer {
  margin-top: 14px; padding-top: 12px;
  border-top: 1px solid rgba(150,150,170,0.18);
  font-size: 14px; opacity: 0.85;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data
def load_data(path: Path):
    return json.loads(Path(path).read_text())


def build_pg_df(games: list[dict]) -> pd.DataFrame:
    rows = []
    for g in games:
        for s in g["stats"]:
            row = {"game_id": g["game_id"], "date": g["date"], "opponent": g["opponent"],
                   "type": g.get("type", "regular"), "player": s["player"]}
            for c in STAT_COLS:
                row[c] = s.get(c, 0)
            rows.append(row)
    return pd.DataFrame(rows)


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["HR"] = df["HR_OTF"] + df["HR_ITP"]
    df["H"] = df["1B"] + df["2B"] + df["3B"] + df["HR"]
    df["XBH"] = df["2B"] + df["3B"] + df["HR"]
    df["TB"] = df["1B"] + 2 * df["2B"] + 3 * df["3B"] + 4 * df["HR"]
    df["AVG"] = (df["H"] / df["AB"]).where(df["AB"] > 0, 0).round(3)
    df["OBP"] = df["AVG"]  # walks count as hits in this league
    df["SLG"] = (df["TB"] / df["AB"]).where(df["AB"] > 0, 0).round(3)
    df["OPS"] = (df["OBP"] + df["SLG"]).round(3)
    return df


def season_totals(pg: pd.DataFrame) -> pd.DataFrame:
    totals = pg.groupby("player", as_index=False)[STAT_COLS].sum()
    totals["G"] = pg.groupby("player")["game_id"].nunique().values
    return add_derived(totals)


def leader_html(title: str, df: pd.DataFrame, col: str, fmt: str = "{:.3f}", n: int = 3) -> str:
    rows = ""
    if df.empty or (df[col].max() == 0 and col in ("HR", "RBI", "R", "H", "XBH")):
        rows = '<div class="leader-row"><span class="name" style="opacity:0.5">—</span></div>'
    else:
        top = df.sort_values(col, ascending=False).head(n)
        for rank, (_, r) in enumerate(top.iterrows(), 1):
            rows += (
                f'<div class="leader-row r{rank}">'
                f'<span><span class="rank">{rank}</span><span class="name">{r["player"]}</span></span>'
                f'<span class="val">{fmt.format(r[col])}</span>'
                f'</div>'
            )
    return f'<div class="leader-card"><h4>{title}</h4>{rows}</div>'


# --- Load --------------------------------------------------------------------
data = load_data(DATA_FILE)
games = sorted(data["games"], key=lambda g: g["game_id"])
team = data.get("team_name", "Our Team")
season = data.get("season", "")
season_len = data.get("regular_season_games", 7)

pg = add_derived(build_pg_df(games))
totals = season_totals(build_pg_df(games))


def pog_totals(games_list: list[dict]) -> pd.DataFrame:
    rows = []
    for g in games_list:
        for p in g.get("players_of_game") or []:
            rows.append({"player": p["player"], "reason": p.get("reason", ""),
                         "game_id": g["game_id"], "date": g["date"]})
    if not rows:
        return pd.DataFrame(columns=["player", "POG"])
    df = pd.DataFrame(rows)
    return (df.groupby("player", as_index=False)
              .size().rename(columns={"size": "POG"})
              .sort_values("POG", ascending=False))


pog_df = pog_totals(games)

reg_games = [g for g in games if g.get("type", "regular") == "regular"]
po_games = [g for g in games if g.get("type") == "playoff"]
wins = sum(1 for g in games if g["result"] == "W")
losses = sum(1 for g in games if g["result"] == "L")
ties = sum(1 for g in games if g["result"] == "T")
rf = sum(g["team_runs"] for g in games)
ra = sum(g["opp_runs"] for g in games)
record = f"{wins}-{losses}" + (f"-{ties}" if ties else "")

# --- Hero --------------------------------------------------------------------
reg_progress_badge = f'<span class="badge">Game {len(reg_games)} of {season_len}</span>'
record_class = "green" if wins > losses else ("red" if losses > wins else "")
record_badge = f'<span class="badge {record_class}">{record}</span>'
diff_badge = f'<span class="badge">Run diff {rf-ra:+d}</span>'
po_badge = f'<span class="badge">Playoffs: {len(po_games)}</span>' if po_games else ""
st.markdown(
    f'<div class="hero"><h1>🤠 {team}</h1>'
    f'<div class="sub">{season} Season Hitting Dashboard</div>'
    f'<div class="badges">{record_badge}{reg_progress_badge}{diff_badge}{po_badge}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

if not games:
    st.info("No games logged yet. Add entries to `data/games.json`.")
    st.stop()

# --- Latest game recap -------------------------------------------------------
latest = games[-1]
latest_pg = pg[pg["game_id"] == latest["game_id"]]


def _stat_line(player_name: str) -> str:
    row = latest_pg[latest_pg["player"] == player_name]
    if row.empty or int(row.iloc[0]["AB"]) == 0:
        return ""
    s = row.iloc[0]
    parts = [f"{int(s['H'])}-for-{int(s['AB'])}"]
    if s["HR"]: parts.append(f"{int(s['HR'])} HR")
    if s["RBI"]: parts.append(f"{int(s['RBI'])} RBI")
    if s["R"]: parts.append(f"{int(s['R'])} R")
    return ", ".join(parts)


pog_entries = latest.get("players_of_game") or []
if pog_entries:
    pog_html = ""
    for p in pog_entries:
        sl = _stat_line(p["player"])
        reason = p.get("reason", "")
        reason_badge = f'<span class="badge" style="margin-left:8px">{reason}</span>' if reason else ""
        sl_text = f' · <span style="opacity:0.8">{sl}</span>' if sl else ""
        pog_html += (
            f'<div style="margin-top:6px"><b>⭐ {p["player"]}</b>{reason_badge}{sl_text}</div>'
        )
    star_line = f'<div style="font-size:13px; opacity:0.75; text-transform:uppercase; letter-spacing:1px; margin-top:4px">Players of the game</div>{pog_html}'
else:
    qualified_latest = latest_pg[latest_pg["AB"] > 0]
    star = qualified_latest.sort_values(["OPS", "H", "RBI"], ascending=False).head(1)
    if not star.empty:
        s = star.iloc[0]
        sl = _stat_line(s["player"])
        star_line = f"⭐ <b>Outlaw of the Game:</b> {s['player']} — {sl}"
    else:
        star_line = ""

result_word = {"W": "Won", "L": "Lost", "T": "Tied"}.get(latest["result"], latest["result"])
st.markdown(
    f'<div class="recap">'
    f'<div class="title">Latest game · {latest["date"]}</div>'
    f'<div class="score">{result_word} {latest["team_runs"]}–{latest["opp_runs"]} vs {latest["opponent"]}</div>'
    f'<div class="star">{star_line}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# --- KPI strip ---------------------------------------------------------------
team_h = int(totals["H"].sum())
team_ab = int(totals["AB"].sum())
team_avg = round(team_h / team_ab, 3) if team_ab else 0
team_tb = int(totals["TB"].sum())
team_slg = round(team_tb / team_ab, 3) if team_ab else 0
team_ops = round(team_avg + team_slg, 3)
gp = len(games)
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Runs / Game", f"{rf/gp:.1f}")
k2.metric("Team AVG", f"{team_avg:.3f}")
k3.metric("Team OPS", f"{team_ops:.3f}")
k4.metric("Team HRs", int(totals["HR"].sum()),
          help=f"{int(totals['HR_OTF'].sum())} over the fence · {int(totals['HR_ITP'].sum())} inside the park")
k5.metric("Total Hits", team_h)

st.write("")

# --- Tabs --------------------------------------------------------------------
tab_overview, tab_leaders, tab_table, tab_log = st.tabs(
    ["📈 Overview", "🏆 Leaders", "📊 Stats Table", "🗓️ Game Log"]
)

with tab_overview:
    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("##### Runs scored vs allowed by game")
        game_summary = pd.DataFrame([{
            "Game": f"G{g['game_id']}",
            "Opponent": g["opponent"],
            "Result": g["result"],
            "For": g["team_runs"],
            "Against": g["opp_runs"],
        } for g in games])
        long = game_summary.melt(id_vars=["Game", "Opponent", "Result"],
                                 value_vars=["For", "Against"],
                                 var_name="Side", value_name="Runs")
        chart = (
            alt.Chart(long)
            .mark_bar()
            .encode(
                x=alt.X("Game:N", sort=None, title=None),
                xOffset=alt.XOffset("Side:N"),
                y=alt.Y("Runs:Q"),
                color=alt.Color("Side:N",
                                scale=alt.Scale(domain=["For", "Against"], range=["#c8102e", "#1d3a6e"]),
                                legend=alt.Legend(orient="top", title=None)),
                tooltip=["Game", "Opponent", "Side", "Runs"],
            )
            .properties(height=260)
        )
        st.altair_chart(chart, use_container_width=True)

    with right:
        st.markdown("##### Top 8 by OPS")
        min_ab_for_chart = max(1, int(totals["AB"].max() * 0.5))
        chart_df = totals[totals["AB"] >= min_ab_for_chart].sort_values("OPS", ascending=False).head(8)
        if chart_df.empty:
            st.caption("Not enough at-bats yet.")
        else:
            ops_chart = (
                alt.Chart(chart_df)
                .mark_bar(color="#c8102e")
                .encode(
                    y=alt.Y("player:N", sort="-x", title=None),
                    x=alt.X("OPS:Q"),
                    tooltip=["player", "AB", "H", "HR", "AVG", "SLG", "OPS"],
                )
                .properties(height=260)
            )
            st.altair_chart(ops_chart, use_container_width=True)
            st.caption(f"Qualified: ≥{min_ab_for_chart} AB")

    st.markdown("##### Home run ticker")
    hr_df = totals[(totals["HR_OTF"] + totals["HR_ITP"]) > 0][["player", "HR_OTF", "HR_ITP"]]
    if hr_df.empty:
        st.caption("No home runs yet.")
    else:
        legend = (
            '<div class="hr-legend">'
            '<span class="hr-dot hr-otf"></span> Over the fence &nbsp; · &nbsp; '
            '<span class="hr-dot hr-itp"></span> Inside the park'
            '</div>'
        )
        rows_html = ""
        sorted_hr = hr_df.assign(_total=hr_df["HR_OTF"] + hr_df["HR_ITP"]) \
                          .sort_values(["_total", "HR_OTF"], ascending=[False, False])
        for _, r in sorted_hr.iterrows():
            otf, itp = int(r["HR_OTF"]), int(r["HR_ITP"])
            markers = ('<span class="hr-dot hr-otf"></span>' * otf
                       + '<span class="hr-dot hr-itp"></span>' * itp)
            total = otf + itp
            rows_html += (
                f'<div class="hr-row">'
                f'<span class="hr-name">{r["player"]}</span>'
                f'<span class="hr-markers">{markers}</span>'
                f'<span class="hr-count">{total} HR</span>'
                f'</div>'
            )
        team_otf = int(hr_df["HR_OTF"].sum())
        team_itp = int(hr_df["HR_ITP"].sum())
        footer = (
            f'<div class="hr-footer">'
            f'Team total: <b>{team_otf + team_itp} HR</b> &nbsp;·&nbsp; '
            f'{team_otf} over the fence &nbsp;·&nbsp; {team_itp} inside the park'
            f'</div>'
        )
        st.markdown(legend + rows_html + footer, unsafe_allow_html=True)

with tab_leaders:
    max_ab = int(totals["AB"].max())
    default_min = max(1, min(max_ab, 2 * len(games)))
    min_ab = st.slider("Min AB to qualify for rate stats", 0, max(max_ab, 1), value=default_min)
    qualified = totals[totals["AB"] >= min_ab]

    row1 = st.columns(3)
    row1[0].markdown(leader_html("Batting average", qualified, "AVG", "{:.3f}"), unsafe_allow_html=True)
    row1[1].markdown(leader_html("OPS", qualified, "OPS", "{:.3f}"), unsafe_allow_html=True)
    row1[2].markdown(leader_html("Slugging", qualified, "SLG", "{:.3f}"), unsafe_allow_html=True)

    row2 = st.columns(3)
    row2[0].markdown(leader_html("Home runs", totals, "HR", "{:.0f}"), unsafe_allow_html=True)
    row2[1].markdown(leader_html("RBIs", totals, "RBI", "{:.0f}"), unsafe_allow_html=True)
    row2[2].markdown(leader_html("Runs scored", totals, "R", "{:.0f}"), unsafe_allow_html=True)

    row3 = st.columns(3)
    row3[0].markdown(leader_html("Hits", totals, "H", "{:.0f}"), unsafe_allow_html=True)
    row3[1].markdown(leader_html("Extra-base hits", totals, "XBH", "{:.0f}"), unsafe_allow_html=True)
    row3[2].markdown(leader_html("Total bases", totals, "TB", "{:.0f}"), unsafe_allow_html=True)

    row4 = st.columns(3)
    row4[0].markdown(leader_html("⭐ Player of the Game honors", pog_df, "POG", "{:.0f}"),
                     unsafe_allow_html=True)

def color_scale(series: pd.Series, rgb: tuple[int, int, int]) -> list[str]:
    """Lightweight stand-in for Styler.background_gradient (no matplotlib needed)."""
    vmax, vmin = series.max(), series.min()
    if pd.isna(vmax) or vmax == vmin:
        return ["" for _ in series]
    r, g, b = rgb
    out = []
    for v in series:
        if pd.isna(v):
            out.append("")
            continue
        norm = (v - vmin) / (vmax - vmin)
        alpha = 0.10 + 0.50 * norm
        out.append(f"background-color: rgba({r},{g},{b},{alpha:.2f})")
    return out


with tab_table:
    _left_margin, center, _right_margin = st.columns([1, 4, 1])
    with center:
        sort_by = st.selectbox("Sort by", ["OPS", "AVG", "HR", "RBI", "R", "H", "TB", "AB"], index=0)
        cols = ["player", "G", "AB", "H", "1B", "2B", "3B", "HR", "HR_OTF", "HR_ITP",
                "R", "RBI", "K", "AVG", "OBP", "SLG", "OPS"]
        table = totals[cols].sort_values(sort_by, ascending=False).reset_index(drop=True)
        rate_cols = ["AVG", "OBP", "SLG", "OPS"]
        int_cols = [c for c in cols if c not in rate_cols + ["player"]]
        styled = (
            table.style
            .format({c: "{:.3f}" for c in rate_cols} | {c: "{:.0f}" for c in int_cols})
            .set_properties(**{"text-align": "center"})
            .set_properties(subset=["player"], **{"text-align": "left", "font-weight": "600"})
            .set_table_styles([{"selector": "th", "props": [("text-align", "center")]}])
            .apply(color_scale, rgb=(212, 175, 55), subset=["OPS"])
            .apply(color_scale, rgb=(80, 180, 110), subset=["HR"])
            .apply(color_scale, rgb=(80, 180, 110), subset=["RBI"])
            .apply(color_scale, rgb=(80, 180, 110), subset=["R"])
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)

with tab_log:
    glog = pd.DataFrame([{
        "Game": g["game_id"],
        "Date": g["date"],
        "Opponent": g["opponent"],
        "Result": g["result"],
        "Score": f"{g['team_runs']}-{g['opp_runs']}",
        "Type": g.get("type", "regular").title(),
    } for g in games])
    st.dataframe(glog, hide_index=True, use_container_width=True)

    st.markdown("##### Per-player game log")
    selected = st.selectbox("Player", sorted(pg["player"].unique()))
    pdf = pg[pg["player"] == selected].sort_values("game_id")
    show = pdf[["date", "opponent", "AB", "H", "1B", "2B", "3B", "HR", "HR_OTF",
                "HR_ITP", "R", "RBI", "K", "AVG", "SLG", "OPS"]]
    st.dataframe(
        show.style.format({"AVG": "{:.3f}", "SLG": "{:.3f}", "OPS": "{:.3f}"}),
        hide_index=True,
        use_container_width=True,
    )
