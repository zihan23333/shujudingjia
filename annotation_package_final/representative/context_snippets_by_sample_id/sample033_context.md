# sample033

- citing paper title: A First Look at Information Entropy-Based Data Pricing
- cited paper title: Query-Based Data Pricing
- target reference marker: [12]
- target reference entry: P . Koutris, P . Upadhyaya, M. Balazinska, B. Howe, and D. Suciu, “Query-based data pricing,” Journal of the ACM (JACM) , vol. 62, no. 5, p. 43, 2015.
- alignment status: high_confidence

## all_target_aligned_contexts

Nevertheless, data markets did not support complex ad-hoc queries at the beginning because it was unclear how to assign a proper price to a query result. Koutris et al proposed query-based data pricing framework to address complex ad-hoc queries [12]. Their framework allows data sellers to assign explicit prices to a few views or sets of views, and also provides the possibility to data buyers to issue and buy any query.

... [another target-aligned mention] ...

Their framework allows data sellers to assign explicit prices to a few views or sets of views, and also provides the possibility to data buyers to issue and buy any query. Although the price of queries can be calculated automatically from explicit prices of views using the framework proposed in [12], guidance for assigning reasonable price to views of datasets is not provided in [12]. 3) Bundling and Discrimination Pricing: Bundling pricing strategy originates from capital data market, and it represents anaggregation techniques [13].

... [another target-aligned mention] ...

As for information entropy-based pricing function presented in Section III-C, the biggest merit of proposed pricing function is the arbitrage-free property. Many of previous studies [16], [17], [12] concerning query-based data pricing dedicate to making the pricing function arbitrage-free. [16] proposed the rudiment of query-based data pricing, where a simple instance for calculation of query price for online data markets is provided.

... [another target-aligned mention] ...

Although subsequent researchers have proposed a variety of pricing functions based on [16], they still do not address the problem that the price for tuple (or view) is assigned subjectively by data owners. The proposed data pricing metric, data information entropy, might offer a new angle to address this problem in [16], [17], [12], because data information entropy could provide speciﬁc pricing relationship among tuples (views). IV .

## LLM outputs

- LLM_section: Introduction
- LLM_sentiment: 0.3
- LLM_relevance: 0.7
- LLM_confidence: 0.9
- LLM_q: 0.1273999999999999

## Human scoring reminder

- First judge whether the context truly aligns to the current target cited paper.
- Only score the current target paper even for grouped/range citation contexts.
- Use `wrong_or_ambiguous` if the context still cannot be confidently aligned to the current target.