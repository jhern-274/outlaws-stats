import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

DATA_FILE = Path(__file__).parent / "data" / "games.json"
STAT_COLS = ["AB", "1B", "2B", "3B", "HR_OTF", "HR_ITP", "R", "RBI", "K"]

HEADER_LABELS = {
    "player": "Player", "G": "G", "AB": "AB", "H": "H",
    "1B": "1B", "2B": "2B", "3B": "3B", "HR": "HR",
    "HR_OTF": "OTF", "HR_ITP": "ITP",
    "R": "R", "RBI": "RBI", "K": "K",
    "AVG": "AVG", "OBP": "OBP", "SLG": "SLG", "OPS": "OPS",
}

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

/* KPI grid — 5 cols desktop, 2 cols mobile */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
  margin: 8px 0 20px 0;
}
@media (max-width: 760px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}
.kpi-card {
  border: 1px solid rgba(150,150,170,0.18);
  border-radius: 10px;
  padding: 14px 16px;
  background: rgba(255,255,255,0.02);
}
.kpi-card .label {
  font-size: 11px; opacity: 0.65;
  text-transform: uppercase; letter-spacing: 0.6px;
  font-weight: 700;
}
.kpi-card .value {
  font-size: 26px; font-weight: 800;
  margin-top: 4px; line-height: 1.1;
}
.kpi-card .hint { font-size: 11px; opacity: 0.55; margin-top: 4px; }

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

/* Stats table — sticky player column, centered values, color grades */
.stats-table-wrap {
  max-width: 1100px;
  margin: 8px auto 8px auto;
  overflow-x: auto;
  border: 1px solid rgba(150,150,170,0.18);
  border-radius: 10px;
  background: #0e1117;
}
.stats-table {
  border-collapse: separate;
  border-spacing: 0;
  width: 100%;
  font-size: 14px;
  color: #fafafa;
}
.stats-table th, .stats-table td {
  padding: 10px 14px;
  text-align: center;
  border-bottom: 1px solid rgba(150,150,170,0.10);
  white-space: nowrap;
}
.stats-table tbody tr:last-child td { border-bottom: none; }
.stats-table th {
  font-weight: 700; font-size: 11px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  opacity: 0.75;
  background: #161922;
  position: sticky; top: 0; z-index: 1;
}
.stats-table td.player-cell {
  text-align: left;
  font-weight: 600;
  position: sticky; left: 0;
  background: #0e1117;
  z-index: 2;
  border-right: 1px solid rgba(150,150,170,0.18);
}
.stats-table th.player-th {
  text-align: left;
  position: sticky; left: 0; top: 0;
  background: #161922;
  z-index: 3;
  border-right: 1px solid rgba(150,150,170,0.18);
}

