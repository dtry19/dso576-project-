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

with st.sidebar:
    st.markdown("## 📦 Appliance Review")
    st.caption("Amazon Appliances category-manager workspace")
    if st.button("Reset filters and selections", width="stretch"):
        for key in ("rating", "year", "verified", "product_type", "concern", "parent"):
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

card1, card2, card3, card4 = st.columns(4)
with card1:
    st.metric("Reviews", f"{summary['reviews']:,}", help="Review rows under the active global filters.")
with card2:
    st.metric("Low-rated reviews", f"{summary['low']:,}", fmt_percent(summary["low_share"]), help="1–2-star reviews divided by all filtered reviews.")
with card3:
    st.metric("Reviewed parent ASINs", f"{summary['parents']:,}", help="Distinct parent identifiers represented in the filtered reviews.")
with card4:
    coverage = "Not supplied" if metadata is None else fmt_percent(summary["metadata_share"])
    detail = None if metadata is None else f"{summary['matched']:,} of {summary['parents']:,} products have listing information"
    st.metric(
        "Listings with information",
        coverage,
        detail,
        help="Share of reviewed products that have a matching product-listing record.",
    )

if scope.empty:
    st.warning("No reviews match these filters. Controls remain available so you can broaden the scope.")

left, middle, right = st.columns([1.0, 1.05, 1.35], gap="large")

with left:
    st.markdown('<div class="step"><span>1</span> Find recurring concerns</div>', unsafe_allow_html=True)
    st.subheader("Customer concerns")
    st.markdown('<p class="section-note">Counts use filtered 1–2-star reviews. Click a bar to inspect its evidence.</p>', unsafe_allow_html=True)
    concern_labels = {item["id"]: item["label"] for item in CONCERNS}
    counts = [summary["concerns"][item["id"]] for item in CONCERNS]
    concern_fig = go.Figure(go.Bar(
        x=counts,
        y=[item["label"] for item in CONCERNS],
        orientation="h",
        marker_color=ROSE,
        text=[f"{count} · {count / summary['low'] * 100:.1f}%" if summary["low"] else "0 · N/A" for count in counts],
        textposition="outside",
        hovertemplate="%{y}: %{x} reviews<extra></extra>",
    ))
    concern_fig.update_layout(height=300, margin=dict(l=0, r=70, t=5, b=10), paper_bgcolor="white", plot_bgcolor="white", xaxis_title="Supporting reviews", yaxis=dict(autorange="reversed"), font=dict(color=INK, size=11), showlegend=False)
    concern_event = st.plotly_chart(
        concern_fig,
        width="stretch",
        config={"displayModeBar": False},
        key="concern_chart",
        on_select="rerun",
        selection_mode="points",
    )
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
    st.markdown('<div class="step"><span>2</span> Examine listing information</div>', unsafe_allow_html=True)
    st.subheader("Listing information check")
    st.markdown('<p class="section-note">Choose a concern to compare what customers report with the exact listing language.</p>', unsafe_allow_html=True)
    concern_options = ["All concerns"] + [item["label"] for item in CONCERNS]
    selected_concern_label = st.selectbox("Concern evidence", concern_options, key="concern")
    selected_concern = next((key for key, label in concern_labels.items() if label == selected_concern_label), None)
    if selected_concern:
        selected_rule = next(item for item in CONCERNS if item["id"] == selected_concern)
        support_count = summary["concerns"][selected_concern]
        support_share = support_count / summary["low"] if summary["low"] else None
        st.info(
            f"**{selected_rule['label']} → {selected_rule['attribute']}**  \n"
            f"{support_count:,} supporting low-rated reviews · {fmt_percent(support_share)} of filtered low-rated reviews"
        )
        st.button("Clear concern evidence", key="clear_concern", on_click=clear_concern, width="stretch")
    if metadata is None:
        st.markdown('<div class="status-card"><b>Listing information not supplied</b><br>Customer reviews are available, but the app cannot compare them with product-page text yet.</div>', unsafe_allow_html=True)
        st.write("**Information the app would check**")
        for item in CONCERNS:
            st.caption(f"{item['label']} → {item['attribute']}")
    else:
        coverage_rows = []
        for field, label in (("product_title", "Listing title"), ("features", "Features"), ("description", "Description"), ("details", "Details")):
            available = metadata["available"][field]
            value = summary["coverage"][field]
            coverage_rows.append({"Field": label, "Coverage": "Source field unavailable" if not available else fmt_percent(value)})
        with st.expander("Data quality details"):
            st.write(
                f"**Listings with information:** {summary['matched']:,} of "
                f"{summary['parents']:,} reviewed products"
            )
            st.dataframe(pd.DataFrame(coverage_rows), hide_index=True, width="stretch")
            st.caption(
                f"Field coverage uses the {summary['matched']:,} matched products as its denominator. "
                "A populated field means text exists; it does not guarantee that the text is clear or accurate."
            )
        st.write("**What the app checks for each concern**")
        shown_concerns = [selected_rule] if selected_concern else CONCERNS
        comparison = pd.DataFrame([{
            "Customer concern": item["label"],
            "Listing information to check": item["attribute"],
            "Where the app looks": "Features · Description · Details",
        } for item in shown_concerns])
        st.dataframe(comparison, hide_index=True, width="stretch", height=278)

