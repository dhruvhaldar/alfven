## 2025-05-24 - [O(N^2) Layer Construction]
**Learning:** Found an O(N^2) anti-pattern in `get_ionosphere_profile` where `ChapmanProfile` objects were repeatedly recreated in a loop using `__add__` (which copies lists). This scaled quadratically with the number of layers.
**Action:** Always prefer constructing lists first and passing them to the constructor once (O(N)) rather than appending/adding in a loop, especially for stateless physics objects.
