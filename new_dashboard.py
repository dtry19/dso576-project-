"""Native Streamlit experience for the Appliance Listing Review workflow."""
from __future__ import annotations

import html
import re
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from appliance_analysis import (
    CONCERNS,
    assess_metadata,
    get_listing_evidence,
    join_reviews_metadata,
    load_metadata,
    load_reviews,
    rank_listings,
    summarize_scope,
    tag_concerns,
)

ROOT = Path(__file__).resolve().parent
RAW_REVIEWS = ROOT / "dataset" / "Appliances_sample.jsonl"
CLEAN_REVIEWS = ROOT / "output" / "Appliances_cleaned.jsonl"
QA_REVIEWS = ROOT / "output" / "Appliances_cleaned_50_examples.jsonl"
DEFAULT_METADATA = ROOT / "output" / "Appliances_metadata_sample.jsonl"
CPSC_CONTEXT = ROOT / "output" / "cpsc_appliance_context.json"

AMAZON_DATA_URL = "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023"
CPSC_DATA_URL = "https://www.cpsc.gov/Recalls"

NAVY = "#131A22"
SLATE = "#232F3E"
ORANGE = "#FF9900"
BLUE = "#146EB4"
PALE = "#F4F6F8"
INK = "#172235"
MUTED = "#687386"
ROSE = "#D4778A"

