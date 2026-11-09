# Amazon Appliances Listing Review

An interactive Streamlit dashboard that helps an Amazon Appliances category manager identify product listings that need information review and determine which product attributes should be clarified or standardized.

## Live app

- **Dashboard:** https://dso576-amazon-project.streamlit.app/
- **Demo video:** [Watch the demo on Google Drive](https://drive.google.com/drive/folders/1zlhh-oQRBWEt0njn5zLXmtwwPXtiAgoO?usp=sharing)

The live dashboard can be opened without signing in.

## Intended user and decision

The intended user is an **Amazon Appliances category manager**. The manager is trying to decide:

1. Which product listings should be prioritized for manual information review?
2. Which listing attributes—such as dimensions, compatibility, installation, instructions, missing parts, noise, or durability—need clearer or more standardized information?
3. What customer-review evidence supports investigating a particular product or attribute?

The dashboard treats low ratings and concern matches as **screening signals**, not proof that a product is defective or that a listing is incorrect. The manager should inspect the review evidence and exact listing text before making a listing change.

## Main dashboard features

- **Overview:** Summarizes review volume, low-rated reviews, reviewed products, metadata coverage, recurring customer concerns, rating mix, concern trends, and products to investigate.
- **Product Review:** Lets the manager select a product and concern, review product-level rating metrics, and compare customer evidence with the exact available listing text.
- **Safety Context:** Provides category-level CPSC recall context. These records are not matched directly to dashboard Parent ASINs and do not mean that a dashboard product was recalled.
- **Global filters:** Rating, review year, verified-purchase status, and product type update the dashboard consistently.
- **Empty-state handling:** Filter combinations with no matching reviews display an explanation and guidance instead of blank charts or errors.

## Run the Streamlit dashboard locally

### Prerequisites

- Python 3.11 or newer
- [`uv`](https://docs.astral.sh/uv/) for dependency management

### Instructions

Clone the repository and enter the project directory:

```bash
git clone https://github.com/dtry19/dso576-project-.git
cd dso576-project-
```

Install the locked dependencies:

```bash
uv sync --frozen
```

Start the current dashboard entry point:

```bash
uv run streamlit run new_dashboard.py
```

Open the local URL printed by Streamlit, normally:

```text
http://localhost:8501
```

To stop the app, press `Ctrl+C` in the terminal.

## Data scope

The deployed app uses a documented subset of the Amazon Reviews 2023 Appliances category:

- **Reviews:** 1,000 review records
- **Review period:** September 27, 2009 through March 14, 2023
- **Reviewed Parent ASINs:** 829
- **Listing metadata:** Matching records for the 829 Parent ASINs represented in the review sample
- **Safety data:** Prepared CPSC appliance recall records used only as category-level context

Primary data source: [McAuley Lab Amazon Reviews 2023](https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023)

Public safety source: [U.S. Consumer Product Safety Commission recalls](https://www.cpsc.gov/Recalls)

Important bundled project files include:

- `dataset/Appliances_sample.jsonl` — original 1,000-review sample
- `output/Appliances_cleaned.jsonl` — validated cleaned reviews used by the app
- `output/Appliances_metadata_sample.jsonl` — listing metadata subset
- `output/cpsc_appliance_context.json` — prepared category-level CPSC context

## Why we included safety data

We included U.S. Consumer Product Safety Commission (CPSC) recall data to give the category manager more context when reviewing appliance listings. Customer reviews describe individual experiences; the Safety Context view adds official recall information about appliance hazards and remedies, making the dashboard more informative when the user decides which product information deserves closer attention.

The user can explore appliance categories and hazard types, read the recall details, and follow links to official CPSC notices. This context can help the manager identify safety-related questions to investigate and consider whether listing instructions, warnings, or usage information need closer review.

The recall records provide category-level context and are not linked directly to the dashboard's Parent ASINs. They do not establish that a product in the review sample has been recalled or is unsafe. Any product-specific action requires checking the exact product against the official recall notice.

## Interpretation notes

- A **low-rated review** is a one- or two-star review.
- A **Parent ASIN** groups related product variants, such as different sizes, colors, or styles.
- Concern percentages use filtered low-rated reviews as the denominator.
- The concern trend uses the comparable 2017–2022 period; 2023 is incomplete through March 14 and is shown separately.
- Metadata coverage means that a matching listing record is available. It does not guarantee that every field is complete, clear, or historically identical to what a customer saw.

## Current limitations

- The app uses a 1,000-review sample rather than the full Amazon Appliances dataset.
- Many products have only one review in the sample, so product rankings should be treated as investigation leads rather than stable performance estimates.
- Concern detection and listing-information checks use rules and keyword matching; they can miss context, sarcasm, or alternative wording.
- CPSC records are category-level context and are not directly matched to Amazon products.
- The dashboard does not contain sales, traffic, inventory, or stock data. Review activity should not be interpreted as actual product demand.
- Monthly popularity and stock-planning features are not currently implemented. Those decisions would require additional sales or inventory data.

## Submission links

- **Live app:** https://dso576-amazon-project.streamlit.app/
- **GitHub repository:** https://github.com/dtry19/dso576-project-
- **Demo video:** [Watch the demo on Google Drive](https://drive.google.com/drive/folders/1zlhh-oQRBWEt0njn5zLXmtwwPXtiAgoO?usp=sharing)

## Optional public showcase preference

**All members agree.** The team consents to the demo video being featured on the course website or shared publicly as part of the course showcase.