/* Player vs Player comparison */
.cmp-wrap { max-width: 720px; margin: 0 auto; }
.cmp-header {
  display: grid;
  grid-template-columns: 1fr 100px 1fr;
  align-items: center;
  padding: 18px 0;
  border-bottom: 2px solid rgba(150,150,170,0.22);
  margin-bottom: 6px;
}
.cmp-name {
  font-size: 26px; font-weight: 800; letter-spacing: -0.5px;
}
.cmp-name.left { text-align: right; padding-right: 12px; }
.cmp-name.right { text-align: left; padding-left: 12px; }
.cmp-header .vs {
  text-align: center; font-size: 13px; font-weight: 700;
  opacity: 0.5; text-transform: uppercase; letter-spacing: 2px;
}
.cmp-row {
  display: grid;
  grid-template-columns: 1fr 140px 1fr;
  align-items: center;
  padding: 11px 0;
  border-bottom: 1px solid rgba(150,150,170,0.08);
}
.cmp-row:last-child { border-bottom: none; }
.cmp-val {
  font-family: ui-monospace, "SF Mono", Consolas, monospace;
  font-size: 18px; font-weight: 500; opacity: 0.55;
}
.cmp-val.left { text-align: right; padding-right: 14px; }
.cmp-val.right { text-align: left; padding-left: 14px; }
.cmp-val.winner { color: #f4d774; font-weight: 800; opacity: 1; }
.cmp-val.tie { opacity: 0.85; }
.cmp-stat {
  text-align: center; font-size: 11px; font-weight: 600;
  opacity: 0.7; text-transform: uppercase; letter-spacing: 1px;
}
.cmp-tally {
  text-align: center; margin-top: 16px; padding-top: 14px;
  border-top: 2px solid rgba(150,150,170,0.22);
  font-size: 14px; opacity: 0.9;
}
@media (max-width: 600px) {
  .cmp-header { grid-template-columns: 1fr 60px 1fr; }
  .cmp-name { font-size: 19px; }
  .cmp-row { grid-template-columns: 1fr 100px 1fr; padding: 9px 0; }
  .cmp-val { font-size: 15px; }
  .cmp-val.left { padding-right: 8px; }
  .cmp-val.right { padding-left: 8px; }
  .cmp-stat { font-size: 9.5px; letter-spacing: 0.5px; }
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
    df["OBP"] = df["AVG"]
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


def make_color_fn(series: pd.Series, rgb: tuple[int, int, int]):
    vmin, vmax = series.min(), series.max()
    if vmin == vmax:
        return lambda _v: ""
    r, g, b = rgb

    def f(v):
        norm = (v - vmin) / (vmax - vmin)
        alpha = 0.10 + 0.50 * float(norm)
        return f"background-color: rgba({r},{g},{b},{alpha:.2f})"
    return f


def render_stats_table(table: pd.DataFrame) -> None:
    rate_cols = {"AVG", "OBP", "SLG", "OPS"}
    color_funcs = {
        "OPS": make_color_fn(table["OPS"], (212, 175, 55)),
        "HR": make_color_fn(table["HR"], (80, 180, 110)),
        "RBI": make_color_fn(table["RBI"], (80, 180, 110)),
        "R": make_color_fn(table["R"], (80, 180, 110)),
    }
    headers = []
    for c in table.columns:
        cls = "player-th" if c == "player" else ""
        headers.append(f'<th class="{cls}">{HEADER_LABELS.get(c, c)}</th>')
    body = []
    for _, row in table.iterrows():
        cells = []
        for c in table.columns:
            v = row[c]
            if c == "player":
                cells.append(f'<td class="player-cell">{v}</td>')
                continue
            bg = color_funcs[c](v) if c in color_funcs else ""
            text = f"{v:.3f}" if c in rate_cols else f"{int(v)}"
            style_attr = f' style="{bg}"' if bg else ""
            cells.append(f"<td{style_attr}>{text}</td>")
        body.append(f'<tr>{"".join(cells)}</tr>')
    html = (
        '<div class="stats-table-wrap">'
        '<table class="stats-table">'
        f'<thead><tr>{"".join(headers)}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody>'
        "</table>"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


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

# --- KPI grid (responsive: 5 cols desktop, 2 cols mobile) --------------------
team_h = int(totals["H"].sum())
team_ab = int(totals["AB"].sum())
team_avg = round(team_h / team_ab, 3) if team_ab else 0
team_tb = int(totals["TB"].sum())
team_slg = round(team_tb / team_ab, 3) if team_ab else 0
team_ops = round(team_avg + team_slg, 3)
team_hr = int(totals["HR"].sum())
team_otf = int(totals["HR_OTF"].sum())
team_itp = int(totals["HR_ITP"].sum())
gp = len(games)

kpi_html = (
    '<div class="kpi-grid">'
    f'<div class="kpi-card"><div class="label">Runs / Game</div>'
    f'<div class="value">{rf/gp:.1f}</div></div>'
    f'<div class="kpi-card"><div class="label">Team AVG</div>'
    f'<div class="value">{team_avg:.3f}</div></div>'
    f'<div class="kpi-card"><div class="label">Team OPS</div>'
    f'<div class="value">{team_ops:.3f}</div></div>'
    f'<div class="kpi-card"><div class="label">Team HRs</div>'
    f'<div class="value">{team_hr}</div>'
    f'<div class="hint">{team_otf} OTF · {team_itp} ITP</div></div>'
    f'<div class="kpi-card"><div class="label">Total Hits</div>'
    f'<div class="value">{team_h}</div></div>'
    '</div>'
)
st.markdown(kpi_html, unsafe_allow_html=True)

# --- Tabs --------------------------------------------------------------------
tab_overview, tab_leaders, tab_compare, tab_table, tab_log = st.tabs(
    ["📈 Overview", "🏆 Leaders", "⚔️ Compare", "📊 Stats Table", "🗓️ Game Log"]
)

with tab_overview:
    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("##### Team hit mix")
        hit_mix = pd.DataFrame([
            {"Type": "Singles",   "Count": int(totals["1B"].sum())},
            {"Type": "Doubles",   "Count": int(totals["2B"].sum())},
            {"Type": "Triples",   "Count": int(totals["3B"].sum())},
            {"Type": "Home Runs", "Count": int(totals["HR"].sum())},
        ])
        total_hits = hit_mix["Count"].sum()
        if total_hits > 0:
            hit_mix["Pct"] = (hit_mix["Count"] / total_hits * 100).round(1)
        else:
            hit_mix["Pct"] = 0.0
        mix_chart = (
            alt.Chart(hit_mix)
            .mark_bar()
            .encode(
                x=alt.X("Type:N", sort=["Singles", "Doubles", "Triples", "Home Runs"],
                        title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Count:Q", title="Hits"),
                color=alt.Color(
                    "Type:N",
                    scale=alt.Scale(
                        domain=["Singles", "Doubles", "Triples", "Home Runs"],
                        range=["#1d3a6e", "#3b6ea5", "#e58a30", "#c8102e"],
                    ),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip("Type:N"),
                    alt.Tooltip("Count:Q"),
                    alt.Tooltip("Pct:Q", format=".1f", title="% of hits"),
                ],
            )
            .properties(height=260)
        )
        st.altair_chart(mix_chart, use_container_width=True)
        st.caption(f"{total_hits} team hits · "
                   + " · ".join(f'{r["Type"]} {int(r["Count"])}' for _, r in hit_mix.iterrows()))

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
                    x=alt.X("OPS:Q", axis=alt.Axis(format=".3f")),
                    tooltip=[
                        "player",
                        "AB",
                        "H",
                        "HR",
                        alt.Tooltip("AVG:Q", format=".3f"),
                        alt.Tooltip("SLG:Q", format=".3f"),
                        alt.Tooltip("OPS:Q", format=".3f"),
                    ],
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
        team_otf_total = int(hr_df["HR_OTF"].sum())
        team_itp_total = int(hr_df["HR_ITP"].sum())
        footer = (
            f'<div class="hr-footer">'
            f'Team total: <b>{team_otf_total + team_itp_total} HR</b> &nbsp;·&nbsp; '
            f'{team_otf_total} over the fence &nbsp;·&nbsp; {team_itp_total} inside the park'
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

with tab_compare:
    players_list = sorted(totals["player"].unique().tolist())
    if len(players_list) < 2:
        st.info("Need at least 2 players to compare.")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            p1 = st.selectbox("Player A", players_list, index=0, key="cmp_p1")
        with col_b:
            default_b = 1 if len(players_list) > 1 else 0
            p2 = st.selectbox("Player B", players_list, index=default_b, key="cmp_p2")

        if p1 == p2:
            st.warning("Pick two different players to compare.")
        else:
            r1 = totals[totals["player"] == p1].iloc[0]
            r2 = totals[totals["player"] == p2].iloc[0]

            # (stat, label, fmt, direction)  — direction "high" = higher is better
            compare_specs = [
                ("G",   "Games",            "{:.0f}", "high"),
                ("AB",  "At-Bats",          "{:.0f}", "high"),
                ("H",   "Hits",             "{:.0f}", "high"),
                ("AVG", "Batting Avg",      "{:.3f}", "high"),
                ("OBP", "On-base %",        "{:.3f}", "high"),
                ("SLG", "Slugging",         "{:.3f}", "high"),
                ("OPS", "OPS",              "{:.3f}", "high"),
                ("HR",  "Home Runs",        "{:.0f}", "high"),
                ("XBH", "Extra-Base Hits",  "{:.0f}", "high"),
                ("R",   "Runs Scored",      "{:.0f}", "high"),
                ("RBI", "RBIs",             "{:.0f}", "high"),
                ("K",   "Strikeouts",       "{:.0f}", "low"),
            ]

            left_wins = right_wins = ties_count = 0
            rows_html = ""
            for stat, label, fmt, direction in compare_specs:
                v1, v2 = r1[stat], r2[stat]
                if direction == "high":
                    if v1 > v2: winner = "left"
                    elif v2 > v1: winner = "right"
                    else: winner = "tie"
                else:
                    if v1 < v2: winner = "left"
                    elif v2 < v1: winner = "right"
                    else: winner = "tie"
                if winner == "left":
                    left_wins += 1
                    lc, rc = "winner", ""
                elif winner == "right":
                    right_wins += 1
                    lc, rc = "", "winner"
                else:
                    ties_count += 1
                    lc = rc = "tie"
                rows_html += (
                    f'<div class="cmp-row">'
                    f'<div class="cmp-val left {lc}">{fmt.format(v1)}</div>'
                    f'<div class="cmp-stat">{label}</div>'
                    f'<div class="cmp-val right {rc}">{fmt.format(v2)}</div>'
                    f'</div>'
                )

            header = (
                f'<div class="cmp-header">'
                f'<div class="cmp-name left">{p1}</div>'
                f'<div class="vs">vs</div>'
                f'<div class="cmp-name right">{p2}</div>'
                f'</div>'
            )
            tally = (
                f'<div class="cmp-tally">'
                f'<b>{p1}</b> leads in <b>{left_wins}</b> &nbsp;·&nbsp; '
                f'<b>{p2}</b> leads in <b>{right_wins}</b> &nbsp;·&nbsp; '
                f'Tied in <b>{ties_count}</b>'
                f'</div>'
            )
            st.markdown('<div class="cmp-wrap">' + header + rows_html + tally + '</div>',
                        unsafe_allow_html=True)

with tab_table:
    sort_by = st.selectbox("Sort by", ["OPS", "AVG", "HR", "RBI", "R", "H", "TB", "AB"], index=0)
    cols = ["player", "G", "AB", "H", "1B", "2B", "3B", "HR", "HR_OTF", "HR_ITP",
            "R", "RBI", "K", "AVG", "OBP", "SLG", "OPS"]
    table = totals[cols].sort_values(sort_by, ascending=False).reset_index(drop=True)
    render_stats_table(table)

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
