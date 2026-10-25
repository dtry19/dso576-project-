# My Module 9 audit

Complete this template in your own words and submit it on Brightspace. Do not push your completed audit to this shared course repo.

## Context

- Name: Dalin Try 
- Team app and version or commit checked: My team version is an Amazon dashboard that help identify product listings that may need clearer or more complete information. 
- Intended user and decision:The intended user is the Amazon Appliances category manager and the dashboard is designed to help them identify products listings that needs clearer or more complete information. 

## 1. Feature audit

- Feature and intended behavior: The feature that I'm auditing is the reset feature when trying to select the ratings. After clicking the reset button it should go back to showing the original data. 
- Inputs and steps to reproduce: The inputs for this dashboard is te 1000 review dataset. The steps to reproduce includes opening up the dashboard.html and then set the verified purchase to not verified. And then confirm if the dashboard shows 102 reviews or not. And then click reset and see if the filter ruetns to 'All' or not. 
- Expected behavior: The expected behavior is when after clicking reset it should return to 'All' and review count should return to 1000. 
- Actual behavior and evidence:But the actual behavior of the reset feature is that it doesn't actually reset and this is evident when I tried to click the reset button on the dashboard. 
- Conclusion and any recommended change: To conclude that means I need to go back to the coding file and fix the JavaScript error and ensure that the Reset does restores all filters, clears products and concerns selections. 

## 2. Number audit

- Number audited and its meaning: The number that I'm auditing is the percentage of low-rated reviews. and thr number 10.5% represents the share of reviews in the sample of 1000 that gave 1 or 2 stars. This also show how common low ratings are among the reviews currently selected in the dashboard.
- Formula, units, population, and time window: The formula is low rated percentage = ((number of 1-2 reviews) / all reviews in the active filter scope) * 100.
- Relevant data assumptions: Each row represents one review and the reviews have equal weights. Ratings are valid as whole numbers from 1 to 5. And low rate means 1 or 2 stars. 
- Code checked: file path, function name, and relevant line numbers or a short code excerpt (at the version recorded above): The code that is checked is in the appliance_analysis.py file and this particular lines.
low = reviews[reviews.rating.le(2)]
low_share = len(low) / len(reviews) if len(reviews) else None
- What this code computes, in my own words: This code counts the reviews rated 1 or 2 stars and then divided by all reviews remained after the filtering. The dashboard also displays that fraction as a percentage. 
- Small test case and expected result: A small test case test that can be done is using a small dataset that contains five reviews with ratings and two of them are low rated and see how does it affect the percentage. 
Ex - Dataset = [1,2,3,4,5]
Formula= 2/5 * 100 = 40%
- Actual result: The actual result is that the function returned 2 low-rated reviews out of 5 and a share of 0.4 which is 40% which matches the expected result. 
- Independent calculation or check of a specific assumption/code line: The AI- assited check independently read the file containing the dataset and counted ratings that were 1 or 2 and also checked the production code as well. 
- What the evidence establishes and what remains uncertain: The evidence supports that the low rated percentage formula works correctly for the tested examples and the supplied datasets. But it doesn't establish that the sample represents all Amazon Appliances reviews or that low rating proves product defects. 
- Recommended change, if any: No change are needed for the percentage formula and I need to fix the reset feature. 

Include the code or a link to the check when needed to reproduce your evidence. Finding no bug is a valid conclusion when supported by checks.

## My contribution

- What I personally checked and concluded:I personally checked the reset feature by interactign with the dashboard and I can conclude that the numbers are fine. 
- How AI helped, if used:I input the build spec file and the dataset into claude to check how it works, and it also generated the same results as welll. Therefore this suggests that the problem is apparent in other AI agents and I need to fix this issue. 
