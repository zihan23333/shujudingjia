# sample005

- citing paper title: Data Collection and Wireless Communication in Internet of Things (IoT) Using Economic Analysis and Pricing Models: A Survey
- cited paper title: A Priced Public Sensing Framework for Heterogeneous IoT Architectures
- target reference marker: [106]
- target reference entry: A. E. Al-Fagih, F. M. Al-Turjman, W. M. Alsalih, and H. S. Hassanein, “A priced public sensing framework for heterogeneous iot architec- tures,” IEEE Transactions on Emerging Topics in Computing, vol. 1, no. 1, pp. 133–147, 2013.
- alignment status: high_confidence

## all_target_aligned_contexts

Thus, the authors in [105] adopted the sealed- bid reverse auction to address the routing problem in WSNs with the aim of minimizing the latency and maximizing the network throughput for all applications. In fact, the latency is also closely related to the energy efﬁciency since a data packet with a large delay due to traveling more hops in the network consumes more energy [106]. The model consists of a router, i.e., a buyer, who selects one of its neighbors, i.e., sellers, as the next hop for the packet delivery.

... [another target-aligned mention] ...

Different from the reverse auction which deﬁnes the lowest price among sellers, the value-based pricing sets price primarily based on the perceived value to the buyer rather than the cost of the product, the market price, or even the historical prices. The authors in [106] employed the value-based pricing to set the data selling price for the sensors, i.e., sellers, according to the requirements of the requester, i.e., the buyer. The general model includes entities as shown in Fig.

... [another target-aligned mention] ...

Citation information: DOI 10.1109/COMST.2016.2582841, IEEE Communications Surveys & Tutorials 17 TABLE II APPLICATIONS OF ECONOMIC AND PRICING MODELS FOR DATA AGGREGATION AND ROUTING Ref. Pricing modelMarket structureMechanism Objective SolutionSeller Buyer ItemData aggregation and routing[103]Sealed-bid reverse auctionSelﬁsh sensorsFusion centerTarget localization dataSellers submit to the auctioneer their ask values inversely proportional to the remaining energy, the auctioneer selects an optimal subset of sellers with the lowest ask valuesEnergy consumption balance, and buyer’s utility maximizationNash equilibrium [105]Sealed-bid reverse auctionNeighboring sensorsRouterPacket forwarding serviceSellers submit to the buyer their asks including the path price, the buyer selects a seller with the lowest path priceOverall minimal delay, and network throughput maximizationNash equilibrium [106]Value-based pricingThe sink nodeRequesterPacket forwarding serviceSeller sets prices according to the requester’s requirements to maximize the utility of the requesterBuyer’s utility maximizationValue optimization [113]Sealed-bid reverse auctionPhone usersServerSensing dataSellers submit their asking prices including the task execution costs to the buyer, the buyer selects a subset of sellers with the lowest asking prices and gives them rewards. The losers also get virtual credit for incentiveService quality guarantee, incentive cost minimization, improved fairness, and social welfare improvementNash equilibrium [115]Sealed-bid reverse auctionPhone usersServerSensing dataSame as [113] but the buyer adds a recruiting mechanism to stimulate the dropped users to join in the futureService quality guarantee, incentive cost minimization, improved fairness, and social welfare improvementNash equilibrium [117]Sealed-bid reverse auctionPhone usersServerSensing dataSame as [113] but the buyer pays the users by monetary instead of the virtual creditIncentive improvementNash equilibrium [118] [119]Sealed-bid reverse auctionPhone usersServerSensing dataSellers submit their asks including costs and their locations.

## LLM outputs

- LLM_section: Result
- LLM_sentiment: 0.2
- LLM_relevance: 0.9
- LLM_confidence: 0.8
- LLM_q: 0.486

## Human scoring reminder

- First judge whether the context truly aligns to the current target cited paper.
- Only score the current target paper even for grouped/range citation contexts.
- Use `wrong_or_ambiguous` if the context still cannot be confidently aligned to the current target.