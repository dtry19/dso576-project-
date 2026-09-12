# Project Starting Point

## Team and GitHub

| Team name | GitHub repository |
|---|---|
| [Team name] | [Link to the team's private GitHub repository] |

## Selected project area

[Area]

## Why our team is interested in it

[Write 2-3 sentences.]

## Candidate Vision A

An Appliances category manager at Amazon must decide which appliance listings to prioritize for product-information review based on recurring customer complaints about missing, unclear, or inaccurate attributes.

## Candidate Vision B

An Amazon product data manager must decide which appliance attributes to standardize across listings based on how frequently customers mention them in reviews but they are missing or inconsistent in product metadata.

## Side-by-side candidate assessment

| Assessment | Vision A | Vision B |
|---|---|---|
| Evidence found so far | The dataset has about 2.1 million reviews in the Appliances category. It includes review text, ratings, helpful votes, and dates. We can match reviews to product information using `parent_asin` and check whether customers keep bringing up details that are missing or unclear in the listing. [Source: Amazon Reviews 2023](https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023#data-fields). | [Summarize the strongest verified evidence and link its original source.] |
| Core-data fit | We can compare customer complaints with product information to decide which listings need to be checked first, but we still need to look at a sample to see whether it has enough detail. | [Strong, partial, or weak—and one sentence explaining why.] |
| Biggest risk | A complaint might be about the appliance itself, how someone used it, or a different model rather than the listing. The listing may also have changed since the review was written. We need to check these cases before saying the product information needs fixing. | [What could prevent this Vision from supporting a useful, defensible decision?] |


## Core data source we confirmed we can access

[Source, original link, and what successfully opened.]

## Three questions we still need to resolve

1. [Question]
2. [Question]
3. [Question]

## Role-file progress

Use one of these status labels: **Not started**, **In progress**, **Ready for team review**, **Complete**, or **Not applicable**.

| Role file | Owner | Status |
|---|---|---|
| [`objectives.md`](objectives.md) | [Name or GitHub username] | [Status] |
| [`alternatives.md`](alternatives.md) | [Name or GitHub username] | [Status] |
| [`data-fit.md`](data-fit.md) | [Name or GitHub username] | [Status] |
| [`auxiliary.md`](auxiliary.md) | [Name or GitHub username] | [Status] |
| [`technical.md`](technical.md) | [Name or GitHub username] | [Status] |
| [`objections.md`](objections.md) | [Name or GitHub username] | [Status; use Not applicable for teams with fewer than six members] |

## Team check

- [ ] We added our team name and the correct private GitHub repository link.
- [ ] We selected the area based first on genuine team interest.
- [ ] A and B are distinct candidate Visions within the same area.
- [ ] The candidate comparison uses verified evidence rather than unsupported claims.
- [ ] At least one data source opened, or we recorded the access blocker.
- [ ] We preserved three real questions instead of hiding uncertainty.
- [ ] Every active role file has an owner and a current status.
- [ ] Every teammate reviewed this provisional starting point.