with right:
    st.markdown('<div class="step"><span>3</span> Prioritize investigation</div>', unsafe_allow_html=True)
    st.subheader("Listing priority")
    st.markdown('<p class="section-note">Select a parent ASIN to inspect its filtered evidence.</p>', unsafe_allow_html=True)
    parent_options = [row["parent_asin"] for row in ranking]
    if parent_options:
        def parent_label(parent):
            title = metadata_lookup.get(parent, {}).get("product_title")
            return f"{title} · {parent}" if title else parent
        selected_parent = st.selectbox("Selected parent ASIN", parent_options, format_func=parent_label, key="parent")
    else:
        selected_parent = None
        st.info("No reviewed parent ASINs are available under these filters.")
    ranking_rows = []
    for row in ranking:
        listing = metadata_lookup.get(row["parent_asin"], {})
        ranking_rows.append({
            "Parent ASIN": row["parent_asin"],
            "Product title": listing.get("product_title") or "—",
            "Reviews": row["total"],
            "Low-rated": row["low"],
            "Supporting reviews": "N/A" if row["gap_count"] is None else row["gap_count"],
            "Topics to check": "N/A" if row["gap_count"] is None else ", ".join(row["attributes"]) or "None",
            "Priority": friendly_priority(row["priority"]),
        })
    st.dataframe(pd.DataFrame(ranking_rows), hide_index=True, width="stretch", height=390)

