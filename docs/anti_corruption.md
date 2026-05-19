# Anti-Corruption Notes

Known endpoint moves are resolved in `krheritage.transport._aliases`.

| Old URL | New URL |
| --- | --- |
| `https://apis.data.go.kr/1550246/recodeImageView` | `https://apis.data.go.kr/1550246/recordImageView` |

Calling a legacy URL emits `DeprecationWarning` and returns the replacement URL.

