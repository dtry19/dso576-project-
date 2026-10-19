# dso576-project-
dso 576

# Appliances review cleaning

This folder contains my Module 6 data-cleaning work.

## Data source

McAuley Lab, Amazon Reviews 2023, Appliances category:
https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023

Our professor approved using the 1,000-review file
`dataset/Appliances_sample.jsonl` because the full category file is too large for our repository. The sample was added to the team repository in commit `2a623b2`. I left the original file unchanged.

## How to run

1. Install the dependencies listed in `requirements.txt`.
2. Open `Jamie Data Cleaning.ipynb` from the repository root.
3. Restart the kernel and run all cells from top to bottom.

## Expected outputs

- `output/Appliances_cleaned.jsonl` — all 1,000 cleaned reviews
- `output/Appliances_cleaned_50_examples.jsonl` — 50 example rows, including the five manually checked reviews

## Submission details

- Branch name: jamie
- Branch URL: https://github.com/dtry19/dso576-project-/tree/jamie
- Commit ID: 63c1b97
