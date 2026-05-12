# sample030

- citing paper title: Towards Query Pricing on Incomplete Data
- cited paper title: QIRANA
- target reference marker: [16]
- target reference entry: S. Deep and P. Koutris, “QIRANA: A framework for scalable query pricing,” in SIGMOD, pp. 699–713, 2017.
- alignment status: high_confidence

## all_target_aligned_contexts

p3 2019-10-21 2019-11-01 t4u2? 2019-09-22 ?(c)Product(P) Pid Size Memory Price p14.7 64 $5988 p24.7 256 $7288 p35.5 64 $6888 p45.5 256 $8188 the literature [13], [14], [15], [16], [17], [18], [19]. However, these existing pricing approaches are notsuitable for pricing incomplete data, since they do not consider data complete- ness.

... [another target-aligned mention] ...

One can also compute other combined prices (e.g., the highest/average price) of lineage tuples for it. Moreover, the higher the tuple completeness, the higher the UCA price.The arbitrage-free property widely explored in relevant studies [13], [16], [19] is a typical and important property for price functions. This property is necessary for data pricing toavoid arbitrage .

... [another target-aligned mention] ...

Following existing studies [31], [7], [10], we simulate incomplete datasets via randomly discarding some values at a certain missing rate. In the experiments, following the related work [16], we use 40 queries over four datasets to conduct performance evaluation. All of the queries are described in Table 5, including 16 queries (w.r.t.

... [another target-aligned mention] ...

The seller sets the price of a speciﬁc set of base queries (also called view), and then, the algorithm has to derive the price of any other query that could be made to the database. This group consists of pricing generalized chain queries (i.e., a special type of join conjunctive query when the base queries are only selection queries) [14], [42] and pricing SQL queries [13], [16]. There are some efforts on revenue maximizing arbitrage-free pricing [19], [43], [44], the pricing problem for trading time series data and personal data [45], [46], [47], [48], pricing queries while protecting the seller’s privacy [49], [50] or in cloud environments [51].

... [another target-aligned mention] ...

Our proposed pricing scheme iDBPricer belongs to the category. Q IRANA [16], [54], standing the viewpoint of the data buyer, employs the possible world semantic to price relational queries. In addition, there is a series of studies on pricing machine learning tasks [17], [18], [55], pricing-related problems in both advertising markets and labor markets [56], etc.

## LLM outputs

- LLM_section: Introduction
- LLM_sentiment: 0.0
- LLM_relevance: 0.3
- LLM_confidence: 0.9
- LLM_q: 0.018

## Human scoring reminder

- First judge whether the context truly aligns to the current target cited paper.
- Only score the current target paper even for grouped/range citation contexts.
- Use `wrong_or_ambiguous` if the context still cannot be confidently aligned to the current target.