st.set_page_config(
    page_title="Appliance Listing Review",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
      .stApp {{ background: {PALE}; color: {INK}; }}
      [data-testid="stHeader"] {{ background: {NAVY}; border-bottom: 3px solid {ORANGE}; }}
      [data-testid="stSidebar"] {{ background: {SLATE}; }}
      [data-testid="stSidebar"] * {{ color: #f4f7fa; }}
      [data-testid="stSidebar"] input,
      [data-testid="stSidebar"] [data-baseweb="select"] * {{ color: {INK}; }}
      [data-testid="stSidebar"] hr {{ border-color: #445164; }}
      [data-testid="stMetric"] {{
        background: white; border: 1px solid #e2e7ec; border-radius: 12px;
        padding: 16px 18px; box-shadow: 0 2px 8px rgba(19,26,34,.05);
      }}
      [data-testid="stMetricLabel"] {{ color: {MUTED}; font-weight: 700; }}
      [data-testid="stMetricValue"] {{ color: {INK}; }}
      .hero {{
        background: linear-gradient(115deg, {NAVY} 0%, {SLATE} 72%, #1d4a6b 100%);
        border-bottom: 4px solid {ORANGE}; border-radius: 14px; color: white;
        padding: 28px 32px; margin-bottom: 18px;
      }}
      .hero .eyebrow {{ color: {ORANGE}; font-size: 11px; font-weight: 800; letter-spacing: .13em; }}
      .hero h1 {{ color: white; margin: 5px 0 4px; font-size: 2rem; }}
      .hero p {{ color: #ced7e0; margin: 0; }}
      .step {{ display:flex; align-items:center; gap:8px; color:{BLUE}; font-size:11px;
        font-weight:800; letter-spacing:.09em; text-transform:uppercase; margin-bottom:4px; }}
      .step span {{ display:inline-grid; place-items:center; width:24px; height:24px;
        border-radius:50%; background:{SLATE}; color:white; }}
      .section-note {{ color:{MUTED}; font-size:12px; margin-top:-7px; margin-bottom:12px; }}
      .status-card {{ background:#fff7e6; border:1px solid #ffd798; border-left:4px solid {ORANGE};
        border-radius:8px; padding:12px 14px; color:#6c4a14; font-size:13px; margin:10px 0 14px; }}
      .decision-card {{ background:white; border:1px solid #dfe5eb; border-left:5px solid {BLUE};
        border-radius:10px; padding:16px 18px; margin:12px 0 18px; box-shadow:0 2px 8px rgba(19,26,34,.04); }}
      .decision-card.found {{ border-left-color:#2e8b57; background:#f5fbf7; }}
      .decision-card.review {{ border-left-color:{ORANGE}; background:#fffaf0; }}
      .decision-card.missing {{ border-left-color:#7a8da5; background:#f7f9fb; }}
      .decision-card h4 {{ margin:0 0 6px; color:{INK}; }}
      .decision-card p {{ margin:5px 0; color:#415065; font-size:13px; }}
      .decision-card .recommendation {{ margin-top:10px; padding-top:9px; border-top:1px solid #dfe5eb; }}
      .product-card {{ background:white; border:1px solid #dfe5eb; border-top:4px solid {ORANGE};
        border-radius:12px; padding:18px 20px; margin:8px 0 18px; box-shadow:0 2px 8px rgba(19,26,34,.05); }}
      .product-card h3 {{ margin:0 0 4px; }}
      .product-card .product-meta {{ color:{MUTED}; font-size:13px; margin:3px 0; }}
      .badge {{ display:inline-block; border-radius:999px; padding:4px 9px; margin:6px 5px 0 0;
        font-size:11px; font-weight:800; background:#edf3f8; color:{SLATE}; }}
      .badge.limited {{ background:#fff0d6; color:#805400; }}
      .badge.stronger {{ background:#e7f5ed; color:#246b45; }}
      .source-box {{ background:#f8fafc; border:1px solid #dfe5eb; border-radius:10px;
        padding:13px 15px; margin:8px 0 14px; color:#415065; font-size:12px; }}
      .evidence-meta {{ color:{MUTED}; font-size:12px; }}
      .footer-note {{ color:{MUTED}; font-size:11px; border-top:1px solid #dde3e8;
        padding-top:14px; margin-top:22px; }}
      div[data-testid="stDataFrame"] {{ border:1px solid #e2e7ec; border-radius:10px; overflow:hidden; }}
      .stButton > button[kind="primary"] {{ background:{ORANGE}; color:#2b1b00; border-color:{ORANGE}; font-weight:800; }}
      .stButton > button:hover {{ border-color:{ORANGE}; color:{ORANGE}; }}
      h2, h3 {{ color:{INK}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Validating review data…")
def load_review_data() -> pd.DataFrame:
    return load_reviews(CLEAN_REVIEWS, RAW_REVIEWS, QA_REVIEWS)


@st.cache_data(show_spinner=False)
def load_cpsc_context() -> dict | None:
    if not CPSC_CONTEXT.is_file():
        return None
    import json

    return json.loads(CPSC_CONTEXT.read_text(encoding="utf-8"))


def build_concern_tags(reviews: pd.DataFrame) -> dict:
    return tag_concerns(reviews)


def upload_metadata(records, mapping):
    if records is None and mapping is None:
        if DEFAULT_METADATA.is_file() and DEFAULT_METADATA.with_suffix(DEFAULT_METADATA.suffix + ".mapping.json").is_file():
            return load_metadata(DEFAULT_METADATA)
        return None
    if records is None or mapping is None:
        st.sidebar.warning("Select both the listing-information file and its field-mapping file.")
        return None
    try:
        with TemporaryDirectory(prefix="appliance-metadata-") as tmp:
            path = Path(tmp) / "uploaded-listings.jsonl"
            path.write_bytes(records.getvalue())
            path.with_suffix(".jsonl.mapping.json").write_bytes(mapping.getvalue())
            result = load_metadata(path)
            result["path"] = f"Uploaded file: {records.name}"
            return result
    except (ValueError, OSError, KeyError) as error:
        st.sidebar.error(f"Listing information was not loaded: {error}")
        return None


def fmt_percent(value) -> str:
    return "N/A" if value is None or pd.isna(value) else f"{value * 100:.1f}%"


FRIENDLY_STATUS = {
    "Available evidence": "Topic mentioned in the listing",
    "Potential information gap": "Relevant information not found",
    "Manual review needed": "Some listing fields are unavailable",
}

FRIENDLY_PRIORITY = {
    "No gap signal under these rules": "No concern-supported signal",
    "Not assessable": "Needs more information",
}


def friendly_status(status: str) -> str:
    return FRIENDLY_STATUS.get(status, status)


def friendly_priority(priority: str) -> str:
    return FRIENDLY_PRIORITY.get(priority, priority)


def evidence_strength(review_count: int) -> tuple[str, str]:
    if review_count >= 3:
        return "Stronger evidence", "stronger"
    if review_count == 2:
        return "Some evidence", ""
    return "Limited evidence", "limited"


def product_brand(listing: dict | None) -> str | None:
    if not listing or not isinstance(listing.get("details"), dict):
        return None
    details = listing["details"]
    return details.get("Brand") or details.get("Manufacturer")


def display_title(value) -> str:
    """Repair the one legacy registered-mark artifact present in the source titles."""
    return str(value or "").replace("174;", "®").strip()


def product_label(parent: str, metadata_lookup: dict[str, dict]) -> str:
    listing = metadata_lookup.get(parent, {})
    title = display_title(listing.get("product_title"))
    return f"{title} · {parent}" if title else parent


def cpsc_hazard_group(record: dict) -> str:
    text = " ".join(
        [record.get("Title", "")]
        + [item.get("Name", "") for item in record.get("Hazards", [])]
    ).lower()
    groups = (
        ("Fire / overheating", ("fire", "overheat", "thermal")),
        ("Burn", ("burn", "scald")),
        ("Electric shock", ("shock", "electrocution")),
        ("Carbon monoxide", ("carbon monoxide",)),
        ("Laceration", ("laceration", "cut hazard")),
        ("Entrapment", ("entrap",)),
    )
    return next((label for label, terms in groups if any(term in text for term in terms)), "Other")


def listing_text(value) -> str:
    """Convert structured listing content using the analysis contract."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return " ".join(part for item in value if (part := listing_text(item)))
    if isinstance(value, dict):
        return " ".join(
            f"{key}: {part}" for key, item in value.items() if (part := listing_text(item))
        )
    return str(value)


def highlighted(value: str, pattern: str) -> str:
    """Escape source text, then mark concern terms without altering the source."""
    escaped = html.escape(value)
    return re.sub(pattern, lambda match: f"<mark>{match.group(0)}</mark>", escaped, flags=re.I)


def clear_concern() -> None:
    st.session_state["concern"] = "All concerns"


def filtered_reviews(reviews: pd.DataFrame, rating: str, year: str, verified: str, product_type: str, metadata) -> pd.DataFrame:
    scope = reviews
    if rating == "1–2 stars":
        scope = scope[scope.rating.le(2)]
    elif rating != "All ratings":
        scope = scope[scope.rating.eq(int(rating[0]))]
    if year != "All years":
        scope = scope[scope.date.dt.year.eq(int(year))]
    if verified == "Verified only":
        scope = scope[scope.verified_purchase]
    elif verified == "Not verified":
        scope = scope[~scope.verified_purchase]
    if metadata and product_type != "All product types":
        lookup = {row["parent_asin"]: (row.get("product_type") or "Unknown / unavailable") for row in metadata["records"]}
        labels = scope.parent_asin.map(lambda parent: lookup.get(parent, "Unknown / unavailable"))
        scope = scope[labels.eq(product_type)]
    return scope.copy()


try:
    reviews = load_review_data()
except (ValueError, OSError) as error:
    st.error(f"Review data could not be loaded: {error}")
    st.stop()

tags = build_concern_tags(reviews)
cpsc_context = load_cpsc_context()

with st.sidebar:
    st.markdown("## 📦 Appliance Review")
    st.caption("Amazon Appliances category-manager workspace")
    if st.button("Reset filters and selections", width="stretch"):
        for key in (
            "rating", "year", "verified", "product_type", "concern", "parent",
            "cpsc_term", "cpsc_hazard",
        ):
            st.session_state.pop(key, None)
        st.rerun()
    st.divider()
    with st.expander("Optional listing information file"):
        st.caption("Upload parent-level product listing records and the file that maps their fields.")
        records_upload = st.file_uploader("Listing records", type=["jsonl"], key="metadata_records")
        mapping_upload = st.file_uploader("Field mapping", type=["json"], key="metadata_mapping")
    metadata = upload_metadata(records_upload, mapping_upload)
    assessments = assess_metadata(metadata)
    if metadata:
        st.success(f"Listing information loaded for {len(metadata['records']):,} products")
    st.markdown("### Global filters")
    rating_filter = st.selectbox("Rating", ["All ratings", "1–2 stars", "1 star", "2 stars", "3 stars", "4 stars", "5 stars"], key="rating")
    year_options = ["All years"] + [str(year) for year in sorted(reviews.date.dt.year.unique(), reverse=True)]
    year_filter = st.selectbox("Review year", year_options, key="year")
    verified_filter = st.selectbox("Verified purchase", ["All purchases", "Verified only", "Not verified"], key="verified")
    product_type_filter = "All product types"
    if metadata and metadata["available"].get("product_type"):
        types = sorted({(row.get("product_type") or "Unknown / unavailable").strip() for row in metadata["records"]})
        product_type_filter = st.selectbox("Product type", ["All product types", *types], key="product_type")
    st.divider()
    st.caption("Filters update all cards, charts, ranking, and evidence consistently.")
    with st.expander("About the data"):
        st.markdown(
            f"""
            **Amazon review sample**

            {len(reviews):,} reviews · {reviews.parent_asin.nunique():,} parent products

            **External context prepared**

            {len(cpsc_context['records']) if cpsc_context else 0:,} CPSC appliance recalls

            [Amazon Reviews 2023]({AMAZON_DATA_URL})

            [CPSC recalls]({CPSC_DATA_URL})
            """
        )
        st.caption(
            "A Parent ASIN groups related item variants. CPSC records are category-level "
            "safety context only and are not matched to dashboard products."
        )

scope = filtered_reviews(reviews, rating_filter, year_filter, verified_filter, product_type_filter, metadata)
linked_scope = join_reviews_metadata(scope, metadata)
summary = summarize_scope(linked_scope, tags, metadata, assessments)
ranking = rank_listings(linked_scope, tags, metadata, assessments)
metadata_lookup = {row["parent_asin"]: row for row in metadata["records"]} if metadata else {}

st.markdown(
    """
    <section class="hero">
      <div class="eyebrow">AMAZON APPLIANCES · LISTING QUALITY</div>
      <h1>Appliance Listing Review</h1>
      <p>Turn customer feedback into clearer, more complete product listings.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

concern_labels = {item["id"]: item["label"] for item in CONCERNS}
concern_options = ["All concerns"] + [item["label"] for item in CONCERNS]
selected_concern_label = st.session_state.get("concern", "All concerns")
selected_concern = next(
    (key for key, label in concern_labels.items() if label == selected_concern_label), None
)
selected_rule = next(
    (item for item in CONCERNS if item["id"] == selected_concern), None
)
parent_options = [row["parent_asin"] for row in ranking]

overview_tab, product_tab, safety_tab = st.tabs(
    ["Overview", "Product Review", "Safety Context"]
)

with overview_tab:
    card1, card2, card3, card4 = st.columns(4)
    card1.metric("Reviews", f"{summary['reviews']:,}", help="Review rows under the active global filters.")
    card2.metric("Low-rated reviews", f"{summary['low']:,}", fmt_percent(summary["low_share"]), help="1–2-star reviews divided by all filtered reviews.")
    card3.metric("Reviewed products", f"{summary['parents']:,}", help="Distinct parent products represented in the filtered reviews.")
    coverage = "Not supplied" if metadata is None else fmt_percent(summary["metadata_share"])
    detail = None if metadata is None else f"{summary['matched']:,} of {summary['parents']:,} products"
    card4.metric("Listings with information", coverage, detail, help="Share of reviewed products with a matching listing record.")

    if scope.empty:
        st.warning("No reviews match these filters. Controls remain available so you can broaden the scope.")
    singleton_count = int(scope.groupby("parent_asin").size().eq(1).sum()) if not scope.empty else 0
    st.info(
        f"**Read sample sizes before acting:** {singleton_count:,} of {summary['parents']:,} products "
        "have only one review under the active filters. Priority is a screening signal, not proof of listing quality."
    )

    left, middle, right = st.columns([1.0, 1.05, 1.35], gap="large")
    with left:
        st.markdown('<div class="step"><span>1</span> Find recurring concerns</div>', unsafe_allow_html=True)
        st.subheader("Customer concerns")
        st.markdown('<p class="section-note">Counts use filtered 1–2-star reviews. Click a bar, then open Product Review.</p>', unsafe_allow_html=True)
        counts = [summary["concerns"][item["id"]] for item in CONCERNS]
        concern_fig = go.Figure(go.Bar(
            x=counts,
            y=[item["label"] for item in CONCERNS],
            orientation="h", marker_color=ROSE,
            text=[f"{count} · {count / summary['low'] * 100:.1f}%" if summary["low"] else "0 · N/A" for count in counts],
            textposition="outside", hovertemplate="%{y}: %{x} reviews<extra></extra>",
        ))
        concern_fig.update_layout(height=300, margin=dict(l=0, r=70, t=5, b=10), paper_bgcolor="white", plot_bgcolor="white", xaxis_title="Supporting reviews", yaxis=dict(autorange="reversed"), font=dict(color=INK, size=11), showlegend=False)
        concern_event = st.plotly_chart(concern_fig, width="stretch", config={"displayModeBar": False}, key="concern_chart", on_select="rerun", selection_mode="points")
        if concern_event.selection.points:
            clicked_concern = concern_event.selection.points[0].get("y")
            if clicked_concern in concern_labels.values() and st.session_state.get("concern") != clicked_concern:
                st.session_state["concern"] = clicked_concern
                st.rerun()
        rating_labels = ["1–2 stars", "3 stars", "4–5 stars"]
        share_fig = go.Figure(go.Pie(labels=rating_labels, values=summary["ratings"], hole=.62, marker_colors=[ORANGE, "#7A8DA5", BLUE], sort=False))
        share_fig.update_traces(textinfo="percent", hovertemplate="%{label}: %{value} reviews (%{percent})<extra></extra>")
        share_fig.update_layout(height=230, margin=dict(l=0, r=0, t=28, b=0), title=dict(text="Rating mix", font=dict(size=14)), paper_bgcolor="white", showlegend=True, legend=dict(orientation="h", y=-.1), font=dict(color=INK, size=10))
        st.plotly_chart(share_fig, width="stretch", config={"displayModeBar": False})

    with middle:
        st.markdown('<div class="step"><span>2</span> Understand listing information</div>', unsafe_allow_html=True)
        st.subheader("Listing information check")
        if selected_rule:
            support_count = summary["concerns"][selected_concern]
            support_share = support_count / summary["low"] if summary["low"] else None
            st.info(f"**{selected_rule['label']} → {selected_rule['attribute']}**  \n{support_count:,} supporting low-rated reviews · {fmt_percent(support_share)} of filtered low-rated reviews")
            st.button("Clear selected concern", key="clear_concern", on_click=clear_concern, width="stretch")
        else:
            st.caption("Select a concern bar or use the selector in Product Review.")
        if metadata is None:
            st.warning("Listing information is not supplied, so product-page comparisons are unavailable.")
        else:
            coverage_rows = []
            for field, label in (("product_title", "Listing title"), ("features", "Features"), ("description", "Description"), ("details", "Details")):
                value = summary["coverage"][field]
                coverage_rows.append({"Field": label, "Coverage": "Source field unavailable" if not metadata["available"][field] else fmt_percent(value)})
            with st.expander("Data quality details"):
                st.write(f"**Listings with information:** {summary['matched']:,} of {summary['parents']:,} reviewed products")
                st.dataframe(pd.DataFrame(coverage_rows), hide_index=True, width="stretch")
                st.caption("A populated field means text exists; it does not guarantee that the text is clear or accurate.")
            shown_concerns = [selected_rule] if selected_rule else CONCERNS
            comparison = pd.DataFrame([{
                "Customer concern": item["label"],
                "Listing information to check": item["attribute"],
                "Where the app looks": "Features · Description · Details",
            } for item in shown_concerns])
            st.dataframe(comparison, hide_index=True, width="stretch", height=300)

    with right:
        st.markdown('<div class="step"><span>3</span> Prioritize investigation</div>', unsafe_allow_html=True)
        st.subheader("Products to review")
        st.markdown('<p class="section-note">Open Product Review for the evidence behind a row.</p>', unsafe_allow_html=True)
        ranking_rows = []
        for row in ranking:
            listing = metadata_lookup.get(row["parent_asin"], {})
            strength, _ = evidence_strength(row["total"])
            ranking_rows.append({
                "Product": display_title(listing.get("product_title")) or "Product name unavailable",
                "Parent product ID": row["parent_asin"],
                "Reviews": row["total"], "Evidence": strength,
                "Low-rated": row["low"],
                "Supporting reviews": "N/A" if row["gap_count"] is None else row["gap_count"],
                "Topics to check": "N/A" if row["gap_count"] is None else ", ".join(row["attributes"]) or "None",
                "Priority": friendly_priority(row["priority"]),
            })
        st.dataframe(pd.DataFrame(ranking_rows), hide_index=True, width="stretch", height=520)

with product_tab:
    st.subheader("Product evidence review")
    st.caption("Select by product name. The Parent ASIN remains visible as the stable group identifier for related variants.")
    if not parent_options:
        selected_parent = None
        st.info("No reviewed products are available under these filters.")
    else:
        controls1, controls2 = st.columns([1.6, 1])
        with controls1:
            selected_parent = st.selectbox("Product", parent_options, format_func=lambda parent: product_label(parent, metadata_lookup), key="parent")
        with controls2:
            selected_concern_label = st.selectbox("Customer concern", concern_options, key="concern")
        selected_concern = next((key for key, label in concern_labels.items() if label == selected_concern_label), None)
        selected_rule = next((item for item in CONCERNS if item["id"] == selected_concern), None)

    if selected_parent:
        evidence = get_listing_evidence(selected_parent, linked_scope, tags, metadata, selected_concern)
        listing = evidence["listing"]
        title = display_title(listing.get("product_title")) if listing else None
        brand = product_brand(listing)
        product_type = listing.get("product_type") if listing else None
        strength, strength_class = evidence_strength(evidence["total"])
        item_asins = sorted(set(scope.loc[scope.parent_asin.eq(selected_parent), "asin"]))
        st.markdown(
            f'<div class="product-card"><h3>{html.escape(title or "Product name unavailable")}</h3>'
            f'<p class="product-meta">{html.escape(" · ".join(value for value in (brand, product_type) if value) or "Product details unavailable")}</p>'
            f'<p class="product-meta"><b>Parent product ID:</b> {html.escape(selected_parent)} · groups {len(item_asins):,} reviewed item variant(s)</p>'
            f'<span class="badge {strength_class}">{strength}</span><span class="badge">{evidence["total"]:,} reviews in sample</span></div>',
            unsafe_allow_html=True,
        )
        with st.expander("What is a Parent ASIN?"):
            st.write("A Parent ASIN groups related item variants such as different sizes, colors, or styles. Signals shown here describe the group; they do not prove that every variant has the same issue.")
            st.caption("Item ASINs represented under the active filters: " + ", ".join(item_asins))

        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Filtered reviews", f"{evidence['total']:,}")
        low_share = evidence["low"] / evidence["total"] if evidence["total"] else None
        e2.metric("Low-rated", f"{evidence['low']:,}", fmt_percent(low_share))
        e3.metric("Average rating", "N/A" if evidence["average"] is None else f"{evidence['average']:.1f} ★")
        verified_share = evidence["verified"] / evidence["total"] if evidence["total"] else None
        e4.metric("Verified purchases", f"{evidence['verified']:,}", fmt_percent(verified_share))

        if evidence["total"] < 3:
            st.warning(f"Only {evidence['total']:,} review(s) support this product-level view. Treat the result as a lead for investigation, not a stable trend.")

        if selected_concern:
            matching_reviews = [row for row in evidence["reviews"] if row["rating"] <= 2]
            st.markdown(f"### {selected_rule['label']} evidence comparison")
            if not matching_reviews:
                card_class, headline = "missing", "No supporting customer reviews"
                interpretation = "No low-rated reviews for this product mention this concern under the active filters."
                recommendation = "Broaden the filters or choose another concern before reviewing the listing text."
            elif listing and selected_parent in assessments:
                assessment = assessments[selected_parent]["concerns"][selected_concern]
                status, headline = assessment["status"], friendly_status(assessment["status"])
                if status == "Available evidence":
                    card_class = "found"
                    interpretation = f"{len(matching_reviews):,} of {evidence['low']:,} low-rated reviews mention {selected_rule['label'].lower()}. Related wording also appears in the listing."
                    recommendation = f"Check whether the existing {selected_rule['attribute'].lower()} text clearly answers the concern and is accurate."
                elif status == "Potential information gap":
                    card_class = "review"
                    interpretation = f"{len(matching_reviews):,} of {evidence['low']:,} low-rated reviews mention {selected_rule['label'].lower()}, but related wording was not found in the current listing fields."
                    recommendation = f"Check whether {selected_rule['attribute'].lower()} information should be added or clarified."
                else:
                    card_class = "missing"
                    interpretation = f"{len(matching_reviews):,} of {evidence['low']:,} low-rated reviews mention {selected_rule['label'].lower()}, but not all listing fields were available."
                    recommendation = "Retrieve the missing listing fields before drawing a conclusion."
            else:
                card_class, headline = "missing", "Listing information unavailable"
                interpretation = "Customer evidence exists, but there is no matching listing record to compare."
                recommendation = "Load or match the product listing before assessing its content."
            st.markdown(f'<div class="decision-card {card_class}"><h4>{html.escape(headline)}</h4><p>{html.escape(interpretation)}</p><p class="recommendation"><b>Recommended manual check:</b> {html.escape(recommendation)}</p></div>', unsafe_allow_html=True)

            customer_side, listing_side = st.columns(2, gap="large")
            with customer_side:
                st.markdown("#### Customer concern evidence")
                st.caption(f"{len(matching_reviews):,} supporting low-rated reviews")
                if not matching_reviews:
                    st.info("No supporting reviews for this product and concern.")
                for index, row in enumerate(matching_reviews[:10]):
                    verified = "Verified purchase" if row["verified_purchase"] else "Not verified"
                    with st.expander(f"{int(row['rating'])}★ · {row['title'] or 'Untitled review'}", expanded=index == 0):
                        st.markdown(highlighted(row["text"], selected_rule["pattern"]), unsafe_allow_html=True)
                        st.caption(f"{pd.to_datetime(row['timestamp']).date()} · {verified} · {row['helpful_vote']:,} helpful votes · Item ASIN {row['asin']}")
            with listing_side:
                st.markdown("#### Exact listing text")
                if listing and selected_parent in assessments:
                    assessment = assessments[selected_parent]["concerns"][selected_concern]
                    st.caption("Listing fields checked: " + (", ".join(field.title() for field in assessment["searched"]) or "None available"))
                    matched_fields = {excerpt["field"] for excerpt in assessment["excerpts"]}
                    for field in ("features", "description", "details"):
                        content = listing_text(listing.get(field))
                        match_label = " · topic mentioned" if field in matched_fields else " · topic not found"
                        with st.expander(f"{field.title()}{match_label}", expanded=field in matched_fields):
                            st.markdown(highlighted(content, selected_rule["terms"]), unsafe_allow_html=True) if content else st.caption("Field is available but empty.")
                    st.caption(f"Listing source: {metadata['source']} · Parent product ID {selected_parent}")
                else:
                    st.info("No matching listing-information record.")
        else:
            review_rows = [row for row in evidence["reviews"] if row["rating"] <= 2]
            st.info("Choose a customer concern above to compare review evidence with the exact listing text.")
            for row in review_rows[:10]:
                with st.expander(f"{int(row['rating'])}★ · {row['title'] or 'Untitled review'}"):
                    st.write(row["text"])

        if metadata and selected_parent in assessments:
            relevant = [selected_concern] if selected_concern else [item["id"] for item in CONCERNS]
            status_rows = []
            for concern_id in relevant:
                assessment = assessments[selected_parent]["concerns"][concern_id]
                status_rows.append({"Customer concern": concern_labels[concern_id], "Information to check": assessment["attribute"], "What the app found": friendly_status(assessment["status"])})
            with st.expander("How this assessment was calculated"):
                st.caption("The app looks for concern-related terms in features, description, and details. This is a screening check, not a quality judgment.")
                st.dataframe(pd.DataFrame(status_rows), hide_index=True, width="stretch")

with safety_tab:
    st.subheader("Appliance safety context")
    st.markdown(f'<div class="source-box"><b>Important:</b> CPSC records are category-level context only. They are not matched to Parent ASINs and do not mean a dashboard product was recalled. <a href="{CPSC_DATA_URL}">Search official CPSC recalls</a>.</div>', unsafe_allow_html=True)
    if not cpsc_context:
        st.warning("Prepared CPSC context is unavailable. Run prepare_external_context.py to retrieve it from the official API.")
    else:
        recall_rows = []
        for record in cpsc_context["records"]:
            recall_rows.append({
                "record": record,
                "date": pd.to_datetime(record.get("RecallDate"), errors="coerce"),
                "hazard_group": cpsc_hazard_group(record),
                "terms": record.get("context_terms", []),
            })
        term_options = ["All appliance searches", *cpsc_context["search_terms"]]
        hazard_options = sorted({row["hazard_group"] for row in recall_rows})
        safety_filter1, safety_filter2 = st.columns(2)
        term_filter = safety_filter1.selectbox("Appliance context", term_options, key="cpsc_term")
        hazard_filter = safety_filter2.selectbox("Hazard type", ["All hazards", *hazard_options], key="cpsc_hazard")
        filtered_recalls = [row for row in recall_rows if (term_filter == "All appliance searches" or term_filter in row["terms"]) and (hazard_filter == "All hazards" or row["hazard_group"] == hazard_filter)]

        s1, s2, s3 = st.columns(3)
        s1.metric("Context recalls", f"{len(filtered_recalls):,}")
        s2.metric("Coverage begins", cpsc_context["recall_date_start"])
        s3.metric("Retrieved", cpsc_context["retrieved_on"])
        hazard_counts = pd.Series([row["hazard_group"] for row in filtered_recalls]).value_counts()
        if not hazard_counts.empty:
            hazard_fig = go.Figure(go.Bar(x=hazard_counts.values, y=hazard_counts.index, orientation="h", marker_color=ORANGE))
            hazard_fig.update_layout(height=280, margin=dict(l=0, r=20, t=35, b=20), title="Recall context by hazard", yaxis=dict(autorange="reversed"), paper_bgcolor="white", plot_bgcolor="white", showlegend=False)
            st.plotly_chart(hazard_fig, width="stretch", config={"displayModeBar": False})
        if not filtered_recalls:
            st.info("No CPSC context records match these filters.")
        for index, row in enumerate(filtered_recalls[:20]):
            record = row["record"]
            product_names = ", ".join(item.get("Name", "") for item in record.get("Products", []) if item.get("Name"))
            hazard_text = " ".join(item.get("Name", "") for item in record.get("Hazards", []))
            remedies = ", ".join(item.get("Option", "") for item in record.get("RemedyOptions", []) if item.get("Option")) or "See recall notice"
            with st.expander(f"{row['date'].date() if not pd.isna(row['date']) else 'Date unavailable'} · {record.get('Title', 'Untitled recall')}", expanded=index == 0):
                st.write(f"**Product context:** {product_names or 'Not specified'}")
                st.write(f"**Hazard:** {hazard_text or 'See official notice'}")
                st.write(f"**Remedy:** {remedies}")
                st.link_button("Open official CPSC notice", record.get("URL") or CPSC_DATA_URL)
        if len(filtered_recalls) > 20:
            st.caption(f"Showing the first 20 of {len(filtered_recalls):,} matching context records.")

date_min = reviews.date.min().date()
date_max = reviews.date.max().date()
metadata_source = metadata["source"] if metadata else "Not supplied"
st.markdown(
    f'<p class="footer-note"><b>Sources:</b> <a href="{AMAZON_DATA_URL}">Amazon Reviews 2023</a> Appliances sample '
    f'({len(reviews):,} reviews; {date_min} to {date_max}); <a href="{CPSC_DATA_URL}">CPSC recalls</a> category-level safety context. '
    f'<b>Listing information:</b> {metadata_source}. '
    'Concern matches and missing-information signals are screening prompts for manual review, not proof of defects, recall status, historical listing omissions, or what a customer saw at purchase time.</p>',
    unsafe_allow_html=True,
)
