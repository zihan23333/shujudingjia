# sample007

- citing paper title: Data pricing in machine learning pipelines
- cited paper title: QIRANA
- target reference marker: 29
- target reference entry: Deep S, Koutris P (2017b) QIRANA: a framework for scalable query pricing. In: Salihoglu S, Zhou W, Chirkova R, Yang J, Suciu D (eds) Proceedings of the 2017 ACM international conference on 123 Data pricing in machine learning pipelines 1449 management of data, SIGMOD conference 2017, Chicago, IL, USA, May 14–19, 2017. ACM, pp 699–
- alignment status: high_confidence

## all_target_aligned_contexts

In a sell-side marketplace, the arbiter is operatedby a monopoly data seller to sell the single seller’s data products. In literature, sell-sidemarketplaces are considered by pricing models of both general data sets [ 43] and speciﬁc types of data products, such as XML documents [ 108] and data queries on a relational database [ 29]. A buy-side marketplace [ 120] ,a ss h o w ni nF i g .

... [another target-aligned mention] ...

Several examples of arbitrage-free pricing functionsare presented, including the weighted coverage function and the Shannon entropy function. Deep and Koutris [ 29] later implement the theoretical framework [ 28] into a real time pricing system, QIRANA, which computes the price of a query bundle Qfrom the view of uncertainty reduction. They assume that a buyer is facing a set of all possible databaseinstances Swith the same schema as the true database instance D.

... [another target-aligned mention] ...

QueryMarket [ 59] tracks the purchased views of a customer and avoids charging those views when pricing future queries of the customer. Both[29]a n d[ 75] support history-aware pricing in the same vein as [ 59]. One drawback of these history-based approaches is that the seller must provide reliable storage to keep users’ queryhistory [ 111].

... [another target-aligned mention] ...

By tracking coupon status, the data seller guarantees that each coupon will be usedonly once. However, the pricing function has no arbitrage-free guarantee [ 29]. 3.4 Privacy compensation Machine learning models in many areas, like recommendation systems [ 21] and personalized medical treatments [ 72], require a large amount of personal data.

... [another target-aligned mention] ...

Such ﬂexibility makes it easier to version raw data products, and enablesmore ﬂexible pricing mechanisms. For example, according to how much information isrevealed, different prices can be assigned to different queries on the same database [ 29]. 123 1442 Z.

... [another target-aligned mention] ...

Cong et al. Table 1 The representative data pricing models of raw data sets Product Objectives References General data No speciﬁc optimization goals [ 43] (1) Revenue maximization [ 117] Sensing data (1) Truthfulness; (2) Individual rationality; (3) Proﬁtability[115] (1) Truthfulness; (2) Social welfare maximization[52] (1) Truthfulness (2) Buyer’s cost minimization [ 60] Chain queries, conjunctive queries, and cyclic queries(1) Arbitrage-freeness; (2) Discount-freeness [ 58] Conjunctive queries (1) Arbitrage-freeness; (2) Discount-freeness; (3) History-awareness; (4) Fairness[59] General data queries (1) Arbitrage-freeness [ 28], [65] (1) Arbitrage-freeness; (2) History-awareness [ 29] (1) Arbitrage-freeness; (2) Revenue maximization[16] Selection-projection-natural join queries over incomplete databases(1) Arbitrage-freeness; (2) History-awareness [ 75] Selection queries (1) History-awareness [ 111] Counting queries on binary data (1) Privacy compensation; (2) Truthfulness; (3) Buyer’s cost minimization[38] Linear aggregation queries (1) Privacy compensation; (2) Query accuracy maximization under budget constraint[21] (1) Privacy compensation; (2) Personalized maximum tolerable privacy loss; (3) Queryaccuracy maximization under budgetconstraint[83] (1) Privacy compensation; (2) Truthfulness; (3) Personalized maximum tolerable privacy loss; (4) Query accuracy maximization under budget constraint[121] (1) Privacy compensation; (2) Arbitrage-freeness [ 62] (1) Privacy compensation; (2) Arbitrage-freeness; (3) Dependency fairness[84] Geo-location data (1) Privacy compensation; (2) Data accuracy maximization under budget constraint[53] tables can be used as a starting point in helping data pricing practitioners to choose the right pricing models for their settings. Tables 1,2,3,a n d 4have three columns.

## LLM outputs

- LLM_section: Introduction
- LLM_sentiment: 0.5
- LLM_relevance: 0.8
- LLM_confidence: 0.9
- LLM_q: 0.192

## Human scoring reminder

- First judge whether the context truly aligns to the current target cited paper.
- Only score the current target paper even for grouped/range citation contexts.
- Use `wrong_or_ambiguous` if the context still cannot be confidently aligned to the current target.