st.divider()
st.markdown('<div class="step"><span>↳</span> Selected-product evidence</div>', unsafe_allow_html=True)
if selected_parent:
    evidence = get_listing_evidence(selected_parent, linked_scope, tags, metadata, selected_concern)
    listing = evidence["listing"]
    title = listing.get("product_title") if listing else None
    st.subheader(title or selected_parent)
    st.caption(f"Parent ASIN: {selected_parent}" + (f" · {listing.get('product_type')}" if listing and listing.get("product_type") else ""))
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Filtered reviews", f"{evidence['total']:,}")
    low_share = evidence["low"] / evidence["total"] if evidence["total"] else None
    e2.metric("Low-rated", f"{evidence['low']:,}", fmt_percent(low_share))
    e3.metric("Average rating", "N/A" if evidence["average"] is None else f"{evidence['average']:.1f} ★")
    verified_share = evidence["verified"] / evidence["total"] if evidence["total"] else None
    e4.metric("Verified purchases", f"{evidence['verified']:,}", fmt_percent(verified_share))

    if selected_concern:
        selected_rule = next(item for item in CONCERNS if item["id"] == selected_concern)
        matching_reviews = [row for row in evidence["reviews"] if row["rating"] <= 2]
        st.markdown(f"### {selected_rule['label']} evidence comparison")

        if not matching_reviews:
            card_class = "missing"
            headline = "No supporting customer reviews"
            interpretation = (
                "No low-rated reviews for this product mention this concern under the active filters. "
                "The app does not have enough customer evidence to suggest a listing change."
            )
            recommendation = "Broaden the filters or choose another concern before reviewing the listing text."
        elif listing and selected_parent in assessments:
            assessment = assessments[selected_parent]["concerns"][selected_concern]
            status = assessment["status"]
            headline = friendly_status(status)
            if status == "Available evidence":
                card_class = "found"
                interpretation = (
                    f"{len(matching_reviews):,} of {evidence['low']:,} low-rated reviews for this product "
                    f"mention {selected_rule['label'].lower()}. Related wording also appears in the listing."
                )
                recommendation = (
                    f"Check whether the existing {selected_rule['attribute'].lower()} text clearly answers "
                    "the customer concern and is accurate."
                )
            elif status == "Potential information gap":
                card_class = "review"
                interpretation = (
                    f"{len(matching_reviews):,} of {evidence['low']:,} low-rated reviews for this product "
                    f"mention {selected_rule['label'].lower()}, but related wording was not found in the current listing fields."
                )
                recommendation = (
                    f"Check whether {selected_rule['attribute'].lower()} information should be added or clarified."
                )
            else:
                card_class = "missing"
                interpretation = (
                    f"{len(matching_reviews):,} of {evidence['low']:,} low-rated reviews for this product "
                    f"mention {selected_rule['label'].lower()}, but not all listing fields were available to search."
                )
                recommendation = "Retrieve the missing listing fields before drawing a conclusion."
        elif metadata:
            card_class = "missing"
            headline = "Listing information unavailable for this product"
            interpretation = (
                f"{len(matching_reviews):,} of {evidence['low']:,} low-rated reviews mention "
                f"{selected_rule['label'].lower()}, but this product has no matching listing record."
            )
            recommendation = "Add or match this product's listing record before assessing its content."
        else:
            card_class = "missing"
            headline = "Listing information not supplied"
            interpretation = (
                f"{len(matching_reviews):,} of {evidence['low']:,} low-rated reviews mention "
                f"{selected_rule['label'].lower()}, but there is no listing file to compare."
            )
            recommendation = "Load listing information to compare customer concerns with product-page text."

        st.markdown(
            f'<div class="decision-card {card_class}">'
            f'<h4>{html.escape(headline)}</h4>'
            f'<p>{html.escape(interpretation)}</p>'
            f'<p class="recommendation"><b>Recommended manual check:</b> {html.escape(recommendation)}</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        customer_side, listing_side = st.columns(2, gap="large")
        with customer_side:
            st.markdown("#### Customer concern evidence")
            st.caption(f"{len(matching_reviews):,} supporting low-rated reviews under the active filters")
            if not matching_reviews:
                st.info("No reviews for this parent support the selected concern under the active filters.")
            for index, row in enumerate(matching_reviews[:10]):
                verified = "Verified purchase" if row["verified_purchase"] else "Not verified"
                with st.expander(
                    f"{int(row['rating'])}★ · {row['title'] or 'Untitled review'}",
                    expanded=index == 0,
                ):
                    st.markdown(highlighted(row["text"], selected_rule["pattern"]), unsafe_allow_html=True)
                    st.caption(
                        f"{pd.to_datetime(row['timestamp']).date()} · {verified} · "
                        f"{row['helpful_vote']:,} helpful votes · Item ASIN {row['asin']}"
                    )
        with listing_side:
            st.markdown("#### Exact listing text")
            if listing and selected_parent in assessments:
                assessment = assessments[selected_parent]["concerns"][selected_concern]
                st.caption(
                    "Listing fields checked: " + (", ".join(field.title() for field in assessment["searched"]) or "None available")
                )
                matched_fields = {excerpt["field"] for excerpt in assessment["excerpts"]}
                for field in ("features", "description", "details"):
                    content = listing_text(listing.get(field))
                    match_label = " · topic mentioned" if field in matched_fields else " · topic not found"
                    with st.expander(f"{field.title()}{match_label}", expanded=field in matched_fields):
                        if content:
                            st.markdown(highlighted(content, selected_rule["terms"]), unsafe_allow_html=True)
                        else:
                            st.caption("Field is available but empty.")
                st.caption(f"Listing information source: {metadata['source']} · parent ASIN {selected_parent}")
            elif metadata:
                st.info("No matching listing-information record for this parent ASIN.")
            else:
                st.info("Listing information not supplied.")

    if metadata and selected_parent in assessments:
        relevant = [selected_concern] if selected_concern else [item["id"] for item in CONCERNS]
        status_rows = []
        for concern_id in relevant:
            assessment = assessments[selected_parent]["concerns"][concern_id]
            status_rows.append({
                "Customer concern": concern_labels[concern_id],
                "Information to check": assessment["attribute"],
                "What the app found": friendly_status(assessment["status"]),
            })
        with st.expander("How this assessment was calculated"):
            st.caption(
                "The app looks for concern-related terms in the listing's features, description, and details. "
                "This is a screening check, not a judgment about listing quality."
            )
            st.dataframe(pd.DataFrame(status_rows), hide_index=True, width="stretch")
    elif metadata:
        st.info("No matching listing-information record for this parent ASIN.")

    if not selected_concern:
        review_rows = [row for row in evidence["reviews"] if row["rating"] <= 2]
        if not review_rows:
            st.info("No supporting low-rated reviews under the current filters.")
        else:
            st.write(f"**Supporting review evidence ({len(review_rows):,})**")
            for row in review_rows[:25]:
                verified = "Verified purchase" if row["verified_purchase"] else "Not verified"
                with st.expander(f"{int(row['rating'])}★ · {row['title'] or 'Untitled review'}"):
                    st.write(row["text"])
                    st.markdown(f'<p class="evidence-meta">{pd.to_datetime(row["timestamp"]).date()} · {verified} · {row["helpful_vote"]:,} helpful votes · Item ASIN {row["asin"]}</p>', unsafe_allow_html=True)
            if len(review_rows) > 25:
                st.caption(f"Showing the first 25 of {len(review_rows):,} supporting reviews for readability.")

date_min = reviews.date.min().date()
date_max = reviews.date.max().date()
metadata_source = metadata["source"] if metadata else "Not supplied"
st.markdown(
    f'<p class="footer-note"><b>Sources:</b> Amazon Reviews 2023 Appliances sample ({len(reviews):,} reviews; {date_min} to {date_max}). '
    f'<b>Listing information:</b> {metadata_source}. Concern matches and missing-information signals are screening prompts for manual review, not proof of defects, historical listing omissions, or what a customer saw at purchase time.</p>',
    unsafe_allow_html=True,
)
