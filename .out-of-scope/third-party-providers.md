# No new search or fetch provider without a gap

Proposed in [#92](https://github.com/tw93/Waza/issues/92): add a third-party service as another search and fetch tier in `/read`, next to DeepSeek.

Decision: not planned. Each third-party tier in `/read` exists because I needed it myself, and every new one is one more service that receives the URLs and queries people send through the skill. A new tier needs a gap the current tiers cannot cover, shown by a failed real fetch or search